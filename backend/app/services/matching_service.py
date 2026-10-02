from typing import Dict, Any, List
from rapidfuzz import fuzz
from backend.app.services.normalization_service import (
    normalize_company_name, normalize_address, normalize_pan,
    normalize_gstin, normalize_cin, normalize_udyam
)

def compute_similarity(str1: str, str2: str) -> float:
    """
    Computes a blended similarity score using RapidFuzz:
    - Token sort ratio (handles word order)
    - Standard ratio
    """
    if not str1 or not str2:
        return 0.0
    s1 = str1.strip().lower()
    s2 = str2.strip().lower()
    if s1 == s2:
        return 100.0
    
    token_sort = fuzz.token_sort_ratio(s1, s2)
    standard = fuzz.ratio(s1, s2)
    return round(float(0.6 * token_sort + 0.4 * standard), 1)

def evaluate_match(field_name: str, doc_val: str, portal_val: str, threshold_exact: float = 95.0, threshold_partial: float = 65.0) -> Dict[str, Any]:
    """
    Evaluates cross-verification match between document value and portal value.
    """
    if not doc_val or not portal_val:
        return {
            "field_name": field_name,
            "doc_value": doc_val or "Not Detected",
            "portal_value": portal_val or "Not Found",
            "match_type": "MISMATCH",
            "similarity_score": 0.0,
            "status_label": "Missing / Unmatched"
        }

    # Field-specific normalization before matching
    if field_name.lower() in ["company_name", "company name", "legal_name"]:
        n_doc = normalize_company_name(doc_val)
        n_portal = normalize_company_name(portal_val)
    elif field_name.lower() in ["address", "registered_address"]:
        n_doc = normalize_address(doc_val)
        n_portal = normalize_address(portal_val)
    elif field_name.lower() in ["pan"]:
        n_doc = normalize_pan(doc_val)
        n_portal = normalize_pan(portal_val)
    elif field_name.lower() in ["gstin"]:
        n_doc = normalize_gstin(doc_val)
        n_portal = normalize_gstin(portal_val)
    elif field_name.lower() in ["cin"]:
        n_doc = normalize_cin(doc_val)
        n_portal = normalize_cin(portal_val)
    elif field_name.lower() in ["udyam", "udyam_number"]:
        n_doc = normalize_udyam(doc_val)
        n_portal = normalize_udyam(portal_val)
    else:
        n_doc = doc_val.strip().lower()
        n_portal = portal_val.strip().lower()

    if n_doc == n_portal and n_doc != "":
        similarity = 100.0
        match_type = "EXACT"
        status_label = "EXACT MATCH"
    else:
        similarity = compute_similarity(n_doc, n_portal)
        if similarity >= threshold_exact:
            match_type = "EXACT"
            status_label = "EXACT / HIGH MATCH"
        elif similarity >= threshold_partial:
            match_type = "PARTIAL"
            status_label = "PARTIAL MATCH"
        else:
            match_type = "MISMATCH"
            status_label = "MISMATCH"

    return {
        "field_name": field_name,
        "doc_value": doc_val,
        "portal_value": portal_val,
        "match_type": match_type,
        "similarity_score": similarity,
        "status_label": status_label
    }

def cross_verify_all(doc_data: Dict[str, Any], portal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Runs full field-by-field cross verification matrix:
    - Company Name
    - PAN
    - GSTIN
    - Address
    - CIN (if present)
    - Udyam (if present)
    - Registration Status
    """
    matrix = []

    # 1. Company Name
    doc_name = doc_data.get("company_name") or doc_data.get("name")
    portal_name = portal_data.get("legal_name") or portal_data.get("company_name")
    matrix.append(evaluate_match("Company Name", doc_name or "", portal_name or "", threshold_exact=90.0, threshold_partial=65.0))

    # 2. GSTIN
    doc_gstin = doc_data.get("gstin")
    portal_gstin = portal_data.get("gstin")
    matrix.append(evaluate_match("GSTIN", doc_gstin or "", portal_gstin or "", threshold_exact=100.0, threshold_partial=80.0))

    # 3. PAN
    doc_pan = doc_data.get("pan")
    portal_pan = portal_data.get("pan")
    matrix.append(evaluate_match("PAN", doc_pan or "", portal_pan or "", threshold_exact=100.0, threshold_partial=80.0))

    # 4. Registered Address
    doc_addr = doc_data.get("address")
    portal_addr = portal_data.get("address")
    matrix.append(evaluate_match("Address", doc_addr or "", portal_addr or "", threshold_exact=85.0, threshold_partial=55.0))

    # 5. CIN (if relevant)
    doc_cin = doc_data.get("cin")
    portal_cin = portal_data.get("cin")
    if doc_cin or portal_cin:
        matrix.append(evaluate_match("CIN", doc_cin or "", portal_cin or "", threshold_exact=100.0, threshold_partial=80.0))

    # 6. Udyam Number (if relevant)
    doc_udyam = doc_data.get("udyam_number")
    portal_udyam = portal_data.get("udyam_number")
    if doc_udyam or portal_udyam:
        matrix.append(evaluate_match("Udyam Number", doc_udyam or "", portal_udyam or "", threshold_exact=100.0, threshold_partial=80.0))

    # 7. Registration Status
    portal_status = portal_data.get("status") or "Active"
    status_score = 100.0 if str(portal_status).lower() == "active" else 0.0
    status_type = "EXACT" if status_score == 100.0 else "MISMATCH"
    matrix.append({
        "field_name": "Registration Status",
        "doc_value": "Active",
        "portal_value": portal_status,
        "match_type": status_type,
        "similarity_score": status_score,
        "status_label": f"Status: {portal_status}"
    })

    return matrix
