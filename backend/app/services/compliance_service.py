from typing import Dict, Any, List

def evaluate_compliance(
    vendor_profile: Dict[str, Any],
    documents: List[Dict[str, Any]],
    cross_verification_matrix: List[Dict[str, Any]],
    portal_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic rule-based compliance engine.
    Calculates Compliance Score (0-100) and returns itemized checklist.
    """
    checks = []
    passed_checks = []
    failed_checks = []
    warnings = []
    missing_docs = []

    # Map matrix results for easy lookup
    matrix_map = {item["field_name"]: item for item in cross_verification_matrix}

    # 1. Required Documents Check (Weight: 20%)
    uploaded_doc_types = [doc.get("doc_type", "").lower() for doc in documents]
    has_pan_doc = any("pan" in dt for dt in uploaded_doc_types)
    has_gst_doc = any("gst" in dt for dt in uploaded_doc_types)

    doc_score = 0.0
    if has_pan_doc and has_gst_doc:
        doc_score = 100.0
        checks.append({
            "check_name": "Mandatory Compliance Documents",
            "status": "PASS",
            "rule_description": "Both PAN and GST Registration Certificates must be provided.",
            "failure_reason": None,
            "weight": 20.0,
            "score": 20.0
        })
        passed_checks.append("Mandatory PAN and GST certificates submitted")
    else:
        if not has_pan_doc:
            missing_docs.append("PAN Card / Certificate")
        if not has_gst_doc:
            missing_docs.append("GST Registration Certificate")

        if has_pan_doc or has_gst_doc:
            doc_score = 50.0
            checks.append({
                "check_name": "Mandatory Compliance Documents",
                "status": "REVIEW",
                "rule_description": "Both PAN and GST Registration Certificates must be provided.",
                "failure_reason": f"Missing: {', '.join(missing_docs)}",
                "weight": 20.0,
                "score": 10.0
            })
            warnings.append(f"Partial documentation: Missing {', '.join(missing_docs)}")
        else:
            doc_score = 0.0
            checks.append({
                "check_name": "Mandatory Compliance Documents",
                "status": "FAIL",
                "rule_description": "Both PAN and GST Registration Certificates must be provided.",
                "failure_reason": "No primary identity documents uploaded.",
                "weight": 20.0,
                "score": 0.0
            })
            failed_checks.append("Missing mandatory compliance documents")

    # 2. Registration Status Check (Weight: 20%)
    gst_status = portal_data.get("status", "Unknown")
    reg_score = 0.0
    if str(gst_status).lower() == "active":
        reg_score = 100.0
        checks.append({
            "check_name": "GSTN Registration Active Status",
            "status": "PASS",
            "rule_description": "Vendor GST registration status must be Active on GSTN portal.",
            "failure_reason": None,
            "weight": 20.0,
            "score": 20.0
        })
        passed_checks.append("GSTN status is currently Active")
    elif str(gst_status).lower() == "suspended":
        reg_score = 25.0
        checks.append({
            "check_name": "GSTN Registration Active Status",
            "status": "FAIL",
            "rule_description": "Vendor GST registration status must be Active on GSTN portal.",
            "failure_reason": "Vendor GST registration is currently SUSPENDED.",
            "weight": 20.0,
            "score": 5.0
        })
        failed_checks.append("GSTN status is SUSPENDED")
    else:
        reg_score = 0.0
        checks.append({
            "check_name": "GSTN Registration Active Status",
            "status": "FAIL",
            "rule_description": "Vendor GST registration status must be Active on GSTN portal.",
            "failure_reason": f"GST registration is {gst_status}.",
            "weight": 20.0,
            "score": 0.0
        })
        failed_checks.append(f"GST registration is inactive ({gst_status})")

    # 3. PAN & GSTIN Cross-Verification (Weight: 20%)
    pan_item = matrix_map.get("PAN", {})
    gst_item = matrix_map.get("GSTIN", {})
    pan_sim = pan_item.get("similarity_score", 0.0)
    gst_sim = gst_item.get("similarity_score", 0.0)

    ident_score = (pan_sim * 0.5 + gst_sim * 0.5)
    if ident_score >= 95.0:
        checks.append({
            "check_name": "Tax Identification (PAN & GSTIN) Match",
            "status": "PASS",
            "rule_description": "PAN and GSTIN extracted from documents must match portal records.",
            "failure_reason": None,
            "weight": 20.0,
            "score": 20.0
        })
        passed_checks.append("PAN and GSTIN numbers exactly verified")
    elif ident_score >= 70.0:
        checks.append({
            "check_name": "Tax Identification (PAN & GSTIN) Match",
            "status": "REVIEW",
            "rule_description": "PAN and GSTIN extracted from documents must match portal records.",
            "failure_reason": "Minor character discrepancy in tax identifiers.",
            "weight": 20.0,
            "score": 12.0
        })
        warnings.append("Discrepancy in tax identifiers")
    else:
        checks.append({
            "check_name": "Tax Identification (PAN & GSTIN) Match",
            "status": "FAIL",
            "rule_description": "PAN and GSTIN extracted from documents must match portal records.",
            "failure_reason": "PAN or GSTIN does not match government portal records.",
            "weight": 20.0,
            "score": 0.0
        })
        failed_checks.append("Tax identification mismatch with government registry")

    # 4. Company Legal Name Similarity (Weight: 15%)
    name_item = matrix_map.get("Company Name", {})
    name_sim = name_item.get("similarity_score", 0.0)

    if name_sim >= 85.0:
        name_score = 15.0
        checks.append({
            "check_name": "Company Legal Name Consistency",
            "status": "PASS",
            "rule_description": "Legal company name similarity must meet or exceed 85%.",
            "failure_reason": None,
            "weight": 15.0,
            "score": 15.0
        })
        passed_checks.append(f"Company name similarity is high ({name_sim}%)")
    elif name_sim >= 60.0:
        name_score = 8.0
        checks.append({
            "check_name": "Company Legal Name Consistency",
            "status": "REVIEW",
            "rule_description": "Legal company name similarity must meet or exceed 85%.",
            "failure_reason": f"Name similarity is {name_sim}%. Trade name vs legal name variation suspected.",
            "weight": 15.0,
            "score": 8.0
        })
        warnings.append(f"Company name partial match ({name_sim}%): requires manual confirmation")
    else:
        name_score = 0.0
        checks.append({
            "check_name": "Company Legal Name Consistency",
            "status": "FAIL",
            "rule_description": "Legal company name similarity must meet or exceed 85%.",
            "failure_reason": f"Company name mismatch ({name_sim}%). Document entity differs from registry.",
            "weight": 15.0,
            "score": 0.0
        })
        failed_checks.append(f"Significant company name mismatch ({name_sim}%)")

    # 5. Registered Address Consistency (Weight: 10%)
    addr_item = matrix_map.get("Address", {})
    addr_sim = addr_item.get("similarity_score", 0.0)

    if addr_sim >= 80.0:
        addr_score = 10.0
        checks.append({
            "check_name": "Registered Address Match",
            "status": "PASS",
            "rule_description": "Document address must correspond with registered principal place of business.",
            "failure_reason": None,
            "weight": 10.0,
            "score": 10.0
        })
        passed_checks.append(f"Registered address verified ({addr_sim}%)")
    elif addr_sim >= 50.0:
        addr_score = 6.0
        checks.append({
            "check_name": "Registered Address Match",
            "status": "REVIEW",
            "rule_description": "Document address must correspond with registered principal place of business.",
            "failure_reason": f"Address differs slightly between document and portal ({addr_sim}%).",
            "weight": 10.0,
            "score": 6.0
        })
        warnings.append(f"Address formatting difference detected ({addr_sim}%)")
    else:
        addr_score = 2.0
        checks.append({
            "check_name": "Registered Address Match",
            "status": "FAIL",
            "rule_description": "Document address must correspond with registered principal place of business.",
            "failure_reason": f"Registered address mismatch ({addr_sim}%).",
            "weight": 10.0,
            "score": 2.0
        })
        warnings.append("Significant address divergence from government registry")

    # 6. Profile Completeness & Document Validity (Weight: 15%)
    validity_points = 0
    if vendor_profile.get("contact_email"): validity_points += 3
    if vendor_profile.get("contact_phone"): validity_points += 3
    if vendor_profile.get("cin") or vendor_profile.get("udyam_number"): validity_points += 4
    if len(documents) >= 2: validity_points += 5

    validity_score = float(validity_points)
    if validity_points >= 12:
        checks.append({
            "check_name": "Profile Completeness & Document Validity",
            "status": "PASS",
            "rule_description": "Comprehensive contact, corporate registration, and secondary proofs provided.",
            "failure_reason": None,
            "weight": 15.0,
            "score": validity_score
        })
        passed_checks.append("Profile details and supporting documentation complete")
    else:
        checks.append({
            "check_name": "Profile Completeness & Document Validity",
            "status": "REVIEW",
            "rule_description": "Comprehensive contact, corporate registration, and secondary proofs provided.",
            "failure_reason": "Incomplete corporate details or single document uploaded.",
            "weight": 15.0,
            "score": validity_score
        })
        warnings.append("Additional corporate details or secondary documentation recommended")

    total_compliance = round(doc_score * 0.20 + reg_score * 0.20 + (ident_score / 100.0 * 20.0) + name_score + addr_score + validity_score, 1)
    total_compliance = max(0.0, min(100.0, total_compliance))

    return {
        "compliance_score": total_compliance,
        "checks": checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "missing_documents": missing_docs
    }
