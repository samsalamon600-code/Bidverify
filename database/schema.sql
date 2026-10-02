-- PostgreSQL Schema for Bidverify Platform
-- Generated for PostgreSQL 14+ / 15+

DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS risk_assessments CASCADE;
DROP TABLE IF EXISTS compliance_checks CASCADE;
DROP TABLE IF EXISTS verification_results CASCADE;
DROP TABLE IF EXISTS extracted_data CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS vendors CASCADE;
DROP TABLE IF EXISTS government_mock_records CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Procurement Officer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE government_mock_records (
    id SERIAL PRIMARY KEY,
    gstin VARCHAR(50) UNIQUE,
    pan VARCHAR(20),
    cin VARCHAR(50) UNIQUE,
    udyam_number VARCHAR(50) UNIQUE,
    legal_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Active',
    address TEXT,
    state VARCHAR(100),
    pincode VARCHAR(20),
    registration_date VARCHAR(50)
);

CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    gstin VARCHAR(50),
    pan VARCHAR(20),
    cin VARCHAR(50),
    udyam_number VARCHAR(50),
    address TEXT,
    state VARCHAR(100),
    pincode VARCHAR(20),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    turnover_cr DOUBLE PRECISION DEFAULT 1.0,
    employee_count INTEGER DEFAULT 10,
    established_year INTEGER DEFAULT 2020,
    verification_status VARCHAR(50) DEFAULT 'Pending',
    compliance_score DOUBLE PRECISION DEFAULT 0.0,
    risk_score DOUBLE PRECISION DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    match_score DOUBLE PRECISION DEFAULT 0.0,
    ocr_confidence DOUBLE PRECISION DEFAULT 0.0,
    anomaly_score DOUBLE PRECISION DEFAULT 0.0,
    anomaly_status VARCHAR(50) DEFAULT 'LOW ANOMALY',
    recommended_action VARCHAR(255) DEFAULT 'Verification Pending',
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    doc_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    status VARCHAR(50) DEFAULT 'Uploaded',
    ocr_confidence DOUBLE PRECISION DEFAULT 0.0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE extracted_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    raw_text TEXT,
    structured_json TEXT,
    ocr_confidence DOUBLE PRECISION DEFAULT 0.0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE verification_results (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    doc_value VARCHAR(500),
    portal_value VARCHAR(500),
    match_type VARCHAR(50) DEFAULT 'MISMATCH',
    similarity_score DOUBLE PRECISION DEFAULT 0.0,
    source_portal VARCHAR(100) DEFAULT 'GSTN',
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compliance_checks (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    check_name VARCHAR(200) NOT NULL,
    status VARCHAR(50) DEFAULT 'PASS',
    rule_description VARCHAR(500),
    failure_reason VARCHAR(500),
    weight DOUBLE PRECISION DEFAULT 1.0,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    total_risk_score DOUBLE PRECISION DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    factors_json TEXT,
    explanation_json TEXT,
    recommended_action VARCHAR(500),
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_email VARCHAR(255) DEFAULT 'system@bidverify.com',
    vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
    vendor_name VARCHAR(255),
    action VARCHAR(150) NOT NULL,
    details_json TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    report_id VARCHAR(100) UNIQUE NOT NULL,
    report_path VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    generated_by VARCHAR(255) DEFAULT 'Procurement Officer',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendors_gstin ON vendors(gstin);
CREATE INDEX idx_vendors_pan ON vendors(pan);
CREATE INDEX idx_audit_vendor ON audit_logs(vendor_id);
