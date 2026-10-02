import os
import uuid
from flask import Blueprint, request, g, send_file
from backend.config import Config
from backend.extensions import db
from backend.models.models import Bid, Document
from backend.auth.decorators import jwt_required
from backend.document_processing.pipeline import process_document_pipeline
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error
from backend.utils.validators import validate_file_upload

document_bp = Blueprint("document_bp", __name__)


@document_bp.route("/api/bids/<int:bid_id>/documents", methods=["POST"])
@jwt_required()
def upload_bid_documents(bid_id):
    bid = db.session.get(Bid, bid_id)
    if not bid:
        return api_error("Bid not found.", "INVALID_BID", 404)

    user = g.current_user
    if user.role_name == "COMPANY":
        if not user.company_profile or bid.company_id != user.company_profile.id:
            return api_error("Unauthorized to upload documents to this bid.", "UNAUTHORIZED_BID_ACCESS", 403)

    files = request.files.getlist("documents") or request.files.getlist("file")
    if not files or all(not f.filename for f in files):
        return api_error("No files provided for upload.", "MISSING_FILE", 400)

    declared_types_list = request.form.getlist("declared_doc_types")
    fallback_type = (request.form.get("declared_doc_type") or "").strip()
    existing_filenames = {d.original_filename for d in bid.documents}

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    uploaded_docs = []

    for idx, f_storage in enumerate(files):
        if not f_storage or not f_storage.filename:
            continue

        is_valid, err_msg, err_code, safe_name, ext, size_bytes = validate_file_upload(
            f_storage, existing_filenames
        )
        if not is_valid:
            db.session.rollback()
            return api_error(err_msg, err_code, 400)

        existing_filenames.add(f_storage.filename.strip())
        unique_name = f"bid_{bid.id}_{uuid.uuid4().hex[:6]}_{safe_name}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        f_storage.save(file_path)

        declared_type_for_doc = (
            declared_types_list[idx].strip()
            if idx < len(declared_types_list) and declared_types_list[idx]
            else fallback_type
        )

        doc = Document(
            bid_id=bid.id,
            tender_id=bid.tender_id,
            original_filename=f_storage.filename.strip(),
            safe_filename=unique_name,
            file_type=ext,
            file_size_bytes=size_bytes,
            file_path=file_path,
            declared_doc_type=declared_type_for_doc,
        )
        db.session.add(doc)
        db.session.flush()

        # Run OCR & NLP pipeline automatically on upload
        process_document_pipeline(doc, commit=False)
        uploaded_docs.append(doc)

        record_audit_log(
            "Document Uploaded & Processed",
            user=user,
            tender_id=bid.tender_id,
            bid_id=bid.id,
            document_id=doc.id,
            result_status=doc.detected_doc_type,
            commit=False,
        )

    db.session.commit()
    return api_success(
        {"documents": [d.to_dict(include_extraction=True) for d in uploaded_docs]},
        message=f"{len(uploaded_docs)} document(s) uploaded and analyzed successfully.",
        status_code=201,
    )


