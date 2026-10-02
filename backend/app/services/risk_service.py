from typing import Dict, Any, List
from backend.app.config import settings

def calculate_risk_score(
    vendor_profile: Dict[str, Any],
    documents: List[Dict[str, Any]],
    cross_verification_matrix: List[Dict[str, Any]],
    portal_data: Dict[str, Any],
    anomaly_result: Dict[str, Any],
    custom_weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Computes an explainable, weighted verification risk score (0-100).
    Categorizes into LOW (0-30), MEDIUM (31-60), and HIGH (61-100).
    """
    weights = {
        "identity_mismatch": settings.WEIGHT_IDENTITY_MISMATCH,
        "document_issues": settings.WEIGHT_DOCUMENT_ISSUES,
        "registration_issues": settings.WEIGHT_REGISTRATION_ISSUES,
        "address_mismatch": settings.WEIGHT_ADDRESS_MISMATCH,
        "ml_anomaly": settings.WEIGHT_ML_ANOMALY,
        "missing_info": settings.WEIGHT_MISSING_INFO
    }
    if custom_weights:
        weights.update(custom_weights)

    factors = []
    explanations = []
    matrix_map = {item["field_name"]: item for item in cross_verification_matrix}

    # 1. Identity Mismatch (PAN / GSTIN / Legal Name)
    name_sim = matrix_map.get("Company Name", {}).get("similarity_score", 100.0)
    pan_sim = matrix_map.get("PAN", {}).get("similarity_score", 100.0)
    gst_sim = matrix_map.get("GSTIN", {}).get("similarity_score", 100.0)

    ident_risk_raw = 100.0 - (name_sim * 0.4 + pan_sim * 0.3 + gst_sim * 0.3)
    ident_risk_raw = max(0.0, min(100.0, ident_risk_raw))
    ident_contrib = ident_risk_raw * weights["identity_mismatch"]

    factors.append({
        "factor_name": "Identity & Legal Name Concordance",
        "raw_risk": round(ident_risk_raw, 1),
        "weight_percent": int(weights["identity_mismatch"] * 100),
        "weighted_impact": round(ident_contrib, 1),
        "status": "PASS" if ident_risk_raw < 20 else ("ELEVATED" if ident_risk_raw < 45 else "HIGH_RISK")
    })
    if ident_risk_raw > 35:
        explanations.append(f"Significant identity mismatch: Legal name or tax identification discordance ({ident_risk_raw:.1f}% risk).")
    elif ident_risk_raw > 15:
        explanations.append(f"Minor corporate naming or suffix variation noted.")

    # 2. Document Issues & Missing Docs
    uploaded_doc_types = [doc.get("doc_type", "").lower() for doc in documents]
    has_pan_doc = any("pan" in dt for dt in uploaded_doc_types)
    has_gst_doc = any("gst" in dt for dt in uploaded_doc_types)
    doc_count = len(documents)

    if not has_pan_doc and not has_gst_doc:
        doc_risk_raw = 100.0
        explanations.append("High verification risk: Crucial mandatory compliance certificates (PAN & GST) are missing.")
    elif not has_pan_doc or not has_gst_doc:
        doc_risk_raw = 55.0
        explanations.append("Moderate risk: One mandatory compliance document is missing from the submission.")
    elif doc_count < 2:
        doc_risk_raw = 25.0
        explanations.append("Only a single supporting document has been submitted.")
    else:
        doc_risk_raw = 5.0

    doc_contrib = doc_risk_raw * weights["document_issues"]
    factors.append({
        "factor_name": "Document Completeness & Authenticity",
        "raw_risk": round(doc_risk_raw, 1),
        "weight_percent": int(weights["document_issues"] * 100),
        "weighted_impact": round(doc_contrib, 1),
        "status": "PASS" if doc_risk_raw < 20 else ("ELEVATED" if doc_risk_raw < 50 else "HIGH_RISK")
    })

    # 3. Registration Issues (GST status)
    gst_status = str(portal_data.get("status", "Active")).lower()
    if gst_status == "active":
        reg_risk_raw = 0.0
    elif gst_status == "suspended":
        reg_risk_raw = 85.0
        explanations.append("High risk: Vendor GST registration is officially SUSPENDED on the government portal.")
    elif gst_status in ["cancelled", "inactive"]:
        reg_risk_raw = 100.0
        explanations.append("Critical risk: Vendor GST registration is cancelled or inactive.")
    else:
        reg_risk_raw = 50.0
        explanations.append(f"Uncertain registration status: {gst_status}.")

    reg_contrib = reg_risk_raw * weights["registration_issues"]
    factors.append({
        "factor_name": "Government Registry Operational Status",
        "raw_risk": round(reg_risk_raw, 1),
        "weight_percent": int(weights["registration_issues"] * 100),
        "weighted_impact": round(reg_contrib, 1),
        "status": "PASS" if reg_risk_raw == 0 else "HIGH_RISK"
    })

    # 4. Address Mismatch
    addr_sim = matrix_map.get("Address", {}).get("similarity_score", 100.0)
    addr_risk_raw = max(0.0, 100.0 - addr_sim)
    addr_contrib = addr_risk_raw * weights["address_mismatch"]

    factors.append({
        "factor_name": "Physical & Registered Address Alignment",
        "raw_risk": round(addr_risk_raw, 1),
        "weight_percent": int(weights["address_mismatch"] * 100),
        "weighted_impact": round(addr_contrib, 1),
        "status": "PASS" if addr_risk_raw < 25 else ("ELEVATED" if addr_risk_raw < 50 else "HIGH_RISK")
    })
    if addr_risk_raw > 40:
        explanations.append(f"Physical address differs substantially ({addr_sim}% match) from the principal place of business.")

    # 5. ML Anomaly Score
    anomaly_score = anomaly_result.get("anomaly_score", 0.15)
    ml_risk_raw = anomaly_score * 100.0
    ml_contrib = ml_risk_raw * weights["ml_anomaly"]

    factors.append({
        "factor_name": "Multivariate Anomaly Model (Isolation Forest)",
        "raw_risk": round(ml_risk_raw, 1),
        "weight_percent": int(weights["ml_anomaly"] * 100),
        "weighted_impact": round(ml_contrib, 1),
        "status": "PASS" if anomaly_score < 0.35 else ("ELEVATED" if anomaly_score < 0.65 else "HIGH_RISK")
    })
    if anomaly_score >= 0.65:
        explanations.append(anomaly_result.get("summary_statement", "Unusual operational pattern detected — manual review recommended."))

    # 6. Missing Profile Information
    missing_fields = []
    if not vendor_profile.get("cin"): missing_fields.append("CIN")
    if not vendor_profile.get("udyam_number"): missing_fields.append("Udyam")
    if not vendor_profile.get("contact_phone"): missing_fields.append("Phone")
    if not vendor_profile.get("contact_email"): missing_fields.append("Email")

    missing_risk_raw = (len(missing_fields) / 4.0) * 100.0
    missing_contrib = missing_risk_raw * weights["missing_info"]

    factors.append({
        "factor_name": "Vendor Profile & Direct Contact Details",
        "raw_risk": round(missing_risk_raw, 1),
        "weight_percent": int(weights["missing_info"] * 100),
        "weighted_impact": round(missing_contrib, 1),
        "status": "PASS" if len(missing_fields) <= 1 else "ELEVATED"
    })
    if missing_fields:
        explanations.append(f"Incomplete vendor registry entries: {', '.join(missing_fields)}.")

    total_risk = sum(f["weighted_impact"] for f in factors)
    total_risk = round(max(0.0, min(100.0, total_risk)), 1)

    if total_risk <= 30.0:
        risk_level = "LOW"
        recommended_action = "Proceed to standard procurement review."
    elif total_risk <= 60.0:
        risk_level = "MEDIUM"
        recommended_action = "Manual document verification recommended before contract award."
    else:
        risk_level = "HIGH"
        recommended_action = "High verification risk: Comprehensive physical audit and executive compliance review required."

    if not explanations:
        explanations.append("All primary verification parameters and compliance criteria successfully satisfied.")

    return {
        "risk_score": total_risk,
        "risk_level": risk_level,
        "factors": factors,
        "explanation": explanations,
        "recommended_action": recommended_action
    }
