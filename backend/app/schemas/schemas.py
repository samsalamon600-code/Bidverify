import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "Procurement Officer"  # "Procurement Officer" or "Company / Vendor"
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: str
    role: str
    company_name: Optional[str] = None
    vendor_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    company_name: Optional[str] = None
    vendor_id: Optional[int] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    vendor_id: int
    doc_type: str
    file_name: str
    file_size: int
    mime_type: str
    status: str
    ocr_confidence: float
    uploaded_at: datetime.datetime
    extracted_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ExtractedDataResponse(BaseModel):
    id: int
    document_id: int
    vendor_id: int
    raw_text: Optional[str] = None
    structured_json: Optional[Dict[str, Any]] = None
    ocr_confidence: float
    extracted_at: datetime.datetime

    class Config:
        from_attributes = True

# Verification Schemas
class VerificationResultItem(BaseModel):
    id: int
    field_name: str
    doc_value: Optional[str] = None
    portal_value: Optional[str] = None
    match_type: str
    similarity_score: float
    source_portal: str

    class Config:
        from_attributes = True

class ComplianceCheckItem(BaseModel):
    id: int
    check_name: str
    status: str
    rule_description: Optional[str] = None
    failure_reason: Optional[str] = None
    weight: float

    class Config:
        from_attributes = True

class RiskAssessmentItem(BaseModel):
    total_risk_score: float
    risk_level: str
    factors: List[Dict[str, Any]]
    explanations: List[str]
    recommended_action: str

# Vendor Schemas
class VendorBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam_number: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    turnover_cr: Optional[float] = 1.0
    employee_count: Optional[int] = 10
    established_year: Optional[int] = 2020

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam_number: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    turnover_cr: Optional[float] = None
    employee_count: Optional[int] = None
    established_year: Optional[int] = None

class VendorListItem(BaseModel):
    id: int
    name: str
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    verification_status: str
    compliance_score: float
    risk_score: float
    risk_level: str
    match_score: float
    ocr_confidence: float
    anomaly_score: float
    last_verified: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class VendorDetailResponse(VendorListItem):
    cin: Optional[str] = None
    udyam_number: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    turnover_cr: float
    employee_count: int
    established_year: int
    anomaly_status: str
    recommended_action: str
    documents: List[DocumentResponse] = []
    verification_results: List[VerificationResultItem] = []
    compliance_checks: List[ComplianceCheckItem] = []
    risk_assessment: Optional[RiskAssessmentItem] = None

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    user_email: Optional[str] = None
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardKPI(BaseModel):
    total_vendors: int
    verified_vendors: int
    review_required_vendors: int
    high_risk_vendors: int
    avg_compliance_score: float
    avg_risk_score: float
    avg_verification_time_mins: float

class ChartDataPoint(BaseModel):
    label: str
    value: float
    category: Optional[str] = None

class DashboardResponse(BaseModel):
    kpis: DashboardKPI
    compliance_distribution: List[ChartDataPoint]
    risk_distribution: List[ChartDataPoint]
    verification_status: List[ChartDataPoint]
    monthly_trend: List[ChartDataPoint]
    risk_factors: List[ChartDataPoint]

# Settings Schemas
class WeightSettings(BaseModel):
    weight_identity_mismatch: float
    weight_document_issues: float
    weight_registration_issues: float
    weight_address_mismatch: float
    weight_ml_anomaly: float
    weight_missing_info: float

class WeightSettingsUpdate(BaseModel):
    weight_identity_mismatch: Optional[float] = None
    weight_document_issues: Optional[float] = None
    weight_registration_issues: Optional[float] = None
    weight_address_mismatch: Optional[float] = None
    weight_ml_anomaly: Optional[float] = None
    weight_missing_info: Optional[float] = None
