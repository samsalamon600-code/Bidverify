import os
import uuid
from flask import Blueprint, request, g, send_file
from backend.extensions import db
from backend.models.models import Bid, Report
from backend.auth.decorators import jwt_required
from backend.reports.pdf_generator import generate_compliance_pdf_report
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error

report_bp = Blueprint("report_bp", __name__)


@report_bp.route("/api/bids/<int:bid_id>/report", methods=["POST"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def create_bid_pdf_report(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    report_code = f"RPT-GEM-{bid.id:03d}-{uuid.uuid4().hex[:5].upper()}"
    try:
        pdf_path = generate_compliance_pdf_report(bid, report_code, generated_by_user=g.current_user)
    except Exception as exc:
        return api_error(f"Failed to generate PDF report: {str(exc)}", "REPORT_GENERATION_FAILURE", 500)

    report = Report(
        report_code=report_code,
        bid_id=bid.id,
        tender_id=bid.tender_id,
        generated_by=g.current_user.id,
        file_path=pdf_path,
        overall_score=bid.overall_compliance_score,
        risk_level=bid.risk_level,
        review_status=bid.officer_review_status,
    )
    db.session.add(report)
    db.session.commit()

    record_audit_log(
        "Report Generated",
        user=g.current_user,
        tender_id=bid.tender_id,
        bid_id=bid.id,
        result_status=report_code,
        review_comments=f"Generated downloadable PDF compliance report ({report_code}).",
    )

    return api_success(
        {
            "report": report.to_dict(),
            "download_url": f"/api/reports/{report.id}?download=true",
        },
        message="PDF Compliance Verification Report generated successfully.",
        status_code=201,
    )


@report_bp.route("/api/reports/<int:report_id>", methods=["GET"])
@jwt_required()
def get_or_download_report(report_id):
    report = db.session.get(Report, report_id)
    if not report:
        return api_error("Report not found.", "REPORT_NOT_FOUND", 404)

    download = request.args.get("download", "false").lower() == "true"
    if download:
        if not os.path.exists(report.file_path):
            # Regenerate on the fly if file was cleaned up
            bid = db.session.get(Bid, report.bid_id)
            if bid:
                report.file_path = generate_compliance_pdf_report(bid, report.report_code, g.current_user)
                db.session.commit()
        return send_file(
            report.file_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{report.report_code}.pdf",
        )

    return api_success({
        "report": report.to_dict(),
        "download_url": f"/api/reports/{report.id}?download=true",
    })


@report_bp.route("/api/reports", methods=["GET"])
@jwt_required()
def list_reports():
    bid_id = request.args.get("bid_id", type=int)
    query = Report.query.order_by(Report.generated_at.desc())
    if bid_id:
        query = query.filter_by(bid_id=bid_id)
    reports = query.all()
    return api_success({"reports": [r.to_dict() for r in reports]})
