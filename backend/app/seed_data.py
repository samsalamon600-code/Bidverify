import os
import json
import datetime
from sqlalchemy.orm import Session
from backend.app.database import engine, SessionLocal, Base
from backend.app.models.models import (
    User, Vendor, Document, ExtractedData, VerificationResult,
    ComplianceCheck, RiskAssessment, AuditLog, MockGovRecord, ReportRecord
)
from backend.app.utils.security import get_password_hash
from backend.app.config import settings

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Users if not present
        if db.query(User).count() == 0:
            print("Seeding initial users...")
            demo_users = [
                User(
                    email="officer@bidverify.com",
                    hashed_password=get_password_hash("officer123"),
                    full_name="Rajesh Sharma",
                    role="Procurement Officer"
                ),
                User(
                    email="vendor@alphalogix.com",
                    hashed_password=get_password_hash("vendor123"),
                    full_name="Vikram Mehta",
                    role="Company / Vendor",
                    company_name="Alpha Logix Solutions Private Limited"
                ),
                User(
                    email="admin@bidverify.com",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Priya Varma",
                    role="Admin"
                )
            ]
            db.add_all(demo_users)
            db.commit()

        # 2. Seed Mock Government Registry if not present
        if db.query(MockGovRecord).count() == 0:
            print("Seeding Government Mock Registry (GSTN, Udyam, MCA21)...")
            mock_records = [
                MockGovRecord(
                    gstin="36ABCDE1234F1Z5",
                    pan="ABCDE1234F",
                    cin="U72200TG2020PTC145678",
                    udyam_number="UDYAM-TS-02-0012345",
                    legal_name="Alpha Logix Solutions Private Limited",
                    trade_name="Alpha Logix Tech",
                    status="Active",
                    address="Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081",
                    state="Telangana",
                    pincode="500081",
                    registration_date="2020-04-15"
                ),
                MockGovRecord(
                    gstin="27AABCA5678B1Z2",
                    pan="AABCA5678B",
                    cin="L45200MH2018PLC234567",
                    udyam_number="UDYAM-MH-01-0089123",
                    legal_name="Apex Infra Projects Limited",
                    trade_name="Apex Infrastructure",
                    status="Active",
                    address="Tower B, Level 14, Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra - 400051",
                    state="Maharashtra",
                    pincode="400051",
                    registration_date="2018-09-12"
                ),
                MockGovRecord(
                    gstin="29AAACZ9999C1Z3",
                    pan="AAACZ9999C",
                    cin=None,
                    udyam_number="UDYAM-KR-03-0045678",
                    legal_name="Zenith Global Supplies LLP",
                    trade_name="Zenith Supplies",
                    status="Active",
                    address="Brigade Towers, MG Road, Bengaluru, Karnataka - 560001",
                    state="Karnataka",
                    pincode="560001",
                    registration_date="2021-01-20"
                ),
                MockGovRecord(
                    gstin="07AABCN1111D1Z4",
                    pan="AABCN1111D",
                    cin="U32109DL2022PTC345678",
                    udyam_number="UDYAM-DL-05-0078901",
                    legal_name="NovaTech Electronics Solutions Private Limited",
                    trade_name="NovaTech Electronics",
                    status="Active",
                    address="Okhla Industrial Area Phase III, New Delhi - 110020",
                    state="Delhi",
                    pincode="110020",
                    registration_date="2022-06-10"
                ),
                MockGovRecord(
                    gstin="33AABCV2222E1Z8",
                    pan="AABCV2222E",
                    cin="U51909TN2023PTC456789",
                    udyam_number=None,
                    legal_name="Vanguard Trading Hub Private Limited",
                    trade_name="Vanguard Enterprises",
                    status="Active",
                    address="Mount Road, Anna Salai, Chennai, Tamil Nadu - 600002",
                    state="Tamil Nadu",
                    pincode="600002",
                    registration_date="2023-11-05"
                ),
                MockGovRecord(
                    gstin="06AABCM3333F1Z1",
                    pan="AABCM3333F",
                    cin="U60200HR2019PLC567890",
                    udyam_number="UDYAM-HR-04-0023456",
                    legal_name="Metro Logistics Corporation",
                    trade_name="Metro Freight",
                    status="Suspended",
                    address="DLF Cyber City, Sector 24, Gurugram, Haryana - 122002",
                    state="Haryana",
                    pincode="122002",
                    registration_date="2019-02-14"
                )
            ]
            db.add_all(mock_records)
            db.commit()

        # 3. Seed Vendors across the 5 distinct enterprise compliance scenarios
        if db.query(Vendor).count() == 0:
            print("Seeding demonstration vendors and verification dossiers...")
            
            # Scenario 1: Alpha Logix (Fully Verified)
            v1 = Vendor(
                name="Alpha Logix Solutions Private Limited",
                legal_name="Alpha Logix Solutions Private Limited",
                gstin="36ABCDE1234F1Z5",
                pan="ABCDE1234F",
                cin="U72200TG2020PTC145678",
                udyam_number="UDYAM-TS-02-0012345",
                address="Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081",
                state="Telangana",
                pincode="500081",
                contact_email="procurement@alphalogix.com",
                contact_phone="+91 98765 43210",
                turnover_cr=18.5,
                employee_count=85,
                established_year=2020,
                verification_status="Verified",
                compliance_score=96.0,
                risk_score=8.5,
                risk_level="LOW",
                match_score=98.5,
                ocr_confidence=97.0,
                anomaly_score=0.12,
                anomaly_status="LOW ANOMALY",
                recommended_action="Proceed to standard procurement review.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
            )
            db.add(v1)
            db.commit()
            db.refresh(v1)

            # Scenario 2: Apex Infra (Minor Address Mismatch)
            v2 = Vendor(
                name="Apex Infra Projects Limited",
                legal_name="Apex Infra Projects Limited",
                gstin="27AABCA5678B1Z2",
                pan="AABCA5678B",
                cin="L45200MH2018PLC234567",
                udyam_number="UDYAM-MH-01-0089123",
                address="Suite 1402, BKC Tower B, Bandra Kurla Complex, Mumbai, Maharashtra 400051", # Slightly altered format
                state="Maharashtra",
                pincode="400051",
                contact_email="bids@apexinfra.co.in",
                contact_phone="+91 98201 23456",
                turnover_cr=85.0,
                employee_count=320,
                established_year=2018,
                verification_status="Verified",
                compliance_score=88.5,
                risk_score=19.2,
                risk_level="LOW",
                match_score=91.0,
                ocr_confidence=95.5,
                anomaly_score=0.18,
                anomaly_status="LOW ANOMALY",
                recommended_action="Proceed to standard procurement review.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(days=1)
            )
            db.add(v2)
            db.commit()
            db.refresh(v2)

            # Scenario 3: Zenith Supplies (Missing Document / Partial)
            v3 = Vendor(
                name="Zenith Global Supplies LLP",
                legal_name="Zenith Global Supplies LLP",
                gstin="29AAACZ9999C1Z3",
                pan="AAACZ9999C",
                cin=None,
                udyam_number=None, # Missing Udyam certificate
                address="Brigade Towers, MG Road, Bengaluru, Karnataka - 560001",
                state="Karnataka",
                pincode="560001",
                contact_email="sales@zenithsupplies.in",
                contact_phone="+91 94480 11223",
                turnover_cr=6.5,
                employee_count=22,
                established_year=2021,
                verification_status="Requires Review",
                compliance_score=72.0,
                risk_score=38.5,
                risk_level="MEDIUM",
                match_score=86.0,
                ocr_confidence=91.0,
                anomaly_score=0.25,
                anomaly_status="LOW ANOMALY",
                recommended_action="Manual document verification recommended before contract award.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(days=2)
            )
            db.add(v3)
            db.commit()
            db.refresh(v3)

            # Scenario 4: NovaTech Electronics (Company Name Discrepancy)
            v4 = Vendor(
                name="NovaTech Electronics", # Shorter trade name vs legal name
                legal_name="NovaTech Electronics Solutions Private Limited",
                gstin="07AABCN1111D1Z4",
                pan="AABCN1111D",
                cin="U32109DL2022PTC345678",
                udyam_number="UDYAM-DL-05-0078901",
                address="Okhla Industrial Area Phase III, New Delhi - 110020",
                state="Delhi",
                pincode="110020",
                contact_email="contact@novatech-elec.com",
                contact_phone="+91 98111 88990",
                turnover_cr=12.0,
                employee_count=45,
                established_year=2022,
                verification_status="Partially Verified",
                compliance_score=68.0,
                risk_score=44.0,
                risk_level="MEDIUM",
                match_score=79.5,
                ocr_confidence=93.0,
                anomaly_score=0.38,
                anomaly_status="MEDIUM ANOMALY",
                recommended_action="Trade name vs legal name variation: Confirm Board resolution before tender.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(days=3)
            )
            db.add(v4)
            db.commit()
            db.refresh(v4)

            # Scenario 5: Vanguard Trading Hub (High ML Anomaly Pattern)
            v5 = Vendor(
                name="Vanguard Trading Hub Private Limited",
                legal_name="Vanguard Trading Hub Private Limited",
                gstin="33AABCV2222E1Z8",
                pan="AABCV2222E",
                cin="U51909TN2023PTC456789",
                udyam_number=None,
                address="Door No 9, Greams Road, Thousand Lights, Chennai, Tamil Nadu - 600006", # Different street from registry
                state="Tamil Nadu",
                pincode="600006",
                contact_email="admin@vanguardhub.net",
                contact_phone="+91 97900 44556",
                turnover_cr=92.0, # Claiming 92 Cr in under 1 year with 2 staff
                employee_count=2,
                established_year=2024,
                verification_status="Requires Review",
                compliance_score=52.0,
                risk_score=74.5,
                risk_level="HIGH",
                match_score=68.0,
                ocr_confidence=89.0,
                anomaly_score=0.84,
                anomaly_status="HIGH ANOMALY",
                recommended_action="High verification risk: Comprehensive physical audit and executive compliance review required.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(hours=6)
            )
            db.add(v5)
            db.commit()
            db.refresh(v5)

            # Scenario 6: Metro Logistics (Suspended GST)
            v6 = Vendor(
                name="Metro Logistics Corporation",
                legal_name="Metro Logistics Corporation",
                gstin="06AABCM3333F1Z1",
                pan="AABCM3333F",
                cin="U60200HR2019PLC567890",
                udyam_number="UDYAM-HR-04-0023456",
                address="DLF Cyber City, Sector 24, Gurugram, Haryana - 122002",
                state="Haryana",
                pincode="122002",
                contact_email="info@metrologistics.com",
                contact_phone="+91 99100 22334",
                turnover_cr=35.0,
                employee_count=110,
                established_year=2019,
                verification_status="Failed",
                compliance_score=36.0,
                risk_score=86.0,
                risk_level="HIGH",
                match_score=75.0,
                ocr_confidence=94.0,
                anomaly_score=0.45,
                anomaly_status="MEDIUM ANOMALY",
                recommended_action="Procurement on hold: Vendor GST registration is officially SUSPENDED.",
                last_verified=datetime.datetime.utcnow() - datetime.timedelta(days=4)
            )
            db.add(v6)
            db.commit()
            db.refresh(v6)

            # Add sample documents and verification records for Alpha Logix
            sample_docs = [
                Document(
                    vendor_id=v1.id,
                    doc_type="GST Certificate",
                    file_name="AlphaLogix_GST_Certificate.pdf",
                    file_path=os.path.join(settings.UPLOAD_DIR, "AlphaLogix_GST_Certificate.pdf"),
                    file_size=245000,
                    mime_type="application/pdf",
                    status="Processed",
                    ocr_confidence=98.0
                ),
                Document(
                    vendor_id=v1.id,
                    doc_type="PAN",
                    file_name="AlphaLogix_PAN_Card.png",
                    file_path=os.path.join(settings.UPLOAD_DIR, "AlphaLogix_PAN_Card.png"),
                    file_size=182000,
                    mime_type="image/png",
                    status="Processed",
                    ocr_confidence=96.0
                )
            ]
            db.add_all(sample_docs)
            db.commit()

            # Add verification results for Alpha Logix
            v1_matrix = [
                VerificationResult(vendor_id=v1.id, field_name="Company Name", doc_value=v1.name, portal_value=v1.legal_name, match_type="EXACT", similarity_score=100.0, source_portal="GSTN"),
                VerificationResult(vendor_id=v1.id, field_name="GSTIN", doc_value=v1.gstin, portal_value=v1.gstin, match_type="EXACT", similarity_score=100.0, source_portal="GSTN"),
                VerificationResult(vendor_id=v1.id, field_name="PAN", doc_value=v1.pan, portal_value=v1.pan, match_type="EXACT", similarity_score=100.0, source_portal="GSTN"),
                VerificationResult(vendor_id=v1.id, field_name="Address", doc_value=v1.address, portal_value=v1.address, match_type="EXACT", similarity_score=97.0, source_portal="GSTN"),
                VerificationResult(vendor_id=v1.id, field_name="Registration Status", doc_value="Active", portal_value="Active", match_type="EXACT", similarity_score=100.0, source_portal="GSTN")
            ]
            db.add_all(v1_matrix)

            # Add compliance checks for Alpha Logix
            v1_checks = [
                ComplianceCheck(vendor_id=v1.id, check_name="Mandatory Compliance Documents", status="PASS", rule_description="PAN and GST provided", weight=20.0),
                ComplianceCheck(vendor_id=v1.id, check_name="GSTN Registration Active Status", status="PASS", rule_description="GST is Active", weight=20.0),
                ComplianceCheck(vendor_id=v1.id, check_name="Tax Identification (PAN & GSTIN) Match", status="PASS", rule_description="Exact match", weight=20.0),
                ComplianceCheck(vendor_id=v1.id, check_name="Company Legal Name Consistency", status="PASS", rule_description=">=85% match", weight=15.0),
                ComplianceCheck(vendor_id=v1.id, check_name="Registered Address Match", status="PASS", rule_description="Address verified", weight=10.0),
                ComplianceCheck(vendor_id=v1.id, check_name="Profile Completeness & Document Validity", status="PASS", rule_description="Complete profile", weight=15.0)
            ]
            db.add_all(v1_checks)

            # Add audit logs
            logs = [
                AuditLog(user_email="officer@bidverify.com", vendor_id=v1.id, vendor_name=v1.name, action="Vendor Onboarded", details_json=json.dumps({"gstin": v1.gstin}), timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=3)),
                AuditLog(user_email="officer@bidverify.com", vendor_id=v1.id, vendor_name=v1.name, action="Documents Uploaded", details_json=json.dumps({"count": 2}), timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2, minutes=30)),
                AuditLog(user_email="system@bidverify.com", vendor_id=v1.id, vendor_name=v1.name, action="OCR Extraction Completed", details_json=json.dumps({"confidence": 97.0}), timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2, minutes=15)),
                AuditLog(user_email="system@bidverify.com", vendor_id=v1.id, vendor_name=v1.name, action="Vendor Verification Completed", details_json=json.dumps({"compliance": 96.0, "risk": 8.5}), timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2)),
                AuditLog(user_email="officer@bidverify.com", vendor_id=v5.id, vendor_name=v5.name, action="Vendor Verification Completed", details_json=json.dumps({"compliance": 52.0, "risk": 74.5, "anomaly": 0.84}), timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=6))
            ]
            db.add_all(logs)
            db.commit()

            print("Database successfully seeded with realistic multi-scenario test records!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
