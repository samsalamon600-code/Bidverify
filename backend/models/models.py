import json
from datetime import datetime, timezone
from backend.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    officer_profile = db.relationship("Officer", backref="user", uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship("Company", backref="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.officer_profile:
            data["officer"] = self.officer_profile.to_dict()
        if self.company_profile:
            data["company"] = self.company_profile.to_dict()
        return data


class Officer(db.Model):
    __tablename__ = "officers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    ministry = db.Column(db.String(150), default="Ministry of Commerce & Industry (GeM)")
    phone = db.Column(db.String(30))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "employee_id": self.employee_id,
            "department": self.department,
            "designation": self.designation,
            "ministry": self.ministry,
            "phone": self.phone,
        }


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100))
    gstin = db.Column(db.String(25))
    pan = db.Column(db.String(20))
    udyam_number = db.Column(db.String(50))
    enterprise_type = db.Column(db.String(50), default="Small Enterprise")
    incorporation_year = db.Column(db.Integer, default=2018)
    local_content_percent = db.Column(db.Float, default=60.0)
    address = db.Column(db.Text)
    contact_phone = db.Column(db.String(30))
    is_msme = db.Column(db.Boolean, default=True)
    is_startup = db.Column(db.Boolean, default=False)

    bids = db.relationship("Bid", backref="company", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_name": self.company_name,
            "registration_number": self.registration_number,
            "gstin": self.gstin,
            "pan": self.pan,
            "udyam_number": self.udyam_number,
            "enterprise_type": self.enterprise_type,
            "incorporation_year": self.incorporation_year,
            "local_content_percent": self.local_content_percent,
            "address": self.address,
            "contact_phone": self.contact_phone,
            "is_msme": self.is_msme,
            "is_startup": self.is_startup,
        }


