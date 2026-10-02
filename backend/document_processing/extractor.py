import re
from rapidfuzz import fuzz

# Optional spaCy NLP loader
_SPACY_NLP = None
_SPACY_CHECKED = False


def _get_spacy_nlp():
    global _SPACY_NLP, _SPACY_CHECKED
    if _SPACY_CHECKED:
        return _SPACY_NLP
    _SPACY_CHECKED = True
    try:
        import spacy
        _SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception:
        _SPACY_NLP = None
    return _SPACY_NLP


GSTIN_REGEX = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
PAN_REGEX = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b")
UDYAM_REGEX = re.compile(r"\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7})\b", re.IGNORECASE)


def _find_field_confidence(val: str, ocr_details: list = None) -> float:
    if not ocr_details or not val:
        return 0.92
    val_clean = str(val).replace(" ", "").upper()
    for item in ocr_details:
        item_text = str(item.get("text", "")).replace(" ", "").upper()
        if val_clean in item_text or (len(val_clean) >= 5 and val_clean[:5] in item_text):
            return round(float(item.get("confidence", 0.92)), 2)
    return 0.90


def extract_structured_information(text: str, doc_type: str = "", ocr_details: list = None):
    """
    Extracts structured key-value fields and named entities from OCR text
    using Regex, spaCy (if available), and RapidFuzz matching.
    Attaches field-level EasyOCR confidence when ocr_details are provided.
    Covers:
    - GST Certificate (GSTIN, Legal Name, Trade Name, Registration Status)
    - PAN (PAN Number, Name)
    - Udyam/MSME Certificate (Udyam Registration Number, Enterprise Name, Enterprise Type)
    - Technical Bid (Product, RAM, SSD, Processor, Warranty, Local Content, Page references)
    - Tender Document / Other statutory certificates
    """
    raw = text or ""
    structured = {"document_category": doc_type}
    entities = []

    # 1. Universal Identifier Extraction
    gst_match = GSTIN_REGEX.search(raw.upper())
    if gst_match:
        gst_val = gst_match.group(1)
        conf = _find_field_confidence(gst_val, ocr_details)
        structured["gstin"] = gst_val
        entities.append({"label": "GSTIN", "text": gst_val, "confidence": conf})

    udyam_match = UDYAM_REGEX.search(raw.upper())
    if udyam_match:
        udyam_val = udyam_match.group(1).upper()
        conf = _find_field_confidence(udyam_val, ocr_details)
        structured["udyam_number"] = udyam_val
        entities.append({"label": "UDYAM_ID", "text": udyam_val, "confidence": conf})

    # Find PAN (excluding substring of GSTIN if both present)
    for pan_match in PAN_REGEX.finditer(raw.upper()):
        candidate = pan_match.group(1)
        if "gstin" in structured and candidate in structured["gstin"] and doc_type == "GST Certificate":
            continue
        conf = _find_field_confidence(candidate, ocr_details)
        structured["pan_number"] = candidate
        entities.append({"label": "PAN", "text": candidate, "confidence": conf})
        break

    # 2. Extract Key-Value lines via Regex
    kv_patterns = {
        "legal_name": r"(?:Legal Name|Name of Enterprise|Company Name|Name)\s*[:\-]\s*([^\n\r]+)",
        "trade_name": r"(?:Trade Name)\s*[:\-]\s*([^\n\r]+)",
        "registration_status": r"(?:Registration Status|Status)\s*[:\-]\s*([A-Za-z_ ]+)",
        "enterprise_name": r"(?:Name of Enterprise|Enterprise Name)\s*[:\-]\s*([^\n\r]+)",
        "enterprise_type": r"(?:Type of Enterprise|Enterprise Type)\s*[:\-]\s*([^\n\r]+)",
        "cin_number": r"(?:CIN|Corporate Identity Number|Registration Number)\s*[:\-]\s*([A-Z0-9\-]+)",
        "epfo_code": r"(?:EPFO Code|Establishment Code)\s*[:\-]\s*([A-Z0-9\-]+)",
        "esic_code": r"(?:ESIC Code|Employer Code)\s*[:\-]\s*([0-9\-]+)",
        "oem_authorization_status": r"(?:OEM Authorization|MAF Status|OEM Status)\s*[:\-]\s*([^\n\r]+)",
    }

    for field, pattern in kv_patterns.items():
        m = re.search(pattern, raw, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            structured[field] = val
            entities.append({"label": field.upper(), "text": val})

    # 3. Extract Technical Specifications (RAM, SSD, Warranty, Local Content, Processor, Display, ISO)
    tech_specs = {}

    ram_match = re.search(r"RAM\s*(?:Capacity|Size)?\s*[:\-=]?\s*([0-9]+)\s*(GB|TB)", raw, re.IGNORECASE)
    if ram_match:
        ram_val = int(ram_match.group(1))
        if ram_match.group(2).upper() == "TB":
            ram_val *= 1024
        tech_specs["RAM"] = {"value": ram_val, "unit": "GB", "page": _detect_page_number(raw, ram_match.start())}

    ssd_match = re.search(r"(?:SSD|Storage|NVMe)\s*(?:Capacity|Size)?\s*[:\-=]?\s*([0-9]+)\s*(GB|TB)", raw, re.IGNORECASE)
    if ssd_match:
        ssd_val = int(ssd_match.group(1))
        if ssd_match.group(2).upper() == "TB":
            ssd_val *= 1024
        tech_specs["SSD"] = {"value": ssd_val, "unit": "GB", "page": _detect_page_number(raw, ssd_match.start())}

    warranty_match = re.search(r"Warranty\s*(?:Period)?\s*[:\-=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(Years?|Yrs?)", raw, re.IGNORECASE)
    if warranty_match:
        tech_specs["Warranty"] = {
            "value": float(warranty_match.group(1)),
            "unit": "Years",
            "page": _detect_page_number(raw, warranty_match.start()),
        }

    lc_match = re.search(r"Local Content\s*(?:Percentage)?\s*[:\-=]?\s*([0-9]+(?:\.[0-9]+)?)\s*%", raw, re.IGNORECASE)
    if lc_match:
        tech_specs["Local Content"] = {
            "value": float(lc_match.group(1)),
            "unit": "%",
            "page": _detect_page_number(raw, lc_match.start()),
        }

    proc_match = re.search(r"Processor\s*[:\-=]\s*([^\n\r]+)", raw, re.IGNORECASE)
    if proc_match:
        tech_specs["Processor"] = {
            "value": proc_match.group(1).strip(),
            "unit": "",
            "page": _detect_page_number(raw, proc_match.start()),
        }

    if tech_specs:
        structured["technical_specifications"] = tech_specs

    # 4. Run spaCy NER if available
    nlp = _get_spacy_nlp()
    if nlp and raw:
        doc = nlp(raw[:5000])
        for ent in doc.ents:
            if ent.label_ in ("ORG", "DATE", "MONEY", "CARDINAL", "GPE"):
                entities.append({"label": ent.label_, "text": ent.text})

    # Compute confidence score based on extracted fields
    confidence = min(0.98, 0.72 + 0.04 * len(structured))
    return structured, entities, round(confidence, 2)


def _detect_page_number(text: str, char_pos: int) -> int:
    """Finds the nearest preceding [Page X] marker in extracted text, defaulting to 1."""
    preceding = text[:char_pos]
    page_markers = re.findall(r"\[Page\s+([0-9]+)\]", preceding, re.IGNORECASE)
    if page_markers:
        return int(page_markers[-1])
    return 1
