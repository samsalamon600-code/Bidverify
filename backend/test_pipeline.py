import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.normalization_service import (
    normalize_company_name, normalize_address, normalize_pan, normalize_gstin
)
from backend.app.services.extraction_service import extract_structured_fields
from backend.app.services.matching_service import cross_verify_all
from backend.app.services.compliance_service import evaluate_compliance
from backend.app.services.risk_service import calculate_risk_score
from backend.app.ml.anomaly_detector import anomaly_detector
from backend.app.services.report_service import generate_vendor_pdf_report
from backend.app.seed_data import seed_database
from backend.app.database import SessionLocal
from backend.app.models.models import Vendor

def test_backend_pipeline():
    print("==================================================")
    print("Testing Bidverify Backend Intelligence Pipeline")
    print("==================================================")

    # 1. Normalization
    print("\n[1] Testing Normalization...")
    n1 = normalize_company_name("ABC Technologies Private Limited")
    n2 = normalize_company_name("ABC Technologies Pvt. Ltd.")
    print(f"  Name 1 normalized: '{n1}'")
    print(f"  Name 2 normalized: '{n2}'")
    assert n1 == n2, "Company name normalization failed"
    print("  [PASS] Normalization test passed!")

    # 2. Field Extraction
    print("\n[2] Testing Field Extraction...")
    sample_text = """
    GOVERNMENT OF INDIA - CERTIFICATE OF REGISTRATION
    GSTIN: 36ABCDE1234F1Z5
    Legal Name: Alpha Logix Solutions Private Limited
    PAN: ABCDE1234F
    Principal Place of Business: Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081
    Date of Registration: 15/04/2020
    """
    fields = extract_structured_fields(sample_text)
    print(f"  Extracted GSTIN: {fields.get('gstin')}")
    print(f"  Extracted PAN: {fields.get('pan')}")
    print(f"  Extracted Name: {fields.get('company_name')}")
    print(f"  Extracted Pincode: {fields.get('pincode')}")
    assert fields.get("gstin") == "36ABCDE1234F1Z5"
    assert fields.get("pan") == "ABCDE1234F"
    print("  [PASS] Field extraction test passed!")

    # 3. Matching Engine
    print("\n[3] Testing Cross-Verification Matching Engine...")
    portal_data = {
        "legal_name": "Alpha Logix Solutions Private Limited",
        "gstin": "36ABCDE1234F1Z5",
        "pan": "ABCDE1234F",
        "address": "Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081",
        "status": "Active"
    }
    matrix = cross_verify_all(fields, portal_data)
    for m in matrix:
        print(f"  {m['field_name']}: {m['match_type']} ({m['similarity_score']}%)")
    assert len(matrix) >= 5
    print("  [PASS] Matching engine test passed!")

    # 4. Compliance Engine
    print("\n[4] Testing Deterministic Compliance Engine...")
    docs = [{"doc_type": "PAN"}, {"doc_type": "GST Certificate"}]
    comp = evaluate_compliance(fields, docs, matrix, portal_data)
    print(f"  Compliance Score: {comp['compliance_score']}/100")
    print(f"  Passed checks: {len(comp['passed_checks'])}")
    assert comp["compliance_score"] >= 85
    print("  [PASS] Compliance engine test passed!")

    # 5. ML Anomaly Detection (Isolation Forest)
    print("\n[5] Testing ML Anomaly Detector (Isolation Forest)...")
    meta = {"established_year": 2020, "employee_count": 85, "turnover_cr": 18.5}
    anomaly = anomaly_detector.evaluate_vendor(meta, len(docs), matrix)
    print(f"  Anomaly Score: {anomaly['anomaly_score']}")
    print(f"  Anomaly Status: {anomaly['anomaly_status']}")
    print(f"  Summary: {anomaly['summary_statement']}")
    assert 0.0 <= anomaly["anomaly_score"] <= 1.0
    print("  [PASS] ML Anomaly detector test passed!")

    # 6. Risk Scoring Engine
    print("\n[6] Testing Risk Scoring Engine...")
    risk = calculate_risk_score(fields, docs, matrix, portal_data, anomaly)
    print(f"  Risk Score: {risk['risk_score']}/100")
    print(f"  Risk Level: {risk['risk_level']}")
    print(f"  Action: {risk['recommended_action']}")
    assert risk["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    print("  [PASS] Risk scoring engine test passed!")

    # 7. ReportLab PDF Generation
    print("\n[7] Testing ReportLab PDF Generation...")
    pdf_path = generate_vendor_pdf_report(
        vendor={
            "id": 1,
            "name": "Alpha Logix Solutions Private Limited",
            "gstin": "36ABCDE1234F1Z5",
            "pan": "ABCDE1234F",
            "compliance_score": comp["compliance_score"],
            "risk_score": risk["risk_score"],
            "match_score": 98.0,
            "ocr_confidence": 97.0,
            "anomaly_score": anomaly["anomaly_score"],
            "verification_status": "Verified"
        },
        verification_results=matrix,
        compliance_checks=comp["checks"],
        risk_assessment=risk
    )
    print(f"  Generated PDF path: {pdf_path}")
    assert os.path.exists(pdf_path), "PDF was not created"
    assert os.path.getsize(pdf_path) > 1000, "PDF file is too small"
    print("  [PASS] PDF generation test passed!")

    # 8. Database Seeding
    print("\n[8] Testing Database Seeding...")
    seed_database()
    db = SessionLocal()
    vendor_count = db.query(Vendor).count()
    db.close()
    print(f"  Seeded Vendors in Database: {vendor_count}")
    assert vendor_count >= 5, "Database did not seed properly"
    print("  [PASS] Database seeding test passed!")

    print("\n==================================================")
    print("ALL BACKEND PIPELINE TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_backend_pipeline()