@document_bp.route("/api/documents/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_document(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc:
        return api_error("Document not found.", "MISSING_DOCUMENT", 404)

    user = g.current_user
    if user.role_name == "COMPANY" and doc.bid_id:
        bid = db.session.get(Bid, doc.bid_id)
        if bid and (not user.company_profile or bid.company_id != user.company_profile.id):
            return api_error("Unauthorized access to document.", "UNAUTHORIZED_DOCUMENT_ACCESS", 403)

    return api_success({"document": doc.to_dict(include_extraction=True)})


@document_bp.route("/api/documents/<int:doc_id>/view", methods=["GET"])
@jwt_required()
def view_document(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc:
        return api_error("Document not found.", "MISSING_DOCUMENT", 404)

    user = g.current_user
    # Both Procurement Officer and the Company submitting the bid can access
    if user.role_name == "COMPANY" and doc.bid_id:
        bid = db.session.get(Bid, doc.bid_id)
        if bid and (not user.company_profile or bid.company_id != user.company_profile.id):
            return api_error("Unauthorized access to document.", "UNAUTHORIZED_DOCUMENT_ACCESS", 403)

    if not doc.file_path or not os.path.exists(doc.file_path):
        fallback_text = (doc.extracted_text or doc.raw_ocr_text or f"Document: {doc.original_filename}\nCategory: {doc.declared_doc_type}").strip()
        from io import BytesIO
        buf = BytesIO(fallback_text.encode("utf-8"))
        buf.seek(0)
        resp = send_file(buf, mimetype="text/plain; charset=utf-8", as_attachment=False, download_name=f"{doc.original_filename}.txt")
        resp.headers["Content-Disposition"] = f'inline; filename="{doc.original_filename}.txt"'
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return resp

    ext = (doc.original_filename.rsplit(".", 1)[-1] if "." in doc.original_filename else "").lower()
    mimetype = "application/octet-stream"
    if ext == "pdf":
        try:
            with open(doc.file_path, "rb") as test_f:
                header = test_f.read(8)
                if header.startswith(b"%PDF-"):
                    mimetype = "application/pdf"
                else:
                    mimetype = "text/plain; charset=utf-8"
        except Exception:
            mimetype = "application/pdf"
    elif ext == "png":
        mimetype = "image/png"
    elif ext in ("jpg", "jpeg"):
        mimetype = "image/jpeg"
    elif ext == "webp":
        mimetype = "image/webp"
    elif ext in ("txt", "log", "csv"):
        mimetype = "text/plain; charset=utf-8"

    resp = send_file(doc.file_path, mimetype=mimetype, as_attachment=False, download_name=doc.original_filename)
    resp.headers["Content-Disposition"] = f'inline; filename="{doc.original_filename}"'
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
    return resp


@document_bp.route("/api/documents/<int:doc_id>/download", methods=["GET"])
@jwt_required()
def download_document(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc:
        return api_error("Document not found.", "MISSING_DOCUMENT", 404)

    user = g.current_user
    # Both Procurement Officer and the Company submitting the bid can access
    if user.role_name == "COMPANY" and doc.bid_id:
        bid = db.session.get(Bid, doc.bid_id)
        if bid and (not user.company_profile or bid.company_id != user.company_profile.id):
            return api_error("Unauthorized access to document.", "UNAUTHORIZED_DOCUMENT_ACCESS", 403)

    if not doc.file_path or not os.path.exists(doc.file_path):
        fallback_text = (doc.extracted_text or doc.raw_ocr_text or f"Document: {doc.original_filename}\nCategory: {doc.declared_doc_type}").strip()
        from io import BytesIO
        buf = BytesIO(fallback_text.encode("utf-8"))
        buf.seek(0)
        return send_file(buf, mimetype="text/plain; charset=utf-8", as_attachment=True, download_name=f"{doc.original_filename}.txt")

    # If the file extension is .pdf but the file content is plain text, serve as text/plain
    mimetype = None
    try:
        with open(doc.file_path, "rb") as test_f:
            header = test_f.read(8)
            if doc.original_filename.lower().endswith(".pdf") and not header.startswith(b"%PDF-"):
                mimetype = "text/plain; charset=utf-8"
    except Exception:
        pass

    return send_file(doc.file_path, mimetype=mimetype, as_attachment=True, download_name=doc.original_filename)



@document_bp.route("/api/documents/<int:doc_id>/process", methods=["POST"])
@jwt_required()
def process_document(doc_id):
    doc = db.session.get(Document, doc_id)
    if not doc:
        return api_error("Document not found.", "MISSING_DOCUMENT", 404)

    res = process_document_pipeline(doc, commit=True)
    if not res["success"]:
        record_audit_log(
            "Document Processing Failed",
            user=g.current_user,
            tender_id=doc.tender_id,
            bid_id=doc.bid_id,
            document_id=doc.id,
            result_status="FAILED",
            review_comments=res.get("error"),
        )
        return api_error(res.get("error", "OCR failure"), res.get("error_code", "OCR_FAILURE"), 422)

    record_audit_log(
        "Document Processed",
        user=g.current_user,
        tender_id=doc.tender_id,
        bid_id=doc.bid_id,
        document_id=doc.id,
        result_status=doc.detected_doc_type,
    )
    return api_success(
        {"document": res["document"]},
        message="Document processed via OpenCV + EasyOCR + NLP pipeline.",
    )
