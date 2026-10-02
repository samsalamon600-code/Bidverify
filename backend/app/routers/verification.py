import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import (
    Vendor, Document, ExtractedData, VerificationResult,
    ComplianceCheck, RiskAssessment, AuditLog, User
)
from backend.app.services.verification_service import GovernmentVerificationService
from backend.app.services.matching_service import cross_verify_all
from backend.app.services.compliance_service import evaluate_compliance
from backend.app.services.risk_service import calculate_risk_score
from backend.app.ml.anomaly_detector import anomaly_detector
from backend.app.utils.security import get_current_user

router = APIRouter(tags=["Verification"])

# Government Mock Endpoints
@router.get("/verification/gst/{gstin}")
def query_gst_portal(gstin: str, db: Session = Depends(get_db)):
    svc = GovernmentVerificationService(db=db)
    return svc.verify_gst(gstin)

@router.get("/verification/udyam/{number}")
def query_udyam_portal(number: str, db: Session = Depends(get_db)):
    svc = GovernmentVerificationService(db=db)
    return svc.verify_udyam(number)

@router.get("/verification/mca/{cin}")
def query_mca_portal(cin: str, db: Session = Depends(get_db)):
    svc = GovernmentVerificationService(db=db)
    return svc.verify_mca(cin)

# Main Vendor Verification Workflow Trigger
@router.post("/vendors/{vendor_id}/verify")
def run_vendor_verification(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # 1. Gather document structured extractions
    docs = db.query(Document).filter(Document.vendor_id == vendor_id).all()
    doc_payloads = []
    combined_doc_data = {
        "company_name": vendor.legal_name or vendor.name,
        "gstin": vendor.gstin,
        "pan": vendor.pan,
        "cin": vendor.cin,
        "udyam_number": vendor.udyam_number,
        "address": vendor.address,
        "state": vendor.state,
        "pincode": vendor.pincode
    }

    conf_scores = []
    for d in docs:
        doc_payloads.append({
            "id": d.id,
            "doc_type": d.doc_type,
            "file_name": d.file_name,
            "ocr_confidence": d.ocr_confidence
        })
        if d.ocr_confidence > 0:
            conf_scores.append(d.ocr_confidence)

        if d.extracted_data and d.extracted_data.structured_json:
            try:
                data = json.loads(d.extracted_data.structured_json)
                for k, v in data.items():
                    if v and not combined_doc_data.get(k):
                        combined_doc_data[k] = v
            except Exception:
                pass

    avg_ocr_conf = round(sum(conf_scores) / len(conf_scores), 1) if conf_scores else 92.0

    # 2. Query Government Verification Service
    gov_service = GovernmentVerificationService(db=db)
    portal_data = {}
    if combined_doc_data.get("gstin"):
        portal_data = gov_service.verify_gst(combined_doc_data["gstin"])
    else:
        # Fallback to simulated record
        portal_data = {
            "legal_name": vendor.name,
            "status": "Active",
            "gstin": vendor.gstin or "",
            "pan": vendor.pan or "",
            "address": vendor.address or ""
        }

    # 3. Cross-Verification & Matching Matrix (RapidFuzz)
    matrix = cross_verify_all(combined_doc_data, portal_data)

    # Calculate overall match score
    sim_scores = [m["similarity_score"] for m in matrix if m["similarity_score"] > 0]
    avg_match_score = round(sum(sim_scores) / len(sim_scores), 1) if sim_scores else 0.0

    # 4. Compliance Engine (Deterministic Rules)
    vendor_dict = {
        "id": vendor.id,
        "name": vendor.name,
        "gstin": vendor.gstin,
        "pan": vendor.pan,
        "cin": vendor.cin,
        "udyam_number": vendor.udyam_number,
        "contact_email": vendor.contact_email,
        "contact_phone": vendor.contact_phone
    }
    compliance_out = evaluate_compliance(vendor_dict, doc_payloads, matrix, portal_data)

    # 5. Machine Learning Anomaly Detection (Isolation Forest)
    vendor_meta = {
        "established_year": vendor.established_year,
        "employee_count": vendor.employee_count,
        "turnover_cr": vendor.turnover_cr
    }
    anomaly_out = anomaly_detector.evaluate_vendor(vendor_meta, len(docs), matrix)

    # 6. Weighted Risk Engine
    risk_out = calculate_risk_score(vendor_dict, doc_payloads, matrix, portal_data, anomaly_out)

    # 7. Determine Final Verification Status
    comp_score = compliance_out["compliance_score"]
    risk_score = risk_out["risk_score"]
    
    if comp_score >= 85 and risk_score <= 30:
        verif_status = "Verified"
    elif risk_score >= 61 or comp_score < 50:
        verif_status = "Requires Review" if comp_score >= 50 else "Failed"
    elif comp_score >= 60 and risk_score <= 60:
        verif_status = "Partially Verified"
    else:
        verif_status = "Requires Review"

    # 8. Clear and rewrite verification matrix records in DB
    db.query(VerificationResult).filter(VerificationResult.vendor_id == vendor_id).delete()
    for m in matrix:
        db_res = VerificationResult(
            vendor_id=vendor_id,
            field_name=m["field_name"],
            doc_value=str(m["doc_value"]),
            portal_value=str(m["portal_value"]),
            match_type=m["match_type"],
            similarity_score=m["similarity_score"],
            source_portal="GSTN"
        )
        db.add(db_res)

    # Clear and rewrite compliance check records
    db.query(ComplianceCheck).filter(ComplianceCheck.vendor_id == vendor_id).delete()
    for c in compliance_out["checks"]:
        db_chk = ComplianceCheck(
            vendor_id=vendor_id,
            check_name=c["check_name"],
            status=c["status"],
            rule_description=c["rule_description"],
            failure_reason=c["failure_reason"],
            weight=c["weight"]
        )
        db.add(db_chk)

    # Create new Risk Assessment
    db_risk = RiskAssessment(
        vendor_id=vendor_id,
        total_risk_score=risk_score,
        risk_level=risk_out["risk_level"],
        factors_json=json.dumps(risk_out["factors"]),
        explanation_json=json.dumps(risk_out["explanation"]),
        recommended_action=risk_out["recommended_action"]
    )
    db.add(db_risk)

    # Update Vendor entity
    vendor.compliance_score = comp_score
    vendor.risk_score = risk_score
    vendor.risk_level = risk_out["risk_level"]
    vendor.match_score = avg_match_score
    vendor.ocr_confidence = avg_ocr_conf
    vendor.anomaly_score = anomaly_out["anomaly_score"]
    vendor.anomaly_status = anomaly_out["anomaly_status"]
    vendor.verification_status = verif_status
    vendor.recommended_action = risk_out["recommended_action"]
    vendor.last_verified = datetime.datetime.utcnow()

    # Create Audit Log entry
    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "officer@bidverify.com",
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        action="Vendor Verification Completed",
        details_json=json.dumps({
            "status": verif_status,
            "compliance_score": comp_score,
            "risk_score": risk_score,
            "anomaly_score": anomaly_out["anomaly_score"]
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(vendor)

    return {
        "vendor_id": vendor.id,
        "verification_status": verif_status,
        "scores": {
            "compliance_score": comp_score,
            "risk_score": risk_score,
            "match_score": avg_match_score,
            "ocr_confidence": avg_ocr_conf,
            "anomaly_score": anomaly_out["anomaly_score"]
        },
        "risk_level": risk_out["risk_level"],
        "anomaly_status": anomaly_out["anomaly_status"],
        "recommended_action": risk_out["recommended_action"],
        "matrix": matrix,
        "compliance": compliance_out,
        "risk": risk_out,
        "anomaly": anomaly_out,
        "portal_data": portal_data
    }
