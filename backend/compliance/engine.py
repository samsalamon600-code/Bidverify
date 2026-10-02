import json
import re
from rapidfuzz import fuzz
from backend.config import Config
from backend.extensions import db
from backend.models.models import (
    Bid,
    ComplianceResult,
    Evidence,
    RiskResult,
)
from backend.document_processing.pipeline import process_document_pipeline
from backend.integrations import (
    verify_gstin,
    verify_udyam,
    verify_mca_and_pan,
    verify_digilocker_document,
    verify_epfo_compliance,
    verify_esic_compliance,
    check_debarment_status,
)
from backend.ml.risk_analyzer import run_isolation_forest_risk_analysis


def _parse_numeric(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(val))
    return float(m.group(0)) if m else None


def run_bid_compliance_verification(bid: Bid, commit: bool = True):
    """
    Modular Compliance Verification Engine (Decision-Support Only).
    Executes all 17 compliance & risk verification dimensions:
    1. Processes any unprocessed documents on the bid via OpenCV + EasyOCR + NLP pipeline
    2. Checks required documents presence & missing document detection
    3. Statutory checks (GST, PAN/MCA, Udyam/MSME, EPFO, ESIC, Debarment/Watchlist, DigiLocker)
    4. Cross-document consistency & conflicting information detection
    5. Make in India / Local Content compliance check
    6. OEM Authorization / Startup India / NSIC check
    7. Technical & Tender-specific structured requirements comparison
    8. Scikit-learn Isolation Forest anomaly & risk analysis
    9. Configurable weighted compliance score calculation
    10. Evidence generation for every single check
    """
    tender = bid.tender
    company = bid.company

    # Ensure all uploaded documents have been processed by OCR/NLP pipeline
    for doc in bid.documents:
        if doc.processing_status != "PROCESSED" or not doc.extractions:
            process_document_pipeline(doc, commit=False)

    # Clear previous compliance, evidence, and risk records for idempotent re-verification
    Evidence.query.filter_by(bid_id=bid.id).delete()
    ComplianceResult.query.filter_by(bid_id=bid.id).delete()
    RiskResult.query.filter_by(bid_id=bid.id).delete()
    db.session.flush()

    # Map uploaded documents by detected or declared category
    doc_map = {}
    extracted_fields = {}
    for doc in bid.documents:
        cat = doc.detected_doc_type or doc.declared_doc_type or "Other"
        doc_map[cat] = doc
        if doc.declared_doc_type:
            doc_map[doc.declared_doc_type] = doc
        if doc.extractions:
            ext_dict = doc.extractions[-1].to_dict()
            s_data = ext_dict.get("structured_data", {})
            for k, v in s_data.items():
                if k not in extracted_fields and v:
                    extracted_fields[k] = (v, doc)

    results = []

    def add_check(
        check_code,
        check_name,
        category,
        req_text,
        sub_text,
        status,
        reason,
        source="Internal Compliance Engine",
        doc=None,
        page=1,
        snippet="",
        field_name="",
    ):
        cr = ComplianceResult(
            bid_id=bid.id,
            check_code=check_code,
            check_name=check_name,
            category=category,
            requirement_text=str(req_text),
            submitted_text=str(sub_text),
            status=status,
            reason=reason,
            integration_source=source,
        )
        db.session.add(cr)
        db.session.flush()

        ev = Evidence(
            compliance_result_id=cr.id,
            bid_id=bid.id,
            document_id=doc.id if doc else None,
            document_name=doc.original_filename if doc else "Bidder Profile / Bid Submission Form",
            page_number=page,
            extracted_snippet=snippet or f"Extracted Field [{field_name or check_name}]: {sub_text}",
            field_name=field_name or check_name,
            expected_value=str(req_text),
            actual_value=str(sub_text),
            explanation=reason,
        )
        db.session.add(ev)
        results.append(cr)
        return cr

    # =========================================================================
    # A. DOCUMENT COMPLETENESS & MISSING DOCUMENT DETECTION (Category: DOCUMENT)
    # =========================================================================
    required_docs = tender.get_required_docs_list() if tender else [
        "Technical Bid",
        "GST Certificate",
        "PAN",
        "Udyam/MSME Certificate",
        "OEM Authorization",
    ]
    if not required_docs:
        required_docs = ["Technical Bid", "GST Certificate", "PAN"]

    for idx, req_doc_type in enumerate(required_docs, start=1):
        matched_doc = None
        for uploaded_cat, doc_obj in doc_map.items():
            if fuzz.token_set_ratio(req_doc_type.lower(), uploaded_cat.lower()) >= 75:
                matched_doc = doc_obj
                break

        if matched_doc:
            low_ocr = (
                matched_doc.ocr_confidence is not None
                and 0.0 < matched_doc.ocr_confidence < Config.OCR_CONFIDENCE_THRESHOLD
            )
            doc_status = "NEEDS_REVIEW" if low_ocr else "COMPLIANT"
            reason_msg = (
                f"Low OCR confidence ({matched_doc.ocr_confidence:.2f} < {Config.OCR_CONFIDENCE_THRESHOLD:.2f}). Document '{req_doc_type}' requires human review."
                if low_ocr
                else f"Required document '{req_doc_type}' was uploaded, validated, and classified with {int((matched_doc.classification_confidence or 0.9)*100)}% confidence."
            )
            add_check(
                check_code=f"DOC_REQ_{idx}",
                check_name=f"Mandatory Document: {req_doc_type}",
                category="DOCUMENT",
                req_text=f"{req_doc_type} must be uploaded and readable",
                sub_text=f"{matched_doc.original_filename} (Classified: {matched_doc.detected_doc_type})",
                status=doc_status,
                reason=reason_msg,
                source=f"{Config.OCR_ENGINE} + Document Classifier",
                doc=matched_doc,
                page=1,
                snippet=(matched_doc.extractions[-1].raw_text[:220] if matched_doc.extractions and matched_doc.extractions[-1].raw_text else matched_doc.original_filename),
                field_name=req_doc_type,
            )
        else:
            add_check(
                check_code=f"DOC_REQ_{idx}",
                check_name=f"Mandatory Document: {req_doc_type}",
                category="DOCUMENT",
                req_text=f"{req_doc_type} must be uploaded",
                sub_text="MISSING DOCUMENT",
                status="NON_COMPLIANT",
                reason=f"Mandatory tender document '{req_doc_type}' is missing from the bidder's submission package.",
                source="Missing Information Detector",
                doc=None,
                page=1,
                snippet=f"No uploaded file matched '{req_doc_type}' in bid #{bid.bid_number}.",
                field_name=req_doc_type,
            )

    # =========================================================================
    # B. STATUTORY & AUTHORIZED ADAPTER CHECKS (Category: STATUTORY)
    # =========================================================================
    gst_doc = doc_map.get("GST Certificate")
    extracted_gstin = extracted_fields.get("gstin", (None, None))[0]
    effective_gstin = extracted_gstin or (company.gstin if company else None)

    gst_res = verify_gstin(effective_gstin, company.company_name if company else "")
    gst_status = "COMPLIANT" if gst_res["verified"] else "NON_COMPLIANT"
    gst_reason = gst_res["reason"]
    if gst_doc and gst_doc.ocr_confidence is not None and 0.0 < gst_doc.ocr_confidence < Config.OCR_CONFIDENCE_THRESHOLD:
        gst_status = "NEEDS_REVIEW"
        gst_reason = f"Low OCR Confidence ({gst_doc.ocr_confidence:.2f} < {Config.OCR_CONFIDENCE_THRESHOLD:.2f}) on GST document. {gst_reason} Human Review Required."

    add_check(
        check_code="STAT_GST_VERIFY",
        check_name="GST Registration & Filing Status",
        category="STATUTORY",
        req_text="Active 15-digit GSTIN with regular GSTR filings",
        sub_text=f"{effective_gstin or 'Not Provided'} ({gst_res.get('status', 'UNKNOWN')})",
        status=gst_status,
        reason=gst_reason,
        source=gst_res["source"],
        doc=gst_doc,
        page=1,
        snippet=f"GSTIN: {effective_gstin} | Status: {gst_res.get('status')} | Filing: {gst_res.get('filing_status', 'N/A')}",
        field_name="GSTIN",
    )

    # Cross-check inconsistency between Company Profile GSTIN and OCR Extracted GSTIN
    if extracted_gstin and company and company.gstin and extracted_gstin.upper() != company.gstin.upper():
        add_check(
            check_code="CONSISTENCY_GSTIN",
            check_name="Cross-Document GSTIN Consistency Check",
            category="STATUTORY",
            req_text=f"Profile GSTIN ({company.gstin}) must match GST Certificate",
            sub_text=f"Document GSTIN: {extracted_gstin}",
            status="NEEDS_REVIEW",
            reason=f"Inconsistent information detected: Company profile declares GSTIN '{company.gstin}', whereas uploaded GST document contains '{extracted_gstin}'.",
            source="Inconsistency Detection Engine",
            doc=gst_doc,
            page=1,
            snippet=f"Profile GSTIN={company.gstin} vs OCR GSTIN={extracted_gstin}",
            field_name="GSTIN Consistency",
        )

    # PAN & MCA Check
    pan_doc = doc_map.get("PAN")
    extracted_pan = extracted_fields.get("pan_number", (None, None))[0]
    effective_pan = extracted_pan or (company.pan if company else None)
    mca_res = verify_mca_and_pan(
        company.registration_number if company else "",
        effective_pan,
        company.company_name if company else "",
    )
    pan_status = "COMPLIANT" if mca_res["verified"] else "NON_COMPLIANT"
    pan_reason = mca_res["reason"]
    if pan_doc and pan_doc.ocr_confidence is not None and 0.0 < pan_doc.ocr_confidence < Config.OCR_CONFIDENCE_THRESHOLD:
        pan_status = "NEEDS_REVIEW"
        pan_reason = f"Low OCR Confidence ({pan_doc.ocr_confidence:.2f} < {Config.OCR_CONFIDENCE_THRESHOLD:.2f}) on PAN document. {pan_reason} Human Review Required."

    add_check(
        check_code="STAT_PAN_MCA",
        check_name="PAN & Income Tax / MCA Corporate Compliance",
        category="STATUTORY",
        req_text="Valid Corporate PAN & Active MCA Registration",
        sub_text=f"PAN: {effective_pan or 'Missing'} | CIN: {company.registration_number if company else 'N/A'}",
        status=pan_status,
        reason=pan_reason,
        source=mca_res["source"],
        doc=pan_doc,
        page=1,
        snippet=f"PAN: {effective_pan} | Status: {mca_res.get('company_status', 'Unverified')}",
        field_name="PAN Number",
    )

    # Udyam / MSME Verification
    udyam_doc = doc_map.get("Udyam/MSME Certificate")
    extracted_udyam = extracted_fields.get("udyam_number", (None, None))[0]
    effective_udyam = extracted_udyam or (company.udyam_number if company else None)
    udyam_res = verify_udyam(effective_udyam, company.company_name if company else "")
    udyam_status = "COMPLIANT" if udyam_res["verified"] else "NEEDS_REVIEW"
    udyam_reason = udyam_res["reason"]
    if udyam_doc and udyam_doc.ocr_confidence is not None and 0.0 < udyam_doc.ocr_confidence < Config.OCR_CONFIDENCE_THRESHOLD:
        udyam_status = "NEEDS_REVIEW"
        udyam_reason = f"Low OCR Confidence ({udyam_doc.ocr_confidence:.2f} < {Config.OCR_CONFIDENCE_THRESHOLD:.2f}) on Udyam document. {udyam_reason} Human Review Required."

    add_check(
        check_code="STAT_UDYAM_MSME",
        check_name="Udyam / MSME Statutory Verification",
        category="STATUTORY",
        req_text="Valid Udyam Registration (UDYAM-XX-00-0000000)",
        sub_text=f"{effective_udyam or 'Not Provided'}",
        status=udyam_status,
        reason=udyam_reason,
        source=udyam_res["source"],
        doc=udyam_doc,
        page=1,
        snippet=f"Udyam ID: {effective_udyam} | Enterprise Type: {udyam_res.get('enterprise_type', 'N/A')}",
        field_name="Udyam Registration Number",
    )

    # EPFO & ESIC Labour Statutory Check
    epfo_res = verify_epfo_compliance(company.company_name if company else "")
    esic_res = verify_esic_compliance(company.company_name if company else "")
    epfo_esic_ok = epfo_res["verified"] and esic_res["verified"]
    add_check(
        check_code="STAT_EPFO_ESIC",
        check_name="EPFO & ESIC Labour Statutory Compliance",
        category="STATUTORY",
        req_text="Active EPFO ECR & ESIC Employer Contribution Status",
        sub_text=f"EPFO: {epfo_res['status']} | ESIC: {esic_res['status']}",
        status="COMPLIANT" if epfo_esic_ok else "NON_COMPLIANT",
        reason=f"{epfo_res['reason']} {esic_res['reason']}",
        source=epfo_res["source"],
        doc=doc_map.get("EPFO") or doc_map.get("ESIC"),
        page=1,
        snippet=f"EPFO Code: {epfo_res['epfo_code']} ({epfo_res['status']})",
        field_name="EPFO / ESIC Status",
    )

    # Blacklisting / Debarment Watchlist Check
    debar_res = check_debarment_status(
        effective_gstin,
        effective_pan,
        company.company_name if company else "",
    )
    add_check(
        check_code="STAT_DEBARMENT",
        check_name="Debarment / Blacklisting Watchlist Check",
        category="STATUTORY",
        req_text="Bidder must not be debarred or blacklisted on GeM / Public Procurement Watchlist",
        sub_text=debar_res["status"],
        status="COMPLIANT" if debar_res["clear"] else "NON_COMPLIANT",
        reason=debar_res["reason"],
        source=debar_res["source"],
        doc=None,
        page=1,
        snippet=debar_res["reason"],
        field_name="Debarment Status",
    )

    # DigiLocker Document Verification Check
    dl_res = verify_digilocker_document("GST & Udyam Statutory Certificates", effective_gstin or effective_udyam or "")
    add_check(
        check_code="STAT_DIGILOCKER",
        check_name="DigiLocker Issuer Metadata Verification",
        category="STATUTORY",
        req_text="Verifiable certificate identifier for DigiLocker issuer validation",
        sub_text=dl_res.get("digital_signature_status", "Unverified"),
        status="COMPLIANT" if dl_res["verified"] else "NEEDS_REVIEW",
        reason=dl_res["reason"],
        source=dl_res["source"],
        doc=gst_doc or udyam_doc,
        page=1,
        snippet=dl_res["reason"],
        field_name="DigiLocker Reference",
    )

    # =========================================================================
    # C. TENDER POLICY & MAKE IN INDIA / OEM CHECKS (Category: TENDER)
    # =========================================================================
    req_lc = float(tender.local_content_requirements if tender and tender.local_content_requirements is not None else 50.0)
    sub_lc = float(bid.local_content_declared if bid.local_content_declared is not None else 0.0)

    # Check if Technical Bid document extracted a conflicting Local Content percentage
    tech_doc = doc_map.get("Technical Bid")
    doc_lc = None
    if tech_doc and tech_doc.extractions:
        t_struct = tech_doc.extractions[-1].to_dict().get("structured_data", {})
        lc_spec = t_struct.get("technical_specifications", {}).get("Local Content")
        if lc_spec:
            doc_lc = float(lc_spec.get("value", sub_lc))

    if doc_lc is not None and abs(doc_lc - sub_lc) > 2.0:
        add_check(
            check_code="TENDER_LC_INCONSISTENCY",
            check_name="Local Content Declaration Consistency",
            category="TENDER",
            req_text=f"Bid Form Local Content ({sub_lc}%) must match Technical Document ({doc_lc}%)",
            sub_text=f"Bid Form: {sub_lc}% vs Document: {doc_lc}%",
            status="NEEDS_REVIEW",
            reason=f"Conflicting information detected: Bidder declared {sub_lc}% local content in bid form, but uploaded Technical Bid states {doc_lc}%.",
            source="Inconsistency Detection Engine",
            doc=tech_doc,
            page=2,
            snippet=f"Local Content Percentage: {doc_lc}% (vs {sub_lc}% in portal form)",
            field_name="Local Content Consistency",
        )

    lc_status = "COMPLIANT" if sub_lc >= req_lc else "NON_COMPLIANT"
    add_check(
        check_code="TENDER_MII_LOCAL_CONTENT",
        check_name="Make in India (PPP-MII) Local Content Requirement",
        category="TENDER",
        req_text=f"Local Content >= {req_lc:g}% (Class-I / Class-II Local Supplier)",
        sub_text=f"{sub_lc:g}%",
        status=lc_status,
        reason=(
            f"Submitted local content ({sub_lc:g}%) meets the minimum tender requirement of {req_lc:g}%."
            if lc_status == "COMPLIANT"
            else f"Submitted local content ({sub_lc:g}%) is below the required minimum of {req_lc:g}%."
        ),
        source="PPP-MII Policy Rule Engine",
        doc=tech_doc,
        page=2,
        snippet=f"Declared Make in India Local Content: {sub_lc:g}% (Required >= {req_lc:g}%)",
        field_name="Local Content (%)",
    )

    # OEM Authorization / Startup / NSIC Check
    oem_doc = doc_map.get("OEM Authorization") or doc_map.get("Startup India Certificate") or doc_map.get("NSIC Certificate")
    oem_declared = (bid.oem_status or "").strip()
    oem_ok = bool(oem_doc) or ("oem" in oem_declared.lower() or "authorized" in oem_declared.lower())
    add_check(
        check_code="TENDER_OEM_AUTH",
        check_name="OEM Authorization (MAF) / Startup / NSIC Eligibility",
        category="TENDER",
        req_text=tender.oem_requirements if tender and tender.oem_requirements else "Valid OEM Authorization or Direct OEM Status",
        sub_text=f"{oem_declared or 'Unspecified'} ({oem_doc.original_filename if oem_doc else 'No MAF Doc'})",
        status="COMPLIANT" if (oem_ok and oem_doc) else ("NEEDS_REVIEW" if oem_ok else "NON_COMPLIANT"),
        reason=(
            f"Bidder verified as '{oem_declared}' with supporting certificate '{oem_doc.original_filename}'."
            if (oem_ok and oem_doc)
            else "OEM status declared in form, but supporting MAF/OEM certificate requires Procurement Officer verification."
            if oem_ok
            else "Missing OEM Authorization (MAF) and bidder is not registered as direct OEM."
        ),
        source="Tender Eligibility Engine",
        doc=oem_doc,
        page=1,
        snippet=f"OEM Status: {oem_declared}",
        field_name="OEM Authorization",
    )

    # =========================================================================
    # D. TECHNICAL SPECIFICATIONS COMPARISON (Category: TECHNICAL)
    # =========================================================================
    # Build lookup of submitted BidItems + extracted technical specs
    submitted_specs = {}
    for item in bid.items:
        submitted_specs[item.parameter_name.lower()] = {
            "value": item.submitted_value,
            "unit": item.unit or "",
            "doc_name": item.source_document or (tech_doc.original_filename if tech_doc else "Technical_Bid.pdf"),
            "page": item.source_page or 4,
        }

    if tech_doc and tech_doc.extractions:
        t_struct = tech_doc.extractions[-1].to_dict().get("structured_data", {})
        for param_k, spec_v in t_struct.get("technical_specifications", {}).items():
            if param_k.lower() not in submitted_specs:
                submitted_specs[param_k.lower()] = {
                    "value": str(spec_v.get("value", "")),
                    "unit": spec_v.get("unit", ""),
                    "doc_name": tech_doc.original_filename,
                    "page": int(spec_v.get("page", 4)),
                }

    # Also include Warranty from bid
    if "warranty" not in submitted_specs:
        submitted_specs["warranty"] = {
            "value": str(bid.warranty_years or 3),
            "unit": "Years",
            "doc_name": tech_doc.original_filename if tech_doc else "Technical_Bid.pdf",
            "page": 4,
        }

    tender_reqs = tender.requirements if tender else []
    for req in tender_reqs:
        if req.category.upper() in ("DOCUMENT",):
            continue
        p_key = req.parameter_name.lower()
        # Find best fuzzy match in submitted_specs
        matched_spec = submitted_specs.get(p_key)
        if not matched_spec:
            for sk, sv in submitted_specs.items():
                if fuzz.token_set_ratio(p_key, sk) >= 80:
                    matched_spec = sv
                    break

        req_display = f"{req.parameter_name} {req.operator} {req.required_value} {req.unit or ''}".strip()

        if not matched_spec:
            add_check(
                check_code=f"TECH_REQ_{req.id}",
                check_name=f"Technical Spec: {req.parameter_name}",
                category="TECHNICAL" if req.category.upper() == "TECHNICAL" else "TENDER",
                req_text=req_display,
                sub_text="MISSING SPECIFICATION",
                status="NON_COMPLIANT" if req.is_mandatory else "NEEDS_REVIEW",
                reason=f"Required technical parameter '{req.parameter_name}' was not found in the submitted technical bid.",
                source="Technical Specification Comparator",
                doc=tech_doc,
                page=4,
                snippet=f"Parameter '{req.parameter_name}' missing from extracted technical table.",
                field_name=req.parameter_name,
            )
            continue

        sub_val_raw = matched_spec["value"]
        sub_unit = matched_spec["unit"] or req.unit or ""
        sub_display = f"{sub_val_raw} {sub_unit}".strip()
        page_num = matched_spec.get("page", 4)

        req_num = _parse_numeric(req.required_value)
        sub_num = _parse_numeric(sub_val_raw)

        status = "COMPLIANT"
        reason = f"Submitted {req.parameter_name} ({sub_display}) satisfies requirement ({req_display})."

        if req.operator in (">=", "<=", ">", "<", "==") and req_num is not None and sub_num is not None:
            if req.operator == ">=" and sub_num < req_num:
                status = "NON_COMPLIANT"
                reason = f"Submitted {req.parameter_name} capacity/value ({sub_display}) is below the required minimum ({req.required_value} {req.unit or ''})."
            elif req.operator == "<=" and sub_num > req_num:
                status = "NON_COMPLIANT"
                reason = f"Submitted {req.parameter_name} ({sub_display}) exceeds the maximum threshold ({req.required_value} {req.unit or ''})."
            elif req.operator == "==" and abs(sub_num - req_num) > 1e-6:
                status = "NON_COMPLIANT"
                reason = f"Submitted {req.parameter_name} ({sub_display}) does not match exact requirement ({req.required_value} {req.unit or ''})."
        else:
            # String / keyword comparison
            sim = fuzz.token_set_ratio(str(req.required_value).lower(), str(sub_val_raw).lower())
            if sim < 65 and str(req.required_value).lower() not in str(sub_val_raw).lower():
                status = "NON_COMPLIANT"
                reason = f"Submitted specification '{sub_display}' does not meet required specification '{req.required_value}'."

        add_check(
            check_code=f"TECH_REQ_{req.id}",
            check_name=f"Technical Spec: {req.parameter_name}",
            category="TECHNICAL" if req.category.upper() == "TECHNICAL" else "TENDER",
            req_text=req_display,
            sub_text=sub_display,
            status=status,
            reason=reason,
            source="Technical Specification Comparator",
            doc=tech_doc,
            page=page_num,
            snippet=f"{ matched_spec['doc_name'] }, Page {page_num} -> {req.parameter_name}: {sub_display}",
            field_name=req.parameter_name,
        )

    # =========================================================================
    # E. COMPUTE TRANSPARENT CATEGORY & OVERALL COMPLIANCE SCORES
    # =========================================================================
    def compute_category_score(cat_name):
        cat_items = [r for r in results if r.category == cat_name and r.status != "NOT_APPLICABLE"]
        if not cat_items:
            return 100.0
        total_pts = 0.0
        for r in cat_items:
            if r.status == "COMPLIANT":
                total_pts += 100.0
            elif r.status == "NEEDS_REVIEW":
                total_pts += 60.0
            else:
                total_pts += 0.0
        return round(total_pts / len(cat_items), 1)

    doc_score = compute_category_score("DOCUMENT")
    stat_score = compute_category_score("STATUTORY")
    tech_score = compute_category_score("TECHNICAL")
    tender_score = compute_category_score("TENDER")

    weights = Config.COMPLIANCE_WEIGHTS
    overall_score = round(
        (doc_score * weights.get("DOCUMENT", 0.25))
        + (stat_score * weights.get("STATUTORY", 0.25))
        + (tech_score * weights.get("TECHNICAL", 0.30))
        + (tender_score * weights.get("TENDER", 0.20)),
        1,
    )

    # =========================================================================
    # F. RUN SCIKIT-LEARN ISOLATION FOREST RISK & ANOMALY ANALYSIS
    # =========================================================================
    risk_data = run_isolation_forest_risk_analysis(bid, tender, results)
    risk_record = RiskResult(
        bid_id=bid.id,
        risk_level=risk_data["risk_level"],
        risk_score=risk_data["risk_score"],
        anomaly_score=risk_data["anomaly_score"],
        is_anomaly_flagged=risk_data["is_anomaly_flagged"],
        risk_factors_json=risk_data["risk_factors_json"],
        ml_explanation=risk_data["ml_explanation"],
        requires_human_review=True,
    )
    db.session.add(risk_record)

    # Update Bid summary scores (Decision Support Only - Officer Review Status stays PENDING_REVIEW unless reviewed)
    bid.document_compliance_score = doc_score
    bid.statutory_compliance_score = stat_score
    bid.technical_compliance_score = tech_score
    bid.tender_compliance_score = tender_score
    bid.overall_compliance_score = overall_score
    bid.risk_level = risk_data["risk_level"]

    has_non_compliant = any(r.status == "NON_COMPLIANT" for r in results)
    has_needs_review = any(r.status == "NEEDS_REVIEW" for r in results) or risk_data["is_anomaly_flagged"]

    if has_non_compliant or has_needs_review:
        bid.verification_status = "NEEDS_REVIEW"
    else:
        bid.verification_status = "VERIFIED"

    if commit:
        db.session.commit()

    return {
        "bid_id": bid.id,
        "bid_number": bid.bid_number,
        "overall_compliance_score": overall_score,
        "category_scores": {
            "document_compliance": doc_score,
            "statutory_compliance": stat_score,
            "technical_compliance": tech_score,
            "tender_compliance": tender_score,
        },
        "weights_applied": weights,
        "risk_level": risk_data["risk_level"],
        "risk_analysis": risk_record.to_dict(),
        "compliance_results": [r.to_dict() for r in results],
        "decision_support_disclaimer": (
            "DECISION SUPPORT ONLY: Automated compliance scores and ML anomaly indicators assist the "
            "Procurement Officer and do NOT constitute an automatic award or rejection decision."
        ),
    }
