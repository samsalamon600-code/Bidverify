import os
import json
import uuid
import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models.models import (
    Vendor, VerificationResult, ComplianceCheck, RiskAssessment,
    ReportRecord, AuditLog, User
)
from backend.app.services.report_service import generate_vendor_pdf_report
from backend.app.utils.security import get_current_user

router = APIRouter(tags=["Reports"])

@router.post("/vendors/{vendor_id}/report")
def generate_report(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Fetch verification results
    verif_results = db.query(VerificationResult).filter(VerificationResult.vendor_id == vendor_id).all()
    matrix_list = [
        {
            "field_name": r.field_name,
            "doc_value": r.doc_value,
            "portal_value": r.portal_value,
            "match_type": r.match_type,
            "similarity_score": r.similarity_score
        }
        for r in verif_results
    ]

    # Fetch compliance checks
    comp_checks = db.query(ComplianceCheck).filter(ComplianceCheck.vendor_id == vendor_id).all()
    comp_list = [
        {
            "check_name": c.check_name,
            "status": c.status,
            "rule_description": c.rule_description,
            "failure_reason": c.failure_reason
        }
        for c in comp_checks
    ]

    # Fetch latest risk assessment
    latest_risk = db.query(RiskAssessment).filter(RiskAssessment.vendor_id == vendor_id).order_by(desc(RiskAssessment.assessed_at)).first()
    risk_dict = {}
    if latest_risk:
        factors = json.loads(latest_risk.factors_json) if latest_risk.factors_json else []
        explanations = json.loads(latest_risk.explanation_json) if latest_risk.explanation_json else []
        risk_dict = {
            "total_risk_score": latest_risk.total_risk_score,
            "risk_level": latest_risk.risk_level,
            "factors": factors,
            "explanation": explanations,
            "recommended_action": latest_risk.recommended_action
        }
    else:
        risk_dict = {
            "total_risk_score": vendor.risk_score,
            "risk_level": vendor.risk_level,
            "factors": [],
            "explanation": [],
            "recommended_action": vendor.recommended_action
        }

    vendor_dict = {
        "id": vendor.id,
        "name": vendor.name,
        "legal_name": vendor.legal_name,
        "gstin": vendor.gstin,
        "pan": vendor.pan,
        "cin": vendor.cin,
        "udyam_number": vendor.udyam_number,
        "address": vendor.address,
        "state": vendor.state,
        "pincode": vendor.pincode,
        "contact_email": vendor.contact_email,
        "contact_phone": vendor.contact_phone,
        "turnover_cr": vendor.turnover_cr,
        "employee_count": vendor.employee_count,
        "verification_status": vendor.verification_status,
        "compliance_score": vendor.compliance_score,
        "risk_score": vendor.risk_score,
        "match_score": vendor.match_score,
        "ocr_confidence": vendor.ocr_confidence,
        "anomaly_score": vendor.anomaly_score
    }

    report_id = f"REP-{vendor.id}-{uuid.uuid4().hex[:6].upper()}"
    pdf_path = generate_vendor_pdf_report(
        vendor=vendor_dict,
        verification_results=matrix_list,
        compliance_checks=comp_list,
        risk_assessment=risk_dict,
        report_id=report_id
    )

    file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0

    # Save record
    record = ReportRecord(
        vendor_id=vendor.id,
        report_id=report_id,
        report_path=pdf_path,
        file_size=file_size,
        generated_by=current_user.full_name if current_user else "Procurement Officer"
    )
    db.add(record)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "officer@bidverify.com",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        action="Verification Report Generated",
        details_json=json.dumps({"report_id": report_id, "file_name": os.path.basename(pdf_path)})
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Report generated successfully",
        "report_id": report_id,
        "file_name": os.path.basename(pdf_path),
        "file_size": file_size,
        "download_url": f"/api/vendors/{vendor_id}/report"
    }

@router.get("/vendors/{vendor_id}/report")
def download_vendor_report(vendor_id: int, db: Session = Depends(get_db)):
    record = db.query(ReportRecord).filter(ReportRecord.vendor_id == vendor_id).order_by(desc(ReportRecord.generated_at)).first()
    
    # If no report exists yet, generate on the fly
    if not record or not os.path.exists(record.report_path):
        res = generate_report(vendor_id=vendor_id, db=db, current_user=None)
        record = db.query(ReportRecord).filter(ReportRecord.vendor_id == vendor_id).order_by(desc(ReportRecord.generated_at)).first()

    if not record or not os.path.exists(record.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=record.report_path,
        filename=os.path.basename(record.report_path),
        media_type="application/pdf"
    )

@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(ReportRecord).order_by(desc(ReportRecord.generated_at)).all()
    results = []
    for r in reports:
        vendor = db.query(Vendor).filter(Vendor.id == r.vendor_id).first()
        results.append({
            "id": r.id,
            "report_id": r.report_id,
            "vendor_id": r.vendor_id,
            "vendor_name": vendor.name if vendor else "Unknown",
            "file_name": os.path.basename(r.report_path),
            "file_size": r.file_size,
            "generated_by": r.generated_by,
            "generated_at": r.generated_at,
            "risk_score": vendor.risk_score if vendor else 0.0,
            "compliance_score": vendor.compliance_score if vendor else 0.0
        })
    return results