class Tender(db.Model):
    __tablename__ = "tenders"
    id = db.Column(db.Integer, primary_key=True)
    tender_code = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    publication_date = db.Column(db.String(40))
    closing_date = db.Column(db.String(40))
    category = db.Column(db.String(100))
    estimated_value = db.Column(db.Float, default=0.0)
    eligibility_requirements = db.Column(db.Text)
    technical_requirements = db.Column(db.Text)
    statutory_requirements = db.Column(db.Text)
    required_documents = db.Column(db.Text)  # JSON or comma-separated list
    local_content_requirements = db.Column(db.Float, default=50.0)
    oem_requirements = db.Column(db.Text)
    other_requirements = db.Column(db.Text)
    tender_document_path = db.Column(db.String(500))
    status = db.Column(db.String(40), default="PUBLISHED")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=utc_now)

    requirements = db.relationship("TenderRequirement", backref="tender", lazy=True, cascade="all, delete-orphan")
    bids = db.relationship("Bid", backref="tender", lazy=True, cascade="all, delete-orphan")

    def get_required_docs_list(self):
        if not self.required_documents:
            return []
        try:
            parsed = json.loads(self.required_documents)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [d.strip() for d in self.required_documents.split(",") if d.strip()]

    def to_dict(self, include_requirements=True):
        data = {
            "id": self.id,
            "tender_code": self.tender_code,
            "title": self.title,
            "department": self.department,
            "description": self.description,
            "publication_date": self.publication_date,
            "closing_date": self.closing_date,
            "category": self.category,
            "estimated_value": self.estimated_value,
            "eligibility_requirements": self.eligibility_requirements,
            "technical_requirements": self.technical_requirements,
            "statutory_requirements": self.statutory_requirements,
            "required_documents": self.get_required_docs_list(),
            "local_content_requirements": self.local_content_requirements,
            "oem_requirements": self.oem_requirements,
            "other_requirements": self.other_requirements,
            "tender_document_path": self.tender_document_path,
            "status": self.status,
            "created_by": self.created_by,
            "bid_count": len(self.bids) if self.bids else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_requirements:
            data["structured_requirements"] = [r.to_dict() for r in self.requirements]
        return data


class TenderRequirement(db.Model):
    __tablename__ = "tender_requirements"
    id = db.Column(db.Integer, primary_key=True)
    tender_id = db.Column(db.Integer, db.ForeignKey("tenders.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)  # TECHNICAL, STATUTORY, ELIGIBILITY, LOCAL_CONTENT, DOCUMENT
    parameter_name = db.Column(db.String(150), nullable=False)
    operator = db.Column(db.String(20), nullable=False)  # >=, <=, ==, IN, PRESENT
    required_value = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(50), default="")
    is_mandatory = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "tender_id": self.tender_id,
            "category": self.category,
            "parameter_name": self.parameter_name,
            "operator": self.operator,
            "required_value": self.required_value,
            "unit": self.unit,
            "is_mandatory": self.is_mandatory,
            "description": self.description,
        }


class Bid(db.Model):
    __tablename__ = "bids"
    id = db.Column(db.Integer, primary_key=True)
    bid_number = db.Column(db.String(80), unique=True, nullable=False)
    tender_id = db.Column(db.Integer, db.ForeignKey("tenders.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    quoted_amount = db.Column(db.Float, nullable=False)
    warranty_years = db.Column(db.Float, default=3.0)
    delivery_days = db.Column(db.Integer, default=30)
    local_content_declared = db.Column(db.Float, default=55.0)
    oem_status = db.Column(db.String(80), default="Authorized OEM / Reseller")
    product_name = db.Column(db.String(200))
    product_model = db.Column(db.String(150))
    technical_summary = db.Column(db.Text)
    declarations_accepted = db.Column(db.Boolean, default=True)
    submission_status = db.Column(db.String(50), default="SUBMITTED")
    verification_status = db.Column(db.String(50), default="PENDING")  # PENDING, VERIFIED, NEEDS_REVIEW, REQUIRES_CLARIFICATION
    officer_review_status = db.Column(db.String(50), default="PENDING_REVIEW")  # PENDING_REVIEW, REVIEWED, REQUIRES_CLARIFICATION, VERIFIED
    officer_review_comments = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)
    overall_compliance_score = db.Column(db.Float, default=0.0)
    document_compliance_score = db.Column(db.Float, default=0.0)
    statutory_compliance_score = db.Column(db.Float, default=0.0)
    technical_compliance_score = db.Column(db.Float, default=0.0)
    tender_compliance_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(30), default="UNASSESSED")  # LOW, MEDIUM, HIGH, UNASSESSED
    submitted_at = db.Column(db.DateTime, default=utc_now)

    items = db.relationship("BidItem", backref="bid", lazy=True, cascade="all, delete-orphan")
    documents = db.relationship("Document", backref="bid", lazy=True, cascade="all, delete-orphan")
    compliance_results = db.relationship("ComplianceResult", backref="bid", lazy=True, cascade="all, delete-orphan")
    risk_results = db.relationship("RiskResult", backref="bid", lazy=True, cascade="all, delete-orphan")
    evidences = db.relationship("Evidence", backref="bid", lazy=True, cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="bid", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, detailed=False):
        data = {
            "id": self.id,
            "bid_number": self.bid_number,
            "tender_id": self.tender_id,
            "tender_code": self.tender.tender_code if self.tender else None,
            "tender_title": self.tender.title if self.tender else None,
            "tender_department": self.tender.department if self.tender else None,
            "company_id": self.company_id,
            "company_name": self.company.company_name if self.company else None,
            "company_gstin": self.company.gstin if self.company else None,
            "company_pan": self.company.pan if self.company else None,
            "company_udyam": self.company.udyam_number if self.company else None,
            "quoted_amount": self.quoted_amount,
            "warranty_years": self.warranty_years,
            "delivery_days": self.delivery_days,
            "local_content_declared": self.local_content_declared,
            "oem_status": self.oem_status,
            "product_name": self.product_name,
            "product_model": self.product_model,
            "technical_summary": self.technical_summary,
            "declarations_accepted": self.declarations_accepted,
            "submission_status": self.submission_status,
            "verification_status": self.verification_status,
            "officer_review_status": self.officer_review_status,
            "officer_review_comments": self.officer_review_comments,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "overall_compliance_score": round(self.overall_compliance_score or 0.0, 1),
            "document_compliance_score": round(self.document_compliance_score or 0.0, 1),
            "statutory_compliance_score": round(self.statutory_compliance_score or 0.0, 1),
            "technical_compliance_score": round(self.technical_compliance_score or 0.0, 1),
            "tender_compliance_score": round(self.tender_compliance_score or 0.0, 1),
            "risk_level": self.risk_level,
            "document_count": len(self.documents) if self.documents else 0,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }
        if detailed:
            data["company"] = self.company.to_dict() if self.company else None
            data["tender"] = self.tender.to_dict(include_requirements=True) if self.tender else None
            data["items"] = [i.to_dict() for i in self.items]
            data["documents"] = [d.to_dict(include_extraction=True) for d in self.documents]
            data["compliance_results"] = [c.to_dict() for c in self.compliance_results]
            data["risk_analysis"] = self.risk_results[-1].to_dict() if self.risk_results else None
            data["evidences"] = [e.to_dict() for e in self.evidences]
            data["reports"] = [r.to_dict() for r in self.reports]
        return data


class BidItem(db.Model):
    __tablename__ = "bid_items"
    id = db.Column(db.Integer, primary_key=True)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=False)
    item_category = db.Column(db.String(80), nullable=False)
    parameter_name = db.Column(db.String(150), nullable=False)
    submitted_value = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(50), default="")
    source_document = db.Column(db.String(200), default="Technical_Bid.pdf")
    source_page = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "bid_id": self.bid_id,
            "item_category": self.item_category,
            "parameter_name": self.parameter_name,
            "submitted_value": self.submitted_value,
            "unit": self.unit,
            "source_document": self.source_document,
            "source_page": self.source_page,
        }


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=True)
    tender_id = db.Column(db.Integer, db.ForeignKey("tenders.id"), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    safe_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(40), nullable=False)
    file_size_bytes = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(500), nullable=False)
    declared_doc_type = db.Column(db.String(100))
    detected_doc_type = db.Column(db.String(100))
    classification_confidence = db.Column(db.Float, default=0.0)
    processing_status = db.Column(db.String(50), default="UPLOADED")  # UPLOADED, PROCESSED, FAILED
    ocr_engine_used = db.Column(db.String(80), default="EasyOCR")
    ocr_confidence = db.Column(db.Float, default=0.0)
    page_count = db.Column(db.Integer, default=1)
    uploaded_at = db.Column(db.DateTime, default=utc_now)

    extractions = db.relationship("DocumentExtraction", backref="document", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_extraction=False):
        data = {
            "id": self.id,
            "bid_id": self.bid_id,
            "tender_id": self.tender_id,
            "original_filename": self.original_filename,
            "safe_filename": self.safe_filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "declared_doc_type": self.declared_doc_type,
            "detected_doc_type": self.detected_doc_type,
            "classification_confidence": round(self.classification_confidence or 0.0, 2),
            "processing_status": self.processing_status,
            "ocr_engine_used": self.ocr_engine_used,
            "ocr_confidence": round(self.ocr_confidence or 0.0, 2),
            "page_count": self.page_count,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
        if include_extraction and self.extractions:
            data["extraction"] = self.extractions[-1].to_dict()
        return data


class DocumentExtraction(db.Model):
    __tablename__ = "document_extractions"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    raw_text = db.Column(db.Text)
    structured_data_json = db.Column(db.Text)
    entities_json = db.Column(db.Text)
    extraction_confidence = db.Column(db.Float, default=0.92)
    ocr_details_json = db.Column(db.Text)
    extracted_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        structured = {}
        entities = []
        ocr_details = []
        try:
            if self.structured_data_json:
                structured = json.loads(self.structured_data_json)
        except Exception:
            pass
        try:
            if self.entities_json:
                entities = json.loads(self.entities_json)
        except Exception:
            pass
        try:
            if self.ocr_details_json:
                ocr_details = json.loads(self.ocr_details_json)
        except Exception:
            pass
        return {
            "id": self.id,
            "document_id": self.document_id,
            "raw_text": self.raw_text,
            "structured_data": structured,
            "entities": entities,
            "ocr_details": ocr_details,
            "extraction_confidence": round(self.extraction_confidence or 0.0, 2),
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }


class ComplianceCheck(db.Model):
    __tablename__ = "compliance_checks"
    id = db.Column(db.Integer, primary_key=True)
    check_code = db.Column(db.String(80), unique=True, nullable=False)
    check_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "check_code": self.check_code,
            "check_name": self.check_name,
            "category": self.category,
            "description": self.description,
            "is_active": self.is_active,
        }


