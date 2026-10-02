import json
import os
import re
import uuid
from flask import Blueprint, request, g
from backend.config import Config
from backend.extensions import db
from backend.models.models import Tender, Bid, BidItem, Document, Notification
from backend.auth.decorators import jwt_required

from backend.document_processing.pipeline import process_document_pipeline
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error
from backend.utils.validators import validate_file_upload

bid_bp = Blueprint("bid_bp", __name__)


@bid_bp.route("/api/tenders/<int:tender_id>/bids", methods=["POST"])
@jwt_required(allowed_roles=["COMPANY"])
def submit_bid(tender_id):
    tender = db.session.get(Tender, tender_id)
    if not tender:
        return api_error("Tender not found.", "INVALID_TENDER", 404)

    company = g.current_user.company_profile
    if not company:
        return api_error("Company profile not found for current user.", "MISSING_COMPANY_PROFILE", 400)

    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
        uploaded_files = request.files.getlist("documents")
        declared_types_list = request.form.getlist("declared_doc_types")
    else:
        data = request.get_json(silent=True) or {}
        uploaded_files = []
        declared_types_list = []

    quoted_amount = data.get("quoted_amount")
    if quoted_amount is None or str(quoted_amount).strip() == "":
        return api_error("Quoted bid amount is required.", "MISSING_QUOTED_AMOUNT", 400)

    try:
        quoted_val = float(quoted_amount)
    except ValueError:
        return api_error("Quoted bid amount must be a valid number.", "INVALID_QUOTED_AMOUNT", 400)

    bid_number = (data.get("bid_number") or f"GEM-BID-2026-{uuid.uuid4().hex[:6].upper()}").strip()

    bid = Bid(
        bid_number=bid_number,
        tender_id=tender.id,
        company_id=company.id,
        quoted_amount=quoted_val,
        warranty_years=float(data.get("warranty_years") or 3.0),
        delivery_days=int(data.get("delivery_days") or 30),
        local_content_declared=float(data.get("local_content_declared") or company.local_content_percent or 60.0),
        oem_status=(data.get("oem_status") or "Authorized OEM / Reseller").strip(),
        product_name=(data.get("product_name") or "Enterprise Workstation / Server Node").strip(),
        product_model=(data.get("product_model") or "ProLine G9-X").strip(),
        technical_summary=(data.get("technical_summary") or "Meets GeM technical & statutory specifications.").strip(),
        declarations_accepted=str(data.get("declarations_accepted", "true")).lower() in ("true", "1", "yes", "on"),
        submission_status="SUBMITTED",
        verification_status="PENDING",
        officer_review_status="PENDING_REVIEW",
    )
    db.session.add(bid)
    db.session.flush()

    # Add structured BidItems from dynamic form/JSON payload (matching tender thresholds)
    specs_payload = data.get("technical_specifications")
    if isinstance(specs_payload, str):
        try:
            specs_payload = json.loads(specs_payload)
        except Exception:
            specs_payload = None

    added_parameters = set()
    if isinstance(specs_payload, list):
        for sp in specs_payload:
            p_name = str(sp.get("parameter_name") or "").strip()
            if p_name and sp.get("submitted_value") is not None:
                added_parameters.add(p_name.lower())
                sub_val = str(sp["submitted_value"]).strip()
                db.session.add(
                    BidItem(
                        bid_id=bid.id,
                        item_category=(sp.get("item_category") or "TECHNICAL").upper(),
                        parameter_name=p_name,
                        submitted_value=sub_val,
                        unit=str(sp.get("unit") or ""),
                        source_document=str(sp.get("source_document") or "Technical_Bid.pdf"),
                        source_page=int(sp.get("source_page") or 4),
                    )
                )
                if "warranty" in p_name.lower() and not data.get("warranty_years"):
                    try:
                        num_part = re.search(r"(\d+(?:\.\d+)?)", sub_val)
                        if num_part:
                            bid.warranty_years = float(num_part.group(1))
                    except Exception:
                        pass

    # Check direct shorthand fields (ram_gb, ssd_gb, processor, warranty_years) if not already added
    shorthand_specs = [
        ("RAM", data.get("ram_gb"), "GB", 4),
        ("SSD", data.get("ssd_gb"), "GB", 4),
        ("Warranty", data.get("warranty_years"), "Years", 5),
        ("Processor", data.get("processor"), "", 3),
    ]
    for p_name, p_val, p_unit, p_page in shorthand_specs:
        if p_name.lower() not in added_parameters and p_val is not None and str(p_val).strip() != "":
            db.session.add(
                BidItem(
                    bid_id=bid.id,
                    item_category="TECHNICAL",
                    parameter_name=p_name,
                    submitted_value=str(p_val).strip(),
                    unit=p_unit,
                    source_document="Technical_Bid.pdf",
                    source_page=p_page,
                )
            )

    # Process any files uploaded alongside bid submission
    existing_names = set()
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    fallback_type = data.get("declared_doc_type") or ""

    for idx, f_storage in enumerate(uploaded_files):
        if not f_storage or not f_storage.filename:
            continue
        is_valid, err_msg, err_code, safe_name, ext, size_bytes = validate_file_upload(f_storage, existing_names)
        if not is_valid:
            db.session.rollback()
            return api_error(err_msg, err_code, 400)
        existing_names.add(f_storage.filename.strip())

        unique_name = f"bid_{bid.id}_{uuid.uuid4().hex[:6]}_{safe_name}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        f_storage.save(file_path)

        declared_type_for_file = (
            declared_types_list[idx].strip()
            if idx < len(declared_types_list) and declared_types_list[idx]
            else fallback_type
        )

        doc = Document(
            bid_id=bid.id,
            tender_id=tender.id,
            original_filename=f_storage.filename.strip(),
            safe_filename=unique_name,
            file_type=ext,
            file_size_bytes=size_bytes,
            file_path=file_path,
            declared_doc_type=declared_type_for_file,
        )
        db.session.add(doc)
        db.session.flush()
        process_document_pipeline(doc, commit=False)
        record_audit_log(
            "Document Uploaded",
            user=g.current_user,
            tender_id=tender.id,
            bid_id=bid.id,
            document_id=doc.id,
            result_status="PROCESSED",
            commit=False,
        )

    db.session.commit()
    record_audit_log("Bid Submitted", user=g.current_user, tender_id=tender.id, bid_id=bid.id, result_status="SUBMITTED")

    # Notify Tender Officers that requirement has been bidded
    db.session.add(
        Notification(
            role="PROCUREMENT_OFFICER",
            tender_id=tender.id,
            tender_code=tender.tender_code,
            bid_id=bid.id,
            bid_number=bid.bid_number,
            title=f"Tender Requirement Bidded: {tender.tender_code}",
            message=f"Bidder '{company.company_name}' has bidded on tender requirement '{tender.tender_code}' ({tender.title}). Total bids received: {len(tender.bids)}.",
            notification_type="BID_SUBMITTED",
        )
    )
    # Notify Bidder confirming submission
    db.session.add(
        Notification(
            user_id=g.current_user.id,
            role="COMPANY",
            tender_id=tender.id,
            tender_code=tender.tender_code,
            bid_id=bid.id,
            bid_number=bid.bid_number,
            title=f"Bid Submission Confirmed: {tender.tender_code}",
            message=f"You have successfully bidded on tender requirement '{tender.tender_code}'. Bid reference: #{bid.bid_number}.",
            notification_type="BID_SUBMITTED",
        )
    )
    db.session.commit()

    return api_success(
        {"bid": bid.to_dict(detailed=True)},
        message="Bid submitted successfully.",
        status_code=201,
    )



