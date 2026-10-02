import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="Procurement Officer")  # Procurement Officer, Company / Vendor, or Admin
    company_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    gstin = Column(String(50), nullable=True, index=True)
    pan = Column(String(20), nullable=True, index=True)
    cin = Column(String(50), nullable=True, index=True)
    udyam_number = Column(String(50), nullable=True, index=True)
    address = Column(Text, nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    turnover_cr = Column(Float, default=1.0)
    employee_count = Column(Integer, default=10)
    established_year = Column(Integer, default=2020)

    # Verification Outcomes
    verification_status = Column(String(50), default="Pending")  # Verified, Partially Verified, Requires Review, Failed, Pending
    compliance_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    match_score = Column(Float, default=0.0)
    ocr_confidence = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    anomaly_status = Column(String(50), default="LOW ANOMALY")  # LOW ANOMALY, MEDIUM ANOMALY, HIGH ANOMALY

    recommended_action = Column(String(255), default="Verification Pending")
    last_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="vendor", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="vendor", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="vendor", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="vendor", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="vendor", cascade="all, delete-orphan")
    reports = relationship("ReportRecord", back_populates="vendor", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    doc_type = Column(String(100), nullable=False)  # PAN, GST Certificate, Udyam Certificate, MCA/Company Registration, Address Proof, Bank Document, Other
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default="application/pdf")
    status = Column(String(50), default="Uploaded")  # Uploaded, Processed, Error
    ocr_confidence = Column(Float, default=0.0)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="documents")
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False, cascade="all, delete-orphan")

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    raw_text = Column(Text, nullable=True)
    structured_json = Column(Text, nullable=True)  # JSON-encoded dictionary
    ocr_confidence = Column(Float, default=0.0)
    extracted_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="extracted_data")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    field_name = Column(String(100), nullable=False)  # PAN, GSTIN, Company Name, Address, CIN, Udyam
    doc_value = Column(String(500), nullable=True)
    portal_value = Column(String(500), nullable=True)
    match_type = Column(String(50), default="MISMATCH")  # EXACT, PARTIAL, MISMATCH
    similarity_score = Column(Float, default=0.0)
    source_portal = Column(String(100), default="GSTN")  # GSTN, Udyam, MCA21
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="verification_results")

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    check_name = Column(String(200), nullable=False)
    status = Column(String(50), default="PASS")  # PASS, REVIEW, FAIL
    rule_description = Column(String(500), nullable=True)
    failure_reason = Column(String(500), nullable=True)
    weight = Column(Float, default=1.0)
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="compliance_checks")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    total_risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    factors_json = Column(Text, nullable=True)  # JSON list of factor dicts
    explanation_json = Column(Text, nullable=True)  # JSON list of explanations
    recommended_action = Column(String(500), nullable=True)
    assessed_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="risk_assessments")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), default="system@bidverify.com")
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    action = Column(String(150), nullable=False)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="audit_logs")

class MockGovRecord(Base):
    __tablename__ = "government_mock_records"

    id = Column(Integer, primary_key=True, index=True)
    gstin = Column(String(50), unique=True, index=True, nullable=True)
    pan = Column(String(20), index=True, nullable=True)
    cin = Column(String(50), unique=True, index=True, nullable=True)
    udyam_number = Column(String(50), unique=True, index=True, nullable=True)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    status = Column(String(50), default="Active")  # Active, Inactive, Suspended
    address = Column(Text, nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    registration_date = Column(String(50), nullable=True)

class ReportRecord(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    report_id = Column(String(100), unique=True, index=True, nullable=False)
    report_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    generated_by = Column(String(255), default="Procurement Officer")
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="reports")
