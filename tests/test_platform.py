import io
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.app import create_app
from backend.extensions import db


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_gem.db"
    upload_dir = tmp_path / "uploads"
    reports_dir = tmp_path / "reports"
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "UPLOAD_FOLDER": str(upload_dir),
        "REPORTS_FOLDER": str(reports_dir),
    })

    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
        yield test_client


def _register_officer(client, email="officer1@gem.gov.in"):
    res = client.post(
        "/api/auth/register",
        json={
            "role": "PROCUREMENT_OFFICER",
            "full_name": "Test Officer IAS",
            "email": email,
            "password": "Pass@12",
            "employee_id": "GEM-OFF-9001",
            "department": "MeitY Procurement Cell",
            "designation": "Director",
        },
    )
    assert res.status_code == 201
    return res.get_json()["data"]["token"]


def _register_company(
    client,
    email="bidder1@apex.in",
    company_name="Apex Bharat Technologies Pvt. Ltd.",
    gstin="07AABCA1234C1Z5",
    pan="AABCA1234C",
    udyam="UDYAM-DL-01-0012345",
):
    res = client.post(
        "/api/auth/register",
        json={
            "role": "COMPANY",
            "full_name": "Bidder Rep",
            "email": email,
            "password": "Pass@12",
            "company_name": company_name,
            "gstin": gstin,
            "pan": pan,
            "udyam_number": udyam,
            "local_content_percent": 68.0,
        },
    )
    assert res.status_code == 201
    return res.get_json()["data"]["token"]


def _create_standard_tender(client, officer_token):
    res = client.post(
        "/api/tenders",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "tender_code": "GEM/2026/B/990001",
            "title": "Enterprise Workstations Tender",
            "department": "MeitY",
            "estimated_value": 10000000.0,
            "local_content_requirements": 50.0,
            "required_documents": [
                "Technical Bid",
                "GST Certificate",
                "PAN",
                "Udyam/MSME Certificate",
                "OEM Authorization",
            ],
            "structured_requirements": [
                {"category": "TECHNICAL", "parameter_name": "RAM", "operator": ">=", "required_value": "16", "unit": "GB"},
                {"category": "TECHNICAL", "parameter_name": "SSD", "operator": ">=", "required_value": "512", "unit": "GB"},
                {"category": "TECHNICAL", "parameter_name": "Warranty", "operator": ">=", "required_value": "3", "unit": "Years"},
            ],
        },
    )
    assert res.status_code == 201
    return res.get_json()["data"]["tender"]["id"]


def _upload_doc(client, token, bid_id, filename, content_bytes, declared_type=""):
    data = {
        "declared_doc_type": declared_type,
        "documents": (io.BytesIO(content_bytes), filename),
    }
    return client.post(
        f"/api/bids/{bid_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        content_type="multipart/form-data",
    )


