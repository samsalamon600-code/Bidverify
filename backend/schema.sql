-- PostgreSQL Schema for AI-Powered Integrated Bid Compliance Verification Platform (SIH 26100)

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    role_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS officers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(150) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    ministry VARCHAR(150),
    phone VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    registration_number VARCHAR(100),
    gstin VARCHAR(25),
    pan VARCHAR(20),
    udyam_number VARCHAR(50),
    enterprise_type VARCHAR(50),
    incorporation_year INTEGER,
    local_content_percent FLOAT DEFAULT 0.0,
    address TEXT,
    contact_phone VARCHAR(30),
    is_msme BOOLEAN DEFAULT FALSE,
    is_startup BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tenders (
    id SERIAL PRIMARY KEY,
    tender_code VARCHAR(80) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(150) NOT NULL,
    description TEXT,
    publication_date VARCHAR(40),
    closing_date VARCHAR(40),
    category VARCHAR(100),
    estimated_value FLOAT DEFAULT 0.0,
    eligibility_requirements TEXT,
    technical_requirements TEXT,
    statutory_requirements TEXT,
    required_documents TEXT,
    local_content_requirements FLOAT DEFAULT 50.0,
    oem_requirements TEXT,
    other_requirements TEXT,
    tender_document_path VARCHAR(500),
    status VARCHAR(40) DEFAULT 'PUBLISHED',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tender_requirements (
    id SERIAL PRIMARY KEY,
    tender_id INTEGER NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    category VARCHAR(80) NOT NULL,
    parameter_name VARCHAR(150) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    required_value VARCHAR(255) NOT NULL,
    unit VARCHAR(50),
    is_mandatory BOOLEAN DEFAULT TRUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS bids (
    id SERIAL PRIMARY KEY,
    bid_number VARCHAR(80) UNIQUE NOT NULL,
    tender_id INTEGER NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    quoted_amount FLOAT NOT NULL,
    warranty_years FLOAT DEFAULT 1.0,
    delivery_days INTEGER DEFAULT 30,
    local_content_declared FLOAT DEFAULT 0.0,
    oem_status VARCHAR(80),
    product_name VARCHAR(200),
    product_model VARCHAR(150),
    technical_summary TEXT,
    declarations_accepted BOOLEAN DEFAULT TRUE,
    submission_status VARCHAR(50) DEFAULT 'SUBMITTED',
    verification_status VARCHAR(50) DEFAULT 'PENDING',
    officer_review_status VARCHAR(50) DEFAULT 'PENDING_REVIEW',
    officer_review_comments TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    overall_compliance_score FLOAT DEFAULT 0.0,
    document_compliance_score FLOAT DEFAULT 0.0,
    statutory_compliance_score FLOAT DEFAULT 0.0,
    technical_compliance_score FLOAT DEFAULT 0.0,
    tender_compliance_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR(30) DEFAULT 'UNASSESSED',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bid_items (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    item_category VARCHAR(80) NOT NULL,
    parameter_name VARCHAR(150) NOT NULL,
    submitted_value VARCHAR(255) NOT NULL,
    unit VARCHAR(50),
    source_document VARCHAR(200),
    source_page INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER REFERENCES bids(id) ON DELETE CASCADE,
    tender_id INTEGER REFERENCES tenders(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    safe_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(40) NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    file_path VARCHAR(500) NOT NULL,
    declared_doc_type VARCHAR(100),
    detected_doc_type VARCHAR(100),
    classification_confidence FLOAT DEFAULT 0.0,
    processing_status VARCHAR(50) DEFAULT 'UPLOADED',
    ocr_engine_used VARCHAR(80),
    page_count INTEGER DEFAULT 1,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_extractions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    raw_text TEXT,
    structured_data_json TEXT,
    entities_json TEXT,
    extraction_confidence FLOAT DEFAULT 0.0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id SERIAL PRIMARY KEY,
    check_code VARCHAR(80) UNIQUE NOT NULL,
    check_name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS compliance_results (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    check_code VARCHAR(80) NOT NULL,
    check_name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    requirement_text VARCHAR(500),
    submitted_text VARCHAR(500),
    status VARCHAR(40) NOT NULL,
    reason TEXT,
    integration_source VARCHAR(120),
    is_reviewed BOOLEAN DEFAULT FALSE,
    officer_comment TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_results (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    risk_level VARCHAR(30) NOT NULL,
    risk_score FLOAT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    is_anomaly_flagged BOOLEAN DEFAULT FALSE,
    risk_factors_json TEXT,
    ml_explanation TEXT,
    requires_human_review BOOLEAN DEFAULT TRUE,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    compliance_result_id INTEGER NOT NULL REFERENCES compliance_results(id) ON DELETE CASCADE,
    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    document_name VARCHAR(255),
    page_number INTEGER DEFAULT 1,
    extracted_snippet TEXT,
    field_name VARCHAR(120),
    expected_value VARCHAR(255),
    actual_value VARCHAR(255),
    explanation TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(150),
    user_role VARCHAR(50),
    action VARCHAR(120) NOT NULL,
    tender_id INTEGER,
    bid_id INTEGER,
    document_id INTEGER,
    result_status VARCHAR(80),
    review_comments TEXT,
    ip_address VARCHAR(60),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_code VARCHAR(80) UNIQUE NOT NULL,
    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    tender_id INTEGER NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    generated_by INTEGER REFERENCES users(id),
    file_path VARCHAR(500) NOT NULL,
    overall_score FLOAT,
    risk_level VARCHAR(30),
    review_status VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