@bid_bp.route("/api/bids", methods=["GET"])
@jwt_required()
def list_bids():
    user = g.current_user
    tender_id = request.args.get("tender_id", type=int)
    risk_filter = request.args.get("risk_level")
    status_filter = request.args.get("verification_status")

    query = Bid.query.order_by(Bid.submitted_at.desc())

    # Role-based filtering: Companies only see their own bids; Officers see all bids
    if user.role_name == "COMPANY":
        if not user.company_profile:
            return api_success({"bids": [], "total": 0})
        query = query.filter_by(company_id=user.company_profile.id)

    if tender_id:
        query = query.filter_by(tender_id=tender_id)
    if risk_filter:
        query = query.filter_by(risk_level=risk_filter.upper())
    if status_filter:
        query = query.filter_by(verification_status=status_filter.upper())

    bids = query.all()
    return api_success({
        "bids": [b.to_dict(detailed=False) for b in bids],
        "total": len(bids),
    })


@bid_bp.route("/api/bids/<int:bid_id>", methods=["GET"])
@jwt_required()
def get_bid(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    user = g.current_user
    if user.role_name == "COMPANY":
        if not user.company_profile or bid.company_id != user.company_profile.id:
            return api_error(
                "Unauthorized access. You can only view bids submitted by your company.",
                "UNAUTHORIZED_BID_ACCESS",
                403,
            )

    return api_success({"bid": bid.to_dict(detailed=True)})


@bid_bp.route("/api/dashboard/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    user = g.current_user
    all_tenders = Tender.query.order_by(Tender.created_at.desc()).all()
    active_tenders = [t for t in all_tenders if t.status == "PUBLISHED"]

    if user.role_name == "PROCUREMENT_OFFICER":
        all_bids = Bid.query.order_by(Bid.submitted_at.desc()).all()
        verified_bids = [b for b in all_bids if b.verification_status == "VERIFIED"]
        needs_review_bids = [b for b in all_bids if b.verification_status == "NEEDS_REVIEW"]
        pending_bids = [b for b in all_bids if b.verification_status == "PENDING"]
        high_risk_bids = [b for b in all_bids if b.risk_level == "HIGH"]
        medium_risk_bids = [b for b in all_bids if b.risk_level == "MEDIUM"]
        low_risk_bids = [b for b in all_bids if b.risk_level == "LOW"]

        avg_score = (
            round(sum(b.overall_compliance_score for b in all_bids if b.overall_compliance_score > 0) / max(1, len([b for b in all_bids if b.overall_compliance_score > 0])), 1)
            if all_bids
            else 0.0
        )

        return api_success({
            "role": "PROCUREMENT_OFFICER",
            "kpis": {
                "total_tenders": len(all_tenders),
                "active_tenders": len(active_tenders),
                "total_bids": len(all_bids),
                "verified_bids": len(verified_bids),
                "pending_verification": len(pending_bids),
                "needs_review": len(needs_review_bids),
                "high_risk_bids": len(high_risk_bids),
                "medium_risk_bids": len(medium_risk_bids),
                "low_risk_bids": len(low_risk_bids),
                "average_compliance_score": avg_score,
            },
            "recent_tenders": [t.to_dict(include_requirements=False) for t in all_tenders[:5]],
            "recent_bids": [b.to_dict(detailed=False) for b in all_bids[:8]],
            "risk_alerts": [
                b.to_dict(detailed=False)
                for b in all_bids
                if b.risk_level in ("HIGH", "MEDIUM")
            ][:6],
        })

    # Company Dashboard Stats
    comp = user.company_profile
    my_bids = Bid.query.filter_by(company_id=comp.id).order_by(Bid.submitted_at.desc()).all() if comp else []
    applied_tender_ids = {b.tender_id for b in my_bids}

    return api_success({
        "role": "COMPANY",
        "kpis": {
            "available_tenders": len(active_tenders),
            "applied_tenders": len(applied_tender_ids),
            "submitted_bids": len(my_bids),
            "verified_bids": len([b for b in my_bids if b.verification_status == "VERIFIED"]),
            "needs_review_or_clarification": len([
                b for b in my_bids
                if b.verification_status == "NEEDS_REVIEW" or b.officer_review_status == "REQUIRES_CLARIFICATION"
            ]),
        },
        "available_tenders": [t.to_dict(include_requirements=True) for t in active_tenders],
        "my_bids": [b.to_dict(detailed=True) for b in my_bids],
    })