# ==============================================================================
# TEST CASE 1: Fully Compliant Bid + Document Classification + Report + Audit Log
# ==============================================================================
def test_1_fully_compliant_bid_report_and_audit(client):
    off_token = _register_officer(client)
    comp_token = _register_company(client)
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={
            "quoted_amount": 9500000.0,
            "warranty_years": 3.0,
            "delivery_days": 30,
            "local_content_declared": 68.0,
            "oem_status": "Direct OEM Manufacturer",
            "product_name": "Apex Workstation",
            "ram_gb": 32,
            "ssd_gb": 1024,
        },
    )
    assert bid_res.status_code == 201
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # Upload all 5 mandatory documents including "Udyam Registration Certificate.pdf"
    docs_to_upload = [
        ("Technical_Bid.pdf", b"[Page 2]\nLocal Content Percentage: 68%\n[Page 4]\nRAM Capacity: 32 GB\nSSD Capacity: 1024 GB\nWarranty Period: 3 Years", "Technical Bid"),
        ("GST_Cert.pdf", b"FORM GST REG-06\nGSTIN: 07AABCA1234C1Z5\nLegal Name: Apex Bharat Technologies Pvt. Ltd.\nRegistration Status: ACTIVE", "GST Certificate"),
        ("PAN_Card.pdf", b"INCOME TAX DEPARTMENT\nPermanent Account Number: AABCA1234C\nName: Apex Bharat Technologies Pvt. Ltd.", "PAN"),
        ("Udyam Registration Certificate.pdf", b"UDYAM REGISTRATION CERTIFICATE\nUdyam Registration Number: UDYAM-DL-01-0012345\nName of Enterprise: Apex Bharat Technologies Pvt. Ltd.\nType of Enterprise: Small Enterprise", ""),
        ("OEM_MAF.pdf", b"MANUFACTURER'S AUTHORIZATION FORM\nOEM Authorization Status: Direct OEM Manufacturer", "OEM Authorization"),
    ]
    for fname, content, dtype in docs_to_upload:
        r = _upload_doc(client, comp_token, bid_id, fname, content, dtype)
        assert r.status_code == 201
        if fname == "Udyam Registration Certificate.pdf":
            detected = r.get_json()["data"]["documents"][0]["detected_doc_type"]
            assert detected == "Udyam/MSME Certificate"

    # Run Compliance Verification
    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert ver_res.status_code == 200
    v_data = ver_res.get_json()["data"]
    assert v_data["overall_compliance_score"] == 100.0
    assert v_data["risk_level"] == "LOW"

    # Officer Human Review
    rev_res = client.post(
        f"/api/bids/{bid_id}/review",
        headers={"Authorization": f"Bearer {off_token}"},
        json={"review_status": "VERIFIED", "review_comments": "All requirements satisfied."},
    )
    assert rev_res.status_code == 200

    # Generate PDF Report
    rpt_res = client.post(
        f"/api/bids/{bid_id}/report",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert rpt_res.status_code == 201
    rpt_id = rpt_res.get_json()["data"]["report"]["id"]

    # Download PDF Report
    dl_res = client.get(
        f"/api/reports/{rpt_id}?download=true",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert dl_res.status_code == 200
    assert dl_res.data.startswith(b"%PDF")

    # Verify Audit Trail
    aud_res = client.get(
        "/api/audit-logs",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert aud_res.status_code == 200
    assert aud_res.get_json()["data"]["total"] >= 5


# ==============================================================================
# TEST CASE 2: Missing Mandatory Document Detection
# ==============================================================================
def test_2_missing_document_detection(client):
    off_token = _register_officer(client, "off2@gem.gov.in")
    comp_token = _register_company(client, "comp2@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={"quoted_amount": 9500000.0, "ram_gb": 16, "ssd_gb": 512, "warranty_years": 3.0},
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # Upload only Technical Bid (omitting GST, PAN, Udyam, OEM)
    _upload_doc(client, comp_token, bid_id, "Technical_Bid.pdf", b"RAM Capacity: 16 GB\nSSD Capacity: 512 GB", "Technical Bid")

    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    v_data = ver_res.get_json()["data"]
    assert v_data["category_scores"]["document_compliance"] < 100.0
    missing_checks = [
        c for c in v_data["compliance_results"]
        if c["category"] == "DOCUMENT" and c["status"] == "NON_COMPLIANT"
    ]
    assert len(missing_checks) >= 3


# ==============================================================================
# TEST CASE 3: Wrong Technical Specification (SSD = 256 GB vs >= 512 GB)
# ==============================================================================
def test_3_wrong_technical_specification(client):
    off_token = _register_officer(client, "off3@gem.gov.in")
    comp_token = _register_company(client, "comp3@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={
            "quoted_amount": 9200000.0,
            "ram_gb": 16,
            "ssd_gb": 256,  # Below required 512 GB!
            "warranty_years": 3.0,
        },
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]
    _upload_doc(
        client,
        comp_token,
        bid_id,
        "Technical_Bid.pdf",
        b"[Page 4]\nRAM Capacity: 16 GB\nSSD Capacity: 256 GB\nWarranty Period: 3 Years",
        "Technical Bid",
    )

    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    v_data = ver_res.get_json()["data"]
    ssd_check = next(c for c in v_data["compliance_results"] if "SSD" in c["check_name"])
    assert ssd_check["status"] == "NON_COMPLIANT"
    assert "below the required minimum" in ssd_check["reason"]
    assert ssd_check["evidence"][0]["page_number"] == 4


# ==============================================================================
# TEST CASE 4: Conflicting / Inconsistent Information Detection
# ==============================================================================
def test_4_conflicting_information_detection(client):
    off_token = _register_officer(client, "off4@gem.gov.in")
    comp_token = _register_company(client, "comp4@apex.in", gstin="07AABCA1234C1Z5")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={
            "quoted_amount": 9400000.0,
            "local_content_declared": 70.0,  # Form says 70%
            "ram_gb": 16,
            "ssd_gb": 512,
        },
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # Document has conflicting GSTIN (29AADCS9012E1Z8 vs profile 07AABCA1234C1Z5) and conflicting Local Content (40% vs 70%)
    _upload_doc(client, comp_token, bid_id, "GST_Cert.pdf", b"FORM GST REG-06\nGSTIN: 29AADCS9012E1Z8\nStatus: ACTIVE", "GST Certificate")
    _upload_doc(client, comp_token, bid_id, "Technical_Bid.pdf", b"[Page 2]\nLocal Content Percentage: 40%\n[Page 4]\nRAM Capacity: 16 GB\nSSD Capacity: 512 GB", "Technical Bid")

    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    v_data = ver_res.get_json()["data"]
    codes = {c["check_code"]: c for c in v_data["compliance_results"]}
    assert "CONSISTENCY_GSTIN" in codes
    assert codes["CONSISTENCY_GSTIN"]["status"] == "NEEDS_REVIEW"
    assert "TENDER_LC_INCONSISTENCY" in codes
    assert codes["TENDER_LC_INCONSISTENCY"]["status"] == "NEEDS_REVIEW"


# ==============================================================================
# TEST CASE 5: OCR Failure Handling on Corrupted / Unreadable File
# ==============================================================================
def test_5_ocr_failure_handling(client):
    off_token = _register_officer(client, "off5@gem.gov.in")
    comp_token = _register_company(client, "comp5@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={"quoted_amount": 9000000.0},
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # Upload a .png file with non-image garbage bytes so OpenCV imread fails
    up_res = _upload_doc(client, comp_token, bid_id, "corrupted_scan.png", b"NOT_A_VALID_PNG_BINARY_STREAM", "GST Certificate")
    doc_id = up_res.get_json()["data"]["documents"][0]["id"]

    proc_res = client.post(
        f"/api/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert proc_res.status_code == 422
    assert proc_res.get_json()["success"] is False


# ==============================================================================
# TEST CASE 6: Unusual / Anomalous Value (Warranty = 30 years -> Isolation Forest)
# ==============================================================================
def test_6_anomalous_value_isolation_forest(client):
    off_token = _register_officer(client, "off6@gem.gov.in")
    comp_token = _register_company(client, "comp6@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={
            "quoted_amount": 9500000.0,
            "warranty_years": 30.0,  # Unusual 30-year warranty!
            "delivery_days": 30,
            "local_content_declared": 65.0,
            "ram_gb": 16,
            "ssd_gb": 512,
        },
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    v_data = ver_res.get_json()["data"]
    risk_info = v_data["risk_analysis"]
    assert risk_info["is_anomaly_flagged"] is True
    assert "Potential Anomaly" in risk_info["ml_explanation"]
    assert "Human Review Required" in risk_info["ml_explanation"]


# ==============================================================================
# TEST CASE 7: Unauthorized User & Role-Based Access Control (RBAC)
# ==============================================================================
def test_7_unauthorized_user_and_rbac(client):
    off_token = _register_officer(client, "off7@gem.gov.in")
    comp_token = _register_company(client, "comp7@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    # Unauthenticated request rejected with 401
    unauth = client.get("/api/bids")
    assert unauth.status_code == 401

    # Company trying to create a tender (Officer-only) -> 403
    comp_create_tender = client.post(
        "/api/tenders",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={"title": "Unauthorized Tender", "department": "Dept"},
    )
    assert comp_create_tender.status_code == 403
    assert comp_create_tender.get_json()["error_code"] == "UNAUTHORIZED_ROLE"

    # Officer trying to submit a bid (Company-only) -> 403
    off_submit_bid = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {off_token}"},
        json={"quoted_amount": 5000000.0},
    )
    assert off_submit_bid.status_code == 403


# ==============================================================================
# TEST CASE 8: Invalid File Upload (Invalid Extension, Empty File, Duplicate Name)
# ==============================================================================
def test_8_invalid_file_upload_validation(client):
    off_token = _register_officer(client, "off8@gem.gov.in")
    comp_token = _register_company(client, "comp8@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={"quoted_amount": 9100000.0},
    )
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # 8a. Disallowed file extension (.exe)
    bad_ext = _upload_doc(client, comp_token, bid_id, "malware.exe", b"MZ12345", "Technical Bid")
    assert bad_ext.status_code == 400
    assert bad_ext.get_json()["error_code"] == "INVALID_FILE_TYPE"

    # 8b. Empty 0-byte file
    empty_res = _upload_doc(client, comp_token, bid_id, "empty_doc.pdf", b"", "GST Certificate")
    assert empty_res.status_code == 400
    assert empty_res.get_json()["error_code"] == "EMPTY_FILE"

    # 8c. Duplicate filename within same bid
    ok_res = _upload_doc(client, comp_token, bid_id, "GST_Certificate.pdf", b"Valid GST Text 07AABCA1234C1Z5", "GST Certificate")
    assert ok_res.status_code == 201
    dup_res = _upload_doc(client, comp_token, bid_id, "GST_Certificate.pdf", b"Valid GST Text 07AABCA1234C1Z5", "GST Certificate")
    assert dup_res.status_code == 400
    assert dup_res.get_json()["error_code"] == "DUPLICATE_FILENAME"


# ==============================================================================
# TEST CASE 9: Tender Delete & Requirement Bidded Notification to Both Parties
# ==============================================================================
def test_9_tender_delete_and_notify_bidded(client):
    off_token = _register_officer(client, "off9@gem.gov.in")
    comp_token = _register_company(client, "comp9@apex.in")
    tender_id = _create_standard_tender(client, off_token)

    # 9a. Initially not bidded
    t_res_before = client.get("/api/tenders", headers={"Authorization": f"Bearer {comp_token}"})
    assert t_res_before.status_code == 200
    tenders_before = t_res_before.get_json()["data"]["tenders"]
    target_before = next(t for t in tenders_before if t["id"] == tender_id)
    assert target_before["has_bidded"] is False
    assert target_before["is_bidded"] is False

    # 9b. Submit a bid
    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={"quoted_amount": 9200000.0},
    )
    assert bid_res.status_code == 201

    # 9c. Now tender has_bidded is True for company and is_bidded is True
    t_res_after = client.get("/api/tenders", headers={"Authorization": f"Bearer {comp_token}"})
    tenders_after = t_res_after.get_json()["data"]["tenders"]
    target_after = next(t for t in tenders_after if t["id"] == tender_id)
    assert target_after["has_bidded"] is True
    assert target_after["is_bidded"] is True
    assert target_after["existing_bid_id"] is not None

    # 9d. Officer sends "Notify Bidded" notice to both officer and bidders
    notify_res = client.post(
        f"/api/tenders/{tender_id}/notify-bidded",
        headers={"Authorization": f"Bearer {off_token}"},
        json={"custom_message": "Notice: Tender requirement GEM/2026/B/TEST is locked in active review."},
    )
    assert notify_res.status_code == 200
    assert "Notification broadcast sent" in notify_res.get_json()["message"]

    # 9e. Verify Officer received notifications
    off_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {off_token}"})
    assert off_notifs.status_code == 200
    assert len(off_notifs.get_json()["data"]["notifications"]) > 0

    # 9f. Verify Company received notifications
    comp_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {comp_token}"})
    assert comp_notifs.status_code == 200
    assert len(comp_notifs.get_json()["data"]["notifications"]) > 0

    # 9g. Officer permanently deletes tender
    del_res = client.delete(f"/api/tenders/{tender_id}", headers={"Authorization": f"Bearer {off_token}"})
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.get_json()["message"]

    # 9h. Tender is no longer in list
    t_res_final = client.get("/api/tenders")
    assert not any(t["id"] == tender_id for t in t_res_final.get_json()["data"]["tenders"])


def test_10_password_policy_validation(client):
    """
    Verifies the password policy:
    1. >= 4 characters
    2. At least 1 symbol
    3. <= 8 characters
    Only compliant passwords allow account creation.
    """
    base_payload = {
        "role": "COMPANY",
        "full_name": "Test User",
        "email": "pw_test@company.in",
        "company_name": "Test Co",
    }

    # 1. Too short (< 4 chars) -> rejected
    r1 = client.post("/api/auth/register", json={**base_payload, "password": "a@1"})
    assert r1.status_code == 400
    assert "at least 4 characters" in r1.get_json()["message"]

    # 2. Too long (> 8 chars) -> rejected
    r2 = client.post("/api/auth/register", json={**base_payload, "password": "LongPass@123"})
    assert r2.status_code == 400
    assert "not exceed 8 characters" in r2.get_json()["message"]

    # 3. Missing symbol (no symbol) -> rejected
    r3 = client.post("/api/auth/register", json={**base_payload, "password": "Pass1234"})
    assert r3.status_code == 400
    assert "at least 1 symbol" in r3.get_json()["message"]

    # 4. Compliant password (4 chars with symbol, e.g. "a@12") -> approved
    r4 = client.post("/api/auth/register", json={**base_payload, "email": "valid1@company.in", "password": "a@12"})
    assert r4.status_code == 201

    # 5. Compliant password (8 chars with symbol, e.g. "Pass@123") -> approved
    r5 = client.post("/api/auth/register", json={**base_payload, "email": "valid2@company.in", "password": "Pass@123"})
    assert r5.status_code == 201


def test_11_line_by_line_document_upload_on_bid_apply(client):
    """
    Verifies line-by-line document upload matching procurement officer's required documents list
    during bid application via multipart/form-data.
    """
    off_token = _register_officer(client)
    comp_token = _register_company(client)
    tender_id = _create_standard_tender(client, off_token)

    data = {
        "quoted_amount": "8800000.0",
        "product_name": "Apex Server Node",
        "product_model": "APX-9000",
        "ram_gb": "32",
        "ssd_gb": "1024",
        "warranty_years": "3",
        "delivery_days": "25",
        "local_content_declared": "65",
        "documents": [
            (io.BytesIO(b"TECHNICAL SPECIFICATIONS\nRAM: 32 GB\nSSD: 1024 GB\nWarranty: 3 Years"), "Tech_Proposal.pdf"),
            (io.BytesIO(b"FORM GST REG-06\nGSTIN: 07AABCA1234C1Z5\nLegal Name: Apex Bharat"), "GST_Certificate.pdf"),
            (io.BytesIO(b"INCOME TAX DEPARTMENT\nPermanent Account Number: AABCA1234C"), "PAN_Card.pdf"),
        ],
        "declared_doc_types": [
            "Technical Bid",
            "GST Certificate",
            "PAN",
        ],
    }

    res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        data=data,
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    bid_data = res.get_json()["data"]["bid"]
    bid_id = bid_data["id"]

    # Verify documents were associated line-by-line with exact declared document types
    bid_details = client.get(
        f"/api/bids/{bid_id}",
        headers={"Authorization": f"Bearer {comp_token}"},
    ).get_json()["data"]["bid"]

    docs = bid_details["documents"]
    assert len(docs) == 3

    doc_map = {d["original_filename"]: d["declared_doc_type"] for d in docs}
    assert doc_map["Tech_Proposal.pdf"] == "Technical Bid"
    assert doc_map["GST_Certificate.pdf"] == "GST Certificate"
    assert doc_map["PAN_Card.pdf"] == "PAN"

    # Verify OCR and NLP pipeline processed documents
    for d in docs:
        assert d["ocr_engine_used"] in ("EasyOCR", "Document Stream (Direct Text)")
        assert d["processing_status"] in ("PROCESSED", "COMPLETED")


def test_12_dynamic_solar_tender_thresholds_bid_and_compliance(client):
    """
    Verifies dynamic non-IT tender thresholds (e.g. Solar Panels) where parameters,
    operators, and thresholds differ completely from computer workstations.
    Ensures bidder can offer tailored specifications that are validated against the tender's thresholds.
    """
    off_token = _register_officer(client)
    comp_token = _register_company(client)

    # 1. Officer publishes Solar Panel Tender with specific thresholds
    t_res = client.post(
        "/api/tenders",
        headers={"Authorization": f"Bearer {off_token}"},
        json={
            "tender_code": f"THA/2026/{uuid.uuid4().hex[:7].upper()}",
            "title": "Procurement of solar panels with 5 years warranty",
            "department": "Ministry of Electronics & Information Technology (MeitY)",
            "estimated_value": 15000000.0,
            "local_content_requirements": 50.0,
            "required_documents": [
                "Technical Bid",
                "GST Certificate",
                "PAN",
                "Udyam/MSME Certificate",
            ],
            "technical_specifications": [
                {"category": "TECHNICAL", "parameter_name": "Solar Module Capacity", "operator": ">=", "required_value": "540", "unit": "Wp", "is_mandatory": True},
                {"category": "TECHNICAL", "parameter_name": "Module Efficiency", "operator": ">=", "required_value": "21", "unit": "%", "is_mandatory": True},
                {"category": "TECHNICAL", "parameter_name": "Inverter Efficiency", "operator": ">=", "required_value": "98", "unit": "%", "is_mandatory": True},
                {"category": "TECHNICAL", "parameter_name": "Warranty on Module Output (90%)", "operator": ">=", "required_value": "10", "unit": "Years", "is_mandatory": True},
                {"category": "TECHNICAL", "parameter_name": "Linear Degradation Warranty (80%)", "operator": ">=", "required_value": "25", "unit": "Years", "is_mandatory": True},
                {"category": "STATUTORY", "parameter_name": "ALMM Listed Manufacturer", "operator": "==", "required_value": "Yes", "unit": "", "is_mandatory": True},
                {"category": "STATUTORY", "parameter_name": "IEC 61215 / BIS IS 14286", "operator": "==", "required_value": "Yes", "unit": "", "is_mandatory": True},
            ],
        },
    )
    assert t_res.status_code == 201
    tender_id = t_res.get_json()["data"]["tender"]["id"]

    # 2. Company bids with dynamic technical specifications matching solar thresholds
    bid_res = client.post(
        f"/api/tenders/{tender_id}/bids",
        headers={"Authorization": f"Bearer {comp_token}"},
        json={
            "quoted_amount": 14250000.0,
            "product_name": "High-Efficiency Bifacial Solar PV Modules & Inverter System",
            "product_model": "SPV-540-G5",
            "delivery_days": 28,
            "local_content_declared": 65.0,
            "oem_status": "Direct OEM Manufacturer",
            "technical_summary": "540 Wp Monocrystalline Solar PV Modules, 21% Module Efficiency, 98% Inverter Efficiency, 10 Years Output Warranty.",
            "technical_specifications": [
                {"parameter_name": "Solar Module Capacity", "submitted_value": "540", "unit": "Wp", "item_category": "TECHNICAL"},
                {"parameter_name": "Module Efficiency", "submitted_value": "21.2", "unit": "%", "item_category": "TECHNICAL"},
                {"parameter_name": "Inverter Efficiency", "submitted_value": "98.5", "unit": "%", "item_category": "TECHNICAL"},
                {"parameter_name": "Warranty on Module Output (90%)", "submitted_value": "10", "unit": "Years", "item_category": "TECHNICAL"},
                {"parameter_name": "Linear Degradation Warranty (80%)", "submitted_value": "25", "unit": "Years", "item_category": "TECHNICAL"},
                {"parameter_name": "ALMM Listed Manufacturer", "submitted_value": "Yes", "unit": "", "item_category": "STATUTORY"},
                {"parameter_name": "IEC 61215 / BIS IS 14286", "submitted_value": "Yes", "unit": "", "item_category": "STATUTORY"},
            ],
        },
    )
    assert bid_res.status_code == 201
    bid_id = bid_res.get_json()["data"]["bid"]["id"]

    # 3. Upload statutory & technical documents
    docs = [
        ("Technical_Bid.pdf", b"TECHNICAL SPECIFICATIONS\nSolar Module Capacity: 540 Wp\nModule Efficiency: 21.2%\nInverter Efficiency: 98.5%\nLocal Content: 65%", "Technical Bid"),
        ("GST_Cert.pdf", b"FORM GST REG-06\nGSTIN: 07AABCA1234C1Z5\nLegal Name: Apex Bharat", "GST Certificate"),
        ("PAN_Card.pdf", b"INCOME TAX DEPARTMENT\nPermanent Account Number: AABCA1234C", "PAN"),
        ("Udyam_Cert.pdf", b"UDYAM REGISTRATION CERTIFICATE\nUdyam Registration Number: UDYAM-DL-01-0012345", "Udyam/MSME Certificate"),
    ]
    for fn, content, dtype in docs:
        r = _upload_doc(client, comp_token, bid_id, fn, content, dtype)
        assert r.status_code == 201

    # 4. Officer runs verification
    ver_res = client.post(
        f"/api/bids/{bid_id}/verify",
        headers={"Authorization": f"Bearer {off_token}"},
    )
    assert ver_res.status_code == 200
    report = ver_res.get_json()["data"]

    # 5. Check technical compliance: all 7 solar requirements evaluated and compliant
    res_list = report["compliance_results"]
    solar_cap_check = next((c for c in res_list if "Solar Module Capacity" in c["check_name"]), None)
    assert solar_cap_check is not None
    assert solar_cap_check["status"] == "COMPLIANT"
    assert "540" in solar_cap_check["submitted_text"]

    mod_eff_check = next((c for c in res_list if "Module Efficiency" in c["check_name"]), None)
    assert mod_eff_check is not None
    assert mod_eff_check["status"] == "COMPLIANT"
    assert "21.2" in mod_eff_check["submitted_text"]

    almm_check = next((c for c in res_list if "ALMM Listed Manufacturer" in c["check_name"]), None)
    assert almm_check is not None
    assert almm_check["status"] == "COMPLIANT"



