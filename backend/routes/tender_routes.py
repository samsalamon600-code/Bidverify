import json
import os
import uuid
from flask import Blueprint, request, g
from backend.config import Config
from backend.extensions import db
from backend.models.models import (
    Tender,
    TenderRequirement,
    Document,
    Bid,
    BidItem,
    ComplianceResult,
    RiskResult,
    Evidence,
    Report,
    DocumentExtraction,
    AuditLog,
    Notification,
    User,
    Company,
)
from backend.auth.decorators import jwt_required, extract_bearer_token, decode_jwt_token
from backend.document_processing.pipeline import process_document_pipeline
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error
from backend.utils.validators import validate_file_upload

tender_bp = Blueprint("tender_bp", __name__, url_prefix="/api/tenders")


def _get_current_company_id():
    token = extract_bearer_token()
    if not token:
        return None
    try:
        payload = decode_jwt_token(token)
        user_id = int(payload.get("user_id") or payload.get("sub"))
        user = db.session.get(User, user_id)
        if user and user.role_name == "COMPANY" and user.company_profile:
            return user.company_profile.id
    except Exception:
        return None
    return None


@tender_bp.route("", methods=["GET"])
def list_tenders():
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    search_q = (request.args.get("q") or "").strip().lower()

    query = Tender.query.order_by(Tender.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter.upper())
    if category_filter:
        query = query.filter_by(category=category_filter)

    tenders = query.all()
    company_id = _get_current_company_id()
    company_bids = {}
    if company_id:
        bids = Bid.query.filter_by(company_id=company_id).all()
        for b in bids:
            company_bids[b.tender_id] = b

    result = []
    for t in tenders:
        if search_q:
            haystack = f"{t.tender_code} {t.title} {t.department} {t.category}".lower()
            if search_q not in haystack:
                continue
        tdict = t.to_dict(include_requirements=True)
        tdict["is_bidded"] = (len(t.bids) > 0)
        if company_id:
            user_bid = company_bids.get(t.id)
            if user_bid:
                tdict["has_bidded"] = True
                tdict["existing_bid_id"] = user_bid.id
                tdict["existing_bid_number"] = user_bid.bid_number
                tdict["existing_bid_status"] = user_bid.submission_status
            else:
                tdict["has_bidded"] = False
        else:
            tdict["has_bidded"] = False

        result.append(tdict)

    return api_success({"tenders": result, "total": len(result)})


@tender_bp.route("/<int:tender_id>", methods=["GET"])
def get_tender(tender_id):
    tender = db.session.get(Tender, tender_id)
    if not tender:
        return api_error("Tender not found.", "INVALID_TENDER", 404)

    tdict = tender.to_dict(include_requirements=True)
    tdict["is_bidded"] = (len(tender.bids) > 0)


    company_id = _get_current_company_id()
    if company_id:
        user_bid = Bid.query.filter_by(tender_id=tender.id, company_id=company_id).first()
        if user_bid:
            tdict["has_bidded"] = True
            tdict["existing_bid_id"] = user_bid.id
            tdict["existing_bid_number"] = user_bid.bid_number
            tdict["existing_bid_status"] = user_bid.submission_status
        else:
            tdict["has_bidded"] = False
    else:
        tdict["has_bidded"] = False

    return api_success({"tender": tdict})



