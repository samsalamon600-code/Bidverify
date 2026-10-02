import os
import shutil
import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.models import Vendor, Document, ExtractedData, AuditLog, User
from backend.app.schemas.schemas import DocumentResponse, ExtractedDataResponse
from backend.app.services.ocr_service import process_document
from backend.app.utils.security import get_current_user

router = APIRouter(tags=["Documents"])

SAMPLES_DIR = os.path.join(settings.PROJECT_ROOT, "assets", "sample_documents")

@router.get("/sample-documents")
def list_sample_documents():
    if not os.path.exists(SAMPLES_DIR):
        return []
    files = []
    for f in os.listdir(SAMPLES_DIR):
        doc_type = "GST Certificate" if "gst" in f.lower() else ("PAN" if "pan" in f.lower() else "Udyam Certificate")
        files.append({
            "file_name": f,
            "doc_type": doc_type,
            "size": os.path.getsize(os.path.join(SAMPLES_DIR, f))
        })
    return files

@router.post("/vendors/{vendor_id}/load-sample-document")
def load_sample_document(
    vendor_id: int,
    sample_type: str = Form("gst"),  # gst, pan, udyam
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    sample_file_map = {
        "gst": ("Sample_GST_Certificate.pdf", "GST Certificate", "application/pdf"),
        "pan": ("Sample_PAN_Card.png", "PAN", "image/png"),
        "udyam": ("Sample_Udyam_Certificate.pdf", "Udyam Certificate", "application/pdf")
    }

    key = sample_type.lower()
    if key not in sample_file_map:
        key = "gst"

    file_name, doc_type, mime_type = sample_file_map[key]
    source_path = os.path.join(SAMPLES_DIR, file_name)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Sample document file not found")

    # Copy to uploads
    unique_name = f"{vendor_id}_{uuid.uuid4().hex[:8]}_{file_name}"
    target_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    shutil.copyfile(source_path, target_path)

    file_size = os.path.getsize(target_path)

    # Create document
    doc = Document(
        vendor_id=vendor_id,
        doc_type=doc_type,
        file_name=file_name,
        file_path=target_path,
        file_size=file_size,
        mime_type=mime_type,
        status="Uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Immediately run OCR extraction
    ocr_result = process_document(target_path)
    extracted_obj = ExtractedData(
        document_id=doc.id,
        vendor_id=vendor_id,
        raw_text=ocr_result.get("raw_text", ""),
        structured_json=json.dumps(ocr_result.get("structured_data", {})),
        ocr_confidence=ocr_result.get("ocr_confidence", 95.0)
    )
    db.add(extracted_obj)

    doc.status = "Processed"
    doc.ocr_confidence = ocr_result.get("ocr_confidence", 95.0)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "officer@bidverify.com",
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        action="Sample Document Loaded & OCR Extracted",
        details_json=json.dumps({"document_id": doc.id, "doc_type": doc_type, "ocr_confidence": doc.ocr_confidence})
    )
    db.add(audit)
    db.commit()

    return {
        "document_id": doc.id,
        "vendor_id": doc.vendor_id,
        "doc_type": doc.doc_type,
        "file_name": doc.file_name,
        "ocr_confidence": doc.ocr_confidence,
        "status": doc.status,
        "structured_data": ocr_result.get("structured_data", {})
    }

@router.post("/vendors/{vendor_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    vendor_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form("Other"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    allowed_exts = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{file_ext}'. Allowed: {', '.join(allowed_exts)}")

    unique_name = f"{vendor_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    content = await file.read()
    file_size = len(content)

    if file_size > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum permitted limit of 15MB")

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        vendor_id=vendor_id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        status="Uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "officer@bidverify.com",
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        action="Document Uploaded",
        details_json=json.dumps({"document_id": doc.id, "file_name": doc.file_name, "doc_type": doc_type})
    )
    db.add(audit)
    db.commit()

    return DocumentResponse(
        id=doc.id,
        vendor_id=doc.vendor_id,
        doc_type=doc.doc_type,
        file_name=doc.file_name,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        status=doc.status,
        ocr_confidence=doc.ocr_confidence,
        uploaded_at=doc.uploaded_at
    )

@router.post("/documents/{document_id}/extract", response_model=ExtractedDataResponse)
def trigger_extraction(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        ocr_result = process_document(doc.file_path)
        raw_text = ocr_result.get("raw_text", "")
        ocr_confidence = ocr_result.get("ocr_confidence", 85.0)
        structured = ocr_result.get("structured_data", {})

        existing = db.query(ExtractedData).filter(ExtractedData.document_id == document_id).first()
        if existing:
            existing.raw_text = raw_text
            existing.structured_json = json.dumps(structured)
            existing.ocr_confidence = ocr_confidence
            extracted_obj = existing
        else:
            extracted_obj = ExtractedData(
                document_id=doc.id,
                vendor_id=doc.vendor_id,
                raw_text=raw_text,
                structured_json=json.dumps(structured),
                ocr_confidence=ocr_confidence
            )
            db.add(extracted_obj)

        doc.status = "Processed"
        doc.ocr_confidence = ocr_confidence
        db.commit()
        db.refresh(extracted_obj)

        vendor = db.query(Vendor).filter(Vendor.id == doc.vendor_id).first()
        audit = AuditLog(
            user_id=current_user.id if current_user else None,
            user_email=current_user.email if current_user else "officer@bidverify.com",
            vendor_id=doc.vendor_id,
            vendor_name=vendor.name if vendor else "",
            action="OCR Extraction Completed",
            details_json=json.dumps({"document_id": doc.id, "ocr_confidence": ocr_confidence})
        )
        db.add(audit)
        db.commit()

        return ExtractedDataResponse(
            id=extracted_obj.id,
            document_id=extracted_obj.document_id,
            vendor_id=extracted_obj.vendor_id,
            raw_text=extracted_obj.raw_text,
            structured_json=structured,
            ocr_confidence=extracted_obj.ocr_confidence,
            extracted_at=extracted_obj.extracted_at
        )
    except Exception as e:
        doc.status = "Error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

@router.get("/vendors/{vendor_id}/documents", response_model=List[DocumentResponse])
def get_vendor_documents(vendor_id: int, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.vendor_id == vendor_id).all()
    res = []
    for d in docs:
        ext_dict = None
        if d.extracted_data and d.extracted_data.structured_json:
            try:
                ext_dict = json.loads(d.extracted_data.structured_json)
            except Exception:
                ext_dict = {}
        res.append(DocumentResponse(
            id=d.id,
            vendor_id=d.vendor_id,
            doc_type=d.doc_type,
            file_name=d.file_name,
            file_size=d.file_size,
            mime_type=d.mime_type,
            status=d.status,
            ocr_confidence=d.ocr_confidence,
            uploaded_at=d.uploaded_at,
            extracted_data=ext_dict
        ))
    return res

@router.get("/documents", response_model=List[DocumentResponse])
def get_all_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    res = []
    for d in docs:
        ext_dict = None
        if d.extracted_data and d.extracted_data.structured_json:
            try:
                ext_dict = json.loads(d.extracted_data.structured_json)
            except Exception:
                ext_dict = {}
        res.append(DocumentResponse(
            id=d.id,
            vendor_id=d.vendor_id,
            doc_type=d.doc_type,
            file_name=d.file_name,
            file_size=d.file_size,
            mime_type=d.mime_type,
            status=d.status,
            ocr_confidence=d.ocr_confidence,
            uploaded_at=d.uploaded_at,
            extracted_data=ext_dict
        ))
    return res

@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}
