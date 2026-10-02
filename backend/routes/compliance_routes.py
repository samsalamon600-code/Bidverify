from datetime import datetime, timezone
from flask import Blueprint, request, g
from backend.config import Config
from backend.extensions import db
from backend.models.models import Bid, ComplianceResult
from backend.auth.decorators import jwt_required
from backend.compliance.engine import run_bid_compliance_verification
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error

compliance_bp = Blueprint("compliance_bp", __name__)


@compliance_bp.route("/api/bids/<int:bid_id>/verify", methods=["POST"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def verify_bid_compliance(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    record_audit_log(
        "Compliance Check Started",
        user=g.current_user,
        tender_id=bid.tender_id,
        bid_id=bid.id,
        result_status="IN_PROGRESS",
        commit=False,
    )

    try:
        summary = run_bid_compliance_verification(bid, commit=True)
    except Exception as exc:
        db.session.rollback()
        return api_error(
            f"AI/Compliance verification failure: {str(exc)}",
            "AI_PROCESSING_FAILURE",
            500,
        )

    record_audit_log(
        "Compliance Result Generated",
        user=g.current_user,
        tender_id=bid.tender_id,
        bid_id=bid.id,
        result_status=f"Score: {summary['overall_compliance_score']}% | Risk: {summary['risk_level']}",
        review_comments="Automated Decision-Support Analysis Completed (Awaiting Officer Review)",
    )

    return api_success(
        summary,
        message="Automated compliance verification and ML risk analysis completed. Ready for Officer review.",
    )


@compliance_bp.route("/api/bids/<int:bid_id>/compliance", methods=["GET"])
@jwt_required()
def get_bid_compliance(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    user = g.current_user
    if user.role_name == "COMPANY":
        if not user.company_profile or bid.company_id != user.company_profile.id:
            return api_error("Unauthorized access to compliance results.", "UNAUTHORIZED_BID_ACCESS", 403)

    return api_success({
        "bid_id": bid.id,
        "bid_number": bid.bid_number,
        "company_name": bid.company.company_name if bid.company else None,
        "tender_code": bid.tender.tender_code if bid.tender else None,
        "tender_title": bid.tender.title if bid.tender else None,
        "verification_status": bid.verification_status,
        "officer_review_status": bid.officer_review_status,
        "officer_review_comments": bid.officer_review_comments,
        "overall_compliance_score": round(bid.overall_compliance_score or 0.0, 1),
        "category_scores": {
            "document_compliance": round(bid.document_compliance_score or 0.0, 1),
            "statutory_compliance": round(bid.statutory_compliance_score or 0.0, 1),
            "technical_compliance": round(bid.technical_compliance_score or 0.0, 1),
            "tender_compliance": round(bid.tender_compliance_score or 0.0, 1),
        },
        "weights": Config.COMPLIANCE_WEIGHTS,
        "risk_level": bid.risk_level,
        "compliance_results": [c.to_dict() for c in bid.compliance_results],
        "evidences": [e.to_dict() for e in bid.evidences],
    })


@compliance_bp.route("/api/bids/<int:bid_id>/risk", methods=["GET"])
@jwt_required()
def get_bid_risk(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    user = g.current_user
    if user.role_name == "COMPANY":
        if not user.company_profile or bid.company_id != user.company_profile.id:
            return api_error("Unauthorized access to risk analysis.", "UNAUTHORIZED_BID_ACCESS", 403)

    latest_risk = bid.risk_results[-1].to_dict() if bid.risk_results else None
    return api_success({
        "bid_id": bid.id,
        "bid_number": bid.bid_number,
        "company_name": bid.company.company_name if bid.company else None,
        "risk_level": bid.risk_level,
        "risk_analysis": latest_risk,
    })


@compliance_bp.route("/api/bids/<int:bid_id>/review", methods=["POST"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def submit_officer_human_review(bid_id):
    """
    Human-in-the-loop review endpoint for the authorized Procurement Officer.
    Allows changing status to:
    - Reviewed (REVIEWED)
    - Requires Clarification (REQUIRES_CLARIFICATION)
    - Verified (VERIFIED)
    """
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    data = request.get_json(silent=True) or {}
    new_status = (data.get("review_status") or "REVIEWED").strip().upper().replace(" ", "_")
    comments = (data.get("review_comments") or "").strip()

    valid_statuses = {"APPROVED", "REJECTED", "VERIFIED", "REVIEWED", "REQUIRES_CLARIFICATION", "PENDING_REVIEW"}
    if new_status not in valid_statuses:
        return api_error(
            f"Invalid review status '{new_status}'. Allowed: Approved, Rejected, Reviewed, Requires Clarification, Verified.",
            "INVALID_REVIEW_STATUS",
            400,
        )

    bid.officer_review_status = new_status
    if new_status in ("APPROVED", "VERIFIED"):
        bid.verification_status = "VERIFIED"
    elif new_status == "REJECTED":
        bid.verification_status = "NON_COMPLIANT"
    elif new_status == "REQUIRES_CLARIFICATION":
        bid.verification_status = "NEEDS_REVIEW"

    bid.officer_review_comments = comments
    bid.reviewed_by = g.current_user.id
    bid.reviewed_at = datetime.now(timezone.utc)

    # Optionally mark all individual checks as reviewed
    if data.get("mark_all_checks_reviewed", True):
        for chk in bid.compliance_results:
            chk.is_reviewed = True
            if comments and not chk.officer_comment:
                chk.officer_comment = comments

    db.session.commit()

    record_audit_log(
        "Officer Reviewed",
        user=g.current_user,
        tender_id=bid.tender_id,
        bid_id=bid.id,
        result_status=new_status,
        review_comments=comments or f"Officer updated status to {new_status}",
    )

    return api_success(
        {"bid": bid.to_dict(detailed=True)},
        message=f"Officer human review recorded with status '{new_status}'.",
    )


@compliance_bp.route("/api/compliance-results/<int:result_id>/review", methods=["PUT"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def review_single_compliance_check(result_id):
    chk = db.session.get(ComplianceResult, result_id)
    if not chk:
        return api_error("Compliance check result not found.", "CHECK_NOT_FOUND", 404)

    data = request.get_json(silent=True) or {}
    chk.is_reviewed = bool(data.get("is_reviewed", True))
    if "officer_comment" in data:
        chk.officer_comment = str(data["officer_comment"]).strip()
    if "status" in data and data["status"] in ("COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "NOT_APPLICABLE"):
        chk.status = data["status"]

    db.session.commit()
    record_audit_log(
        f"Check Reviewed ({chk.check_code})",
        user=g.current_user,
        bid_id=chk.bid_id,
        result_status=chk.status,
        review_comments=chk.officer_comment,
    )
    return api_success({"compliance_result": chk.to_dict()}, message="Compliance item review saved.")
