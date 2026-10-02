import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.app.database import get_db
from backend.app.models.models import (
    Vendor, User, AuditLog, Document, VerificationResult, ComplianceCheck, RiskAssessment
)
from backend.app.schemas.schemas import (
    VendorCreate, VendorUpdate, VendorListItem, VendorDetailResponse,
    DocumentResponse, VerificationResultItem, ComplianceCheckItem, RiskAssessmentItem
)
from backend.app.utils.security import get_current_user

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.get("", response_model=List[VendorListItem])
def list_vendors(
    search: Optional[str] = Query(None, description="Search by name, GSTIN, PAN"),
    status: Optional[str] = Query(None, description="Filter by verification status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (LOW, MEDIUM, HIGH)"),
    sort_by: str = Query("created_at", description="Sort field: created_at, compliance_score, risk_score, name"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    query = db.query(Vendor)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Vendor.name.ilike(search_fmt)) |
            (Vendor.gstin.ilike(search_fmt)) |
            (Vendor.pan.ilike(search_fmt))
        )

    if status and status.lower() != "all":
        query = query.filter(Vendor.verification_status.ilike(status))

    if risk_level and risk_level.lower() != "all":
        query = query.filter(Vendor.risk_level == risk_level.upper())

    # Sorting
    sort_col = getattr(Vendor, sort_by, Vendor.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    return query.all()

@router.post("", response_model=VendorListItem, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: VendorCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    vendor = Vendor(
        name=vendor_in.name,
        legal_name=vendor_in.legal_name or vendor_in.name,
        gstin=vendor_in.gstin,
        pan=vendor_in.pan or (vendor_in.gstin[2:12] if vendor_in.gstin and len(vendor_in.gstin) >= 12 else None),
        cin=vendor_in.cin,
        udyam_number=vendor_in.udyam_number,
        address=vendor_in.address,
        state=vendor_in.state,
        pincode=vendor_in.pincode,
        contact_email=vendor_in.contact_email,
        contact_phone=vendor_in.contact_phone,
        turnover_cr=vendor_in.turnover_cr or 1.0,
        employee_count=vendor_in.employee_count or 10,
        established_year=vendor_in.established_year or 2020,
        verification_status="Pending"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    # Add audit log
    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "officer@bidverify.com",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        action="Vendor Onboarded",
        details_json=json.dumps({"vendor_name": vendor.name, "gstin": vendor.gstin})
    )
    db.add(audit)
    db.commit()

    return vendor

@router.get("/{id}", response_model=VendorDetailResponse)
def get_vendor(id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Serialize documents
    doc_responses = []
    for d in vendor.documents:
        extracted = None
        if d.extracted_data and d.extracted_data.structured_json:
            try:
                extracted = json.loads(d.extracted_data.structured_json)
            except Exception:
                extracted = {}
        doc_responses.append(DocumentResponse(
            id=d.id,
            vendor_id=d.vendor_id,
            doc_type=d.doc_type,
            file_name=d.file_name,
            file_size=d.file_size,
            mime_type=d.mime_type,
            status=d.status,
            ocr_confidence=d.ocr_confidence,
            uploaded_at=d.uploaded_at,
            extracted_data=extracted
        ))

    # Serialize verification results
    verif_responses = [
        VerificationResultItem(
            id=v.id,
            field_name=v.field_name,
            doc_value=v.doc_value,
            portal_value=v.portal_value,
            match_type=v.match_type,
            similarity_score=v.similarity_score,
            source_portal=v.source_portal
        )
        for v in vendor.verification_results
    ]

    # Serialize compliance checks
    comp_responses = [
        ComplianceCheckItem(
            id=c.id,
            check_name=c.check_name,
            status=c.status,
            rule_description=c.rule_description,
            failure_reason=c.failure_reason,
            weight=c.weight
        )
        for c in vendor.compliance_checks
    ]

    # Serialize risk assessment
    risk_item = None
    latest_risk = db.query(RiskAssessment).filter(RiskAssessment.vendor_id == id).order_by(desc(RiskAssessment.assessed_at)).first()
    if latest_risk:
        try:
            factors = json.loads(latest_risk.factors_json) if latest_risk.factors_json else []
            explanations = json.loads(latest_risk.explanation_json) if latest_risk.explanation_json else []
        except Exception:
            factors, explanations = [], []
        risk_item = RiskAssessmentItem(
            total_risk_score=latest_risk.total_risk_score,
            risk_level=latest_risk.risk_level,
            factors=factors,
            explanations=explanations,
            recommended_action=latest_risk.recommended_action or vendor.recommended_action
        )

    return VendorDetailResponse(
        id=vendor.id,
        name=vendor.name,
        legal_name=vendor.legal_name,
        gstin=vendor.gstin,
        pan=vendor.pan,
        cin=vendor.cin,
        udyam_number=vendor.udyam_number,
        address=vendor.address,
        state=vendor.state,
        pincode=vendor.pincode,
        contact_email=vendor.contact_email,
        contact_phone=vendor.contact_phone,
        turnover_cr=vendor.turnover_cr,
        employee_count=vendor.employee_count,
        established_year=vendor.established_year,
        verification_status=vendor.verification_status,
        compliance_score=vendor.compliance_score,
        risk_score=vendor.risk_score,
        risk_level=vendor.risk_level,
        match_score=vendor.match_score,
        ocr_confidence=vendor.ocr_confidence,
        anomaly_score=vendor.anomaly_score,
        anomaly_status=vendor.anomaly_status,
        recommended_action=vendor.recommended_action,
        last_verified=vendor.last_verified,
        created_at=vendor.created_at,
        documents=doc_responses,
        verification_results=verif_responses,
        compliance_checks=comp_responses,
        risk_assessment=risk_item
    )

@router.put("/{id}", response_model=VendorListItem)
def update_vendor(id: int, vendor_update: VendorUpdate, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    update_data = vendor_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vendor, key, value)

    db.commit()
    db.refresh(vendor)
    return vendor

@router.delete("/{id}")
def delete_vendor(id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    db.delete(vendor)
    db.commit()
    return {"message": "Vendor deleted successfully"}