class ComplianceResult(db.Model):
    __tablename__ = "compliance_results"
    id = db.Column(db.Integer, primary_key=True)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=False)
    check_code = db.Column(db.String(80), nullable=False)
    check_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)  # DOCUMENT, STATUTORY, TECHNICAL, TENDER, CONSISTENCY
    requirement_text = db.Column(db.String(500))
    submitted_text = db.Column(db.String(500))
    status = db.Column(db.String(40), nullable=False)  # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_APPLICABLE
    reason = db.Column(db.Text)
    integration_source = db.Column(db.String(120), default="Internal Compliance Engine")
    is_reviewed = db.Column(db.Boolean, default=False)
    officer_comment = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime, default=utc_now)

    evidence_items = db.relationship("Evidence", backref="compliance_result", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "bid_id": self.bid_id,
            "check_code": self.check_code,
            "check_name": self.check_name,
            "category": self.category,
            "requirement_text": self.requirement_text,
            "submitted_text": self.submitted_text,
            "status": self.status,
            "reason": self.reason,
            "integration_source": self.integration_source,
            "is_reviewed": self.is_reviewed,
            "officer_comment": self.officer_comment,
            "evidence": [e.to_dict() for e in self.evidence_items],
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }


class RiskResult(db.Model):
    __tablename__ = "risk_results"
    id = db.Column(db.Integer, primary_key=True)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=False)
    risk_level = db.Column(db.String(30), nullable=False)  # LOW, MEDIUM, HIGH
    risk_score = db.Column(db.Float, nullable=False)
    anomaly_score = db.Column(db.Float, nullable=False)
    is_anomaly_flagged = db.Column(db.Boolean, default=False)
    risk_factors_json = db.Column(db.Text)
    ml_explanation = db.Column(db.Text)
    requires_human_review = db.Column(db.Boolean, default=True)
    evaluated_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        factors = []
        try:
            if self.risk_factors_json:
                factors = json.loads(self.risk_factors_json)
        except Exception:
            pass
        return {
            "id": self.id,
            "bid_id": self.bid_id,
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score or 0.0, 2),
            "anomaly_score": round(self.anomaly_score or 0.0, 3),
            "is_anomaly_flagged": self.is_anomaly_flagged,
            "risk_factors": factors,
            "ml_explanation": self.ml_explanation,
            "requires_human_review": self.requires_human_review,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }


class Evidence(db.Model):
    __tablename__ = "evidence"
    id = db.Column(db.Integer, primary_key=True)
    compliance_result_id = db.Column(db.Integer, db.ForeignKey("compliance_results.id"), nullable=False)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    document_name = db.Column(db.String(255))
    page_number = db.Column(db.Integer, default=1)
    extracted_snippet = db.Column(db.Text)
    field_name = db.Column(db.String(120))
    expected_value = db.Column(db.String(255))
    actual_value = db.Column(db.String(255))
    explanation = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "compliance_result_id": self.compliance_result_id,
            "bid_id": self.bid_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "extracted_snippet": self.extracted_snippet,
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "explanation": self.explanation,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_name = db.Column(db.String(150))
    user_role = db.Column(db.String(50))
    action = db.Column(db.String(120), nullable=False)
    tender_id = db.Column(db.Integer, nullable=True)
    bid_id = db.Column(db.Integer, nullable=True)
    document_id = db.Column(db.Integer, nullable=True)
    result_status = db.Column(db.String(80))
    review_comments = db.Column(db.Text)
    ip_address = db.Column(db.String(60), default="127.0.0.1")
    timestamp = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_role": self.user_role,
            "action": self.action,
            "tender_id": self.tender_id,
            "bid_id": self.bid_id,
            "document_id": self.document_id,
            "result_status": self.result_status,
            "review_comments": self.review_comments,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    report_code = db.Column(db.String(80), unique=True, nullable=False)
    bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=False)
    tender_id = db.Column(db.Integer, db.ForeignKey("tenders.id"), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    file_path = db.Column(db.String(500), nullable=False)
    overall_score = db.Column(db.Float)
    risk_level = db.Column(db.String(30))
    review_status = db.Column(db.String(50))
    generated_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "report_code": self.report_code,
            "bid_id": self.bid_id,
            "tender_id": self.tender_id,
            "generated_by": self.generated_by,
            "file_path": self.file_path,
            "overall_score": round(self.overall_score or 0.0, 1),
            "risk_level": self.risk_level,
            "review_status": self.review_status,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    role = db.Column(db.String(50), nullable=True)  # "PROCUREMENT_OFFICER", "COMPANY", "ALL"
    tender_id = db.Column(db.Integer, nullable=True)
    tender_code = db.Column(db.String(80), nullable=True)
    bid_id = db.Column(db.Integer, nullable=True)
    bid_number = db.Column(db.String(80), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default="TENDER_BIDDED")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "tender_id": self.tender_id,
            "tender_code": self.tender_code,
            "bid_id": self.bid_id,
            "bid_number": self.bid_number,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

