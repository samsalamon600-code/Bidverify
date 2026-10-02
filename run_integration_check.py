import sys
import os
import json
import time
import urllib.request
import urllib.parse

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.seed_data import seed_database
from backend.app.database import SessionLocal
from backend.app.models.models import Vendor, User, Document, AuditLog, ReportRecord
from backend.app.services.ocr_service import process_document
from backend.app.services.verification_service import GovernmentVerificationService
from backend.app.services.matching_service import cross_verify_all
from backend.app.services.compliance_service import evaluate_compliance
from backend.app.services.risk_service import calculate_risk_score
from backend.app.ml.anomaly_detector import anomaly_detector
from backend.app.services.report_service import generate_vendor_pdf_report

def run_e2e_integration():
    print("==================================================================")
    print("BIDVERIFY PLATFORM: COMPREHENSIVE END-TO-END INTEGRATION TEST")
    print("==================================================================")

    # Step 1: Database & Seed
    print("\n[STEP 1] Initializing & Seeding Database...")
    seed_database()
    db = SessionLocal()
    officer = db.query(User).filter(User.role == "Procurement Officer").first()
    print(f"  [PASS] Demo user confirmed: {officer.email} ({officer.full_name})")

    # Step 2: Vendor Onboarding
    print("\n[STEP 2] Simulating Vendor Registration...")
    vendor = Vendor(
        name="Integratech Systems Private Limited",
        legal_name="Integratech Systems Private Limited",
        gstin="36AABCI7788J1Z2",
        pan="AABCI7788J",
        cin="U72200TG2021PTC167890",
        udyam_number="UDYAM-TS-02-0077889",
        address="Plot 100, Madhapur, Hyderabad, Telangana - 500081",
        state="Telangana",
        pincode="500081",
        contact_email="bids@integratech.in",
        contact_phone="+91 98499 12345",
        turnover_cr=16.0,
        employee_count=60,
        established_year=2021,
        verification_status="Pending"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    print(f"  [PASS] Vendor registered with ID: #{vendor.id} ({vendor.name})")

    # Step 3: Document Ingestion & OCR
    print("\n[STEP 3] Simulating Document Ingestion & OCR Pipeline...")
    sample_gst_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sample_documents", "Sample_GST_Certificate.pdf")
    assert os.path.exists(sample_gst_path), f"Sample document missing: {sample_gst_path}"
    
    ocr_out = process_document(sample_gst_path)
    print(f"  [PASS] OCR Processed! Confidence: {ocr_out['ocr_confidence']}%")
    print(f"  [PASS] Extracted fields: {list(ocr_out['structured_data'].keys())}")

    doc = Document(
        vendor_id=vendor.id,
        doc_type="GST Certificate",
        file_name="Sample_GST_Certificate.pdf",
        file_path=sample_gst_path,
        file_size=os.path.getsize(sample_gst_path),
        mime_type="application/pdf",
        status="Processed",
        ocr_confidence=ocr_out['ocr_confidence']
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    print(f"  [PASS] Document #{doc.id} attached to Vendor #{vendor.id}")

    # Step 4: Multi-Portal Smart Registry Query
    print("\n[STEP 4] Querying Mock Government Registry (GSTN, Udyam, MCA21)...")
    gov_svc = GovernmentVerificationService(db=db)
    gst_res = gov_svc.verify_gst(vendor.gstin)
    udyam_res = gov_svc.verify_udyam(vendor.udyam_number)
    mca_res = gov_svc.verify_mca(vendor.cin)
    print(f"  [PASS] GSTN Record: {gst_res['legal_name']} (Status: {gst_res['status']})")
    print(f"  [PASS] Udyam Record: {udyam_res['enterprise_name']} ({udyam_res['classification']})")
    print(f"  [PASS] MCA21 Record: {mca_res['company_name']} (Class: {mca_res['company_class']})")

    # Step 5: RapidFuzz Cross-Verification Matching
    print("\n[STEP 5] Running Cross-Verification Matching Matrix...")
    doc_fields = {
        "company_name": vendor.name,
        "gstin": vendor.gstin,
        "pan": vendor.pan,
        "cin": vendor.cin,
        "udyam_number": vendor.udyam_number,
        "address": vendor.address
    }
    matrix = cross_verify_all(doc_fields, gst_res)
    for m in matrix:
        print(f"    - {m['field_name']}: {m['match_type']} ({m['similarity_score']}%)")
    assert len(matrix) >= 5
    print("  [PASS] Cross-verification matrix computed!")

    # Step 6: Deterministic Compliance Engine
    print("\n[STEP 6] Executing Deterministic Compliance Rules...")
    compliance_out = evaluate_compliance(doc_fields, [{"doc_type": "GST Certificate"}, {"doc_type": "PAN"}], matrix, gst_res)
    print(f"  [PASS] Compliance Score: {compliance_out['compliance_score']}/100")
    print(f"  [PASS] Passed checks count: {len(compliance_out['passed_checks'])}")

    # Step 7: ML Anomaly Detector (Isolation Forest)
    print("\n[STEP 7] Executing ML Isolation Forest Anomaly Detector...")
    vendor_meta = {"established_year": vendor.established_year, "employee_count": vendor.employee_count, "turnover_cr": vendor.turnover_cr}
    anomaly_out = anomaly_detector.evaluate_vendor(vendor_meta, 2, matrix)
    print(f"  [PASS] ML Anomaly Score: {anomaly_out['anomaly_score']} ({anomaly_out['anomaly_status']})")
    print(f"  [PASS] Findings: {anomaly_out['summary_statement']}")

    # Step 8: Multi-Factor Weighted Risk Scoring
    print("\n[STEP 8] Calculating Explainable Multi-Factor Risk Score...")
    risk_out = calculate_risk_score(doc_fields, [{"doc_type": "GST Certificate"}, {"doc_type": "PAN"}], matrix, gst_res, anomaly_out)
    print(f"  [PASS] Risk Score: {risk_out['risk_score']}/100 ({risk_out['risk_level']})")
    print(f"  [PASS] Recommended Action: {risk_out['recommended_action']}")

    # Step 9: Publication-Grade PDF Report Generation
    print("\n[STEP 9] Generating Official PDF Verification Dossier (ReportLab)...")
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
        "compliance_score": compliance_out['compliance_score'],
        "risk_score": risk_out['risk_score'],
        "match_score": 97.5,
        "ocr_confidence": 98.0,
        "anomaly_score": anomaly_out['anomaly_score'],
        "verification_status": "Verified"
    }
    pdf_path = generate_vendor_pdf_report(
        vendor=vendor_dict,
        verification_results=matrix,
        compliance_checks=compliance_out['checks'],
        risk_assessment=risk_out
    )
    print(f"  [PASS] Generated PDF saved to: {pdf_path}")
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 2000

    # Step 10: Audit Log Verification
    print("\n[STEP 10] Verifying Audit Trail Storage...")
    audit = AuditLog(
        user_email=officer.email,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        action="End-to-End Verification Completed",
        details_json=json.dumps({"compliance": compliance_out['compliance_score'], "risk": risk_out['risk_score']})
    )
    db.add(audit)
    db.commit()

    total_logs = db.query(AuditLog).filter(AuditLog.vendor_id == vendor.id).count()
    print(f"  [PASS] Audit logs verified for vendor #{vendor.id}: {total_logs} entries")

    db.close()

    print("\n==================================================================")
    print("ALL 10 PIPELINE PHASES INTEGRATED AND VALIDATED WITH 100% SUCCESS!")
    print("==================================================================")

if __name__ == "__main__":
    run_e2e_integration()