@tender_bp.route("", methods=["POST"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def create_tender():
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
        uploaded_file = request.files.get("tender_document")
    else:
        data = request.get_json(silent=True) or {}
        uploaded_file = None

    tender_code = (data.get("tender_code") or f"GEM/2026/B/{uuid.uuid4().hex[:7].upper()}").strip()
    title = (data.get("title") or "").strip()
    department = (data.get("department") or "").strip()

    if not title or not department:
        return api_error("Tender Title and Department are required.", "MISSING_TENDER_FIELDS", 400)

    if Tender.query.filter_by(tender_code=tender_code).first():
        return api_error(f"Tender ID '{tender_code}' already exists.", "DUPLICATE_TENDER_CODE", 409)

    req_docs = data.get("required_documents", "")
    if isinstance(req_docs, list):
        req_docs_str = json.dumps(req_docs)
    else:
        req_docs_str = str(req_docs)

    tender = Tender(
        tender_code=tender_code,
        title=title,
        department=department,
        description=data.get("description", ""),
        publication_date=data.get("publication_date", "2026-09-26"),
        closing_date=data.get("closing_date", "2026-10-25"),
        category=data.get("category", "IT Hardware & Enterprise Systems"),
        estimated_value=float(data.get("estimated_value") or 2500000.0),
        eligibility_requirements=data.get("eligibility_requirements", "Minimum 3 years OEM/Reseller experience"),
        technical_requirements=data.get("technical_requirements", "RAM >= 16 GB, SSD >= 512 GB, Warranty >= 3 Years"),
        statutory_requirements=data.get("statutory_requirements", "Active GSTIN, Valid PAN, Udyam/MSME, EPFO/ESIC"),
        required_documents=req_docs_str or json.dumps([
            "Technical Bid",
            "GST Certificate",
            "PAN",
            "Udyam/MSME Certificate",
            "OEM Authorization",
        ]),
        local_content_requirements=float(data.get("local_content_requirements") or 50.0),
        oem_requirements=data.get("oem_requirements", "Valid OEM Authorization (MAF) or Direct OEM Registration"),
        other_requirements=data.get("other_requirements", "ISO 9001 & BIS Certification"),
        status=(data.get("status") or "PUBLISHED").upper(),
        created_by=g.current_user.id,
    )
    db.session.add(tender)
    db.session.flush()

    # Parse structured requirements if provided, or auto-extract from technical_requirements text
    structured_reqs = (
        data.get("structured_requirements")
        or data.get("technical_specifications")
        or data.get("specifications")
    )
    if isinstance(structured_reqs, str):
        try:
            structured_reqs = json.loads(structured_reqs)
        except Exception:
            structured_reqs = None

    if structured_reqs and isinstance(structured_reqs, list):
        for r in structured_reqs:
            if r.get("parameter_name") and r.get("required_value") is not None:
                tr = TenderRequirement(
                    tender_id=tender.id,
                    category=(r.get("category") or "TECHNICAL").upper(),
                    parameter_name=r["parameter_name"].strip(),
                    operator=r.get("operator") or ">=",
                    required_value=str(r["required_value"]).strip(),
                    unit=r.get("unit") or "",
                    is_mandatory=bool(r.get("is_mandatory", True)),
                    description=r.get("description") or "",
                )
                db.session.add(tr)
    else:
        # Default structured technical requirements parsed from form fields
        default_reqs = [
            ("TECHNICAL", "RAM", ">=", data.get("req_ram_gb", "16"), "GB"),
            ("TECHNICAL", "SSD", ">=", data.get("req_ssd_gb", "512"), "GB"),
            ("TECHNICAL", "Warranty", ">=", data.get("req_warranty_years", "3"), "Years"),
        ]
        for cat, param, op, val, unit in default_reqs:
            if val:
                db.session.add(
                    TenderRequirement(
                        tender_id=tender.id,
                        category=cat,
                        parameter_name=param,
                        operator=op,
                        required_value=str(val),
                        unit=unit,
                        is_mandatory=True,
                    )
                )

    # Handle optional Tender Document file upload
    if uploaded_file and uploaded_file.filename:
        is_valid, err_msg, err_code, safe_name, ext, size_bytes = validate_file_upload(uploaded_file)
        if not is_valid:
            return api_error(err_msg, err_code, 400)

        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        unique_name = f"tender_{tender.id}_{uuid.uuid4().hex[:6]}_{safe_name}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        uploaded_file.save(file_path)
        tender.tender_document_path = file_path

        doc = Document(
            tender_id=tender.id,
            original_filename=uploaded_file.filename,
            safe_filename=unique_name,
            file_type=ext,
            file_size_bytes=size_bytes,
            file_path=file_path,
            declared_doc_type="Tender Document",
        )
        db.session.add(doc)
        db.session.flush()
        process_document_pipeline(doc, commit=False)

    db.session.commit()
    record_audit_log("Tender Created", user=g.current_user, tender_id=tender.id, result_status="PUBLISHED")

    return api_success(
        {"tender": tender.to_dict(include_requirements=True)},
        message="Tender created and published successfully.",
        status_code=201,
    )


@tender_bp.route("/<int:tender_id>", methods=["PUT"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def update_tender(tender_id):
    tender = db.session.get(Tender, tender_id)
    if not tender:
        return api_error("Tender not found.", "INVALID_TENDER", 404)

    data = request.get_json(silent=True) or {}
    for field in (
        "title",
        "department",
        "description",
        "publication_date",
        "closing_date",
        "category",
        "eligibility_requirements",
        "technical_requirements",
        "statutory_requirements",
        "oem_requirements",
        "other_requirements",
        "status",
    ):
        if field in data and data[field] is not None:
            setattr(tender, field, data[field])

    if "estimated_value" in data:
        tender.estimated_value = float(data["estimated_value"] or 0.0)
    if "local_content_requirements" in data:
        tender.local_content_requirements = float(data["local_content_requirements"] or 0.0)
    if "required_documents" in data:
        req_docs = data["required_documents"]
        tender.required_documents = json.dumps(req_docs) if isinstance(req_docs, list) else str(req_docs)

    db.session.commit()
    record_audit_log("Tender Updated", user=g.current_user, tender_id=tender.id, result_status=tender.status)
    return api_success({"tender": tender.to_dict(include_requirements=True)}, message="Tender updated successfully.")


@tender_bp.route("/<int:tender_id>", methods=["DELETE"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def delete_tender(tender_id):
    tender = db.session.get(Tender, tender_id)
    if not tender:
        return api_error("Tender not found.", "INVALID_TENDER", 404)

    tender_code = tender.tender_code
    tender_title = tender.title

    try:
        # 1. Clean up all bids associated with this tender and all their dependent records
        bids = Bid.query.filter_by(tender_id=tender.id).all()
        for b in bids:
            Evidence.query.filter_by(bid_id=b.id).delete()
            ComplianceResult.query.filter_by(bid_id=b.id).delete()
            RiskResult.query.filter_by(bid_id=b.id).delete()
            Report.query.filter_by(bid_id=b.id).delete()
            BidItem.query.filter_by(bid_id=b.id).delete()
            bid_docs = Document.query.filter_by(bid_id=b.id).all()
            for doc in bid_docs:
                DocumentExtraction.query.filter_by(document_id=doc.id).delete()
                db.session.delete(doc)
            db.session.delete(b)

        # 2. Clean up tender-level documents
        tender_docs = Document.query.filter_by(tender_id=tender.id).all()
        for doc in tender_docs:
            DocumentExtraction.query.filter_by(document_id=doc.id).delete()
            db.session.delete(doc)

        # 3. Clean up any remaining reports referencing this tender
        Report.query.filter_by(tender_id=tender.id).delete()

        # 4. Clean up notifications referencing this tender
        Notification.query.filter_by(tender_id=tender.id).delete()

        # 5. Clean up tender requirements
        TenderRequirement.query.filter_by(tender_id=tender.id).delete()

        # 6. Nullify tender_id in AuditLog to preserve history without FK violations
        AuditLog.query.filter_by(tender_id=tender.id).update({"tender_id": None})

        # 7. Record deletion audit entry
        record_audit_log(
            "Tender Deleted",
            user=g.current_user,
            result_status="DELETED",
            review_comments=f"Tender {tender_code} ('{tender_title}') and all associated bids/evaluations were permanently deleted by officer.",
            commit=False,
        )

        # 8. Delete the tender itself
        db.session.delete(tender)
        db.session.commit()

        return api_success(
            {"deleted_tender_code": tender_code},
            message=f"Tender '{tender_code}' and all related records deleted successfully."
        )
    except Exception as exc:
        db.session.rollback()
        return api_error(f"Failed to delete tender: {str(exc)}", "TENDER_DELETE_ERROR", 500)


@tender_bp.route("/<int:tender_id>/notify-bidded", methods=["POST"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def notify_tender_bidded(tender_id):
    """
    Notifies both Tender Officer and Bidders that this tender requirement has already been bidded.
    Creates structured notifications for:
    1) Evaluation Officer(s)
    2) Participating Bidders (and general bidder announcement)
    """
    tender = db.session.get(Tender, tender_id)
    if not tender:
        return api_error("Tender not found.", "INVALID_TENDER", 404)

    data = request.get_json(silent=True) or {}
    bids = Bid.query.filter_by(tender_id=tender.id).all()
    bids_count = len(bids)

    custom_msg = data.get("custom_message")
    officer_msg = custom_msg or (
        f"Notice: Tender requirement for '{tender.tender_code}' ({tender.title}) has been marked as bidded. "
        f"Current submissions: {bids_count} active bid(s). Review and compliance verification is underway."
    )
    bidder_msg = (
        f"Notice: Tender requirement for '{tender.tender_code}' ({tender.title}) has already received bids "
        f"and is active in the evaluation stage. Bidders can track submission compliance and document statuses."
    )

    # 1. Notification for the calling Tender Officer
    notif_officer = Notification(
        user_id=g.current_user.id,
        role="PROCUREMENT_OFFICER",
        tender_id=tender.id,
        tender_code=tender.tender_code,
        title=f"Tender Requirement Bidded Notice: {tender.tender_code}",
        message=officer_msg,
        notification_type="TENDER_BIDDED",
    )
    db.session.add(notif_officer)

    # 2. Broadcast notification for all Bidders
    notif_broadcast = Notification(
        user_id=None,
        role="COMPANY",
        tender_id=tender.id,
        tender_code=tender.tender_code,
        title=f"Tender Requirement Bidded Notice: {tender.tender_code}",
        message=bidder_msg,
        notification_type="TENDER_BIDDED",
    )
    db.session.add(notif_broadcast)

    # 3. Direct notification to each company who submitted a bid on this tender
    for b in bids:
        if b.company and b.company.user_id:
            db.session.add(
                Notification(
                    user_id=b.company.user_id,
                    role="COMPANY",
                    tender_id=tender.id,
                    tender_code=tender.tender_code,
                    bid_id=b.id,
                    bid_number=b.bid_number,
                    title=f"Tender Requirement Bidded: {tender.tender_code}",
                    message=(
                        f"Your submitted bid {b.bid_number} for tender requirement '{tender.tender_code}' "
                        f"is acknowledged and under evaluation."
                    ),
                    notification_type="TENDER_BIDDED",
                )
            )

    record_audit_log(
        "Tender Requirement Bidded Notified",
        user=g.current_user,
        tender_id=tender.id,
        result_status="NOTIFIED",
        review_comments=f"Broadcast notification sent to both Tender Officer and Bidders for tender {tender.tender_code}.",
        commit=False,
    )
    db.session.commit()

    return api_success(
        {
            "tender_id": tender.id,
            "tender_code": tender.tender_code,
            "bids_count": bids_count,
        },
        message=f"Notification broadcast sent to both Tender Officer and Bidders: Tender requirement '{tender.tender_code}' is marked as bidded."
    )

