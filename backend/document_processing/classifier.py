import re
from rapidfuzz import fuzz

DOCUMENT_CATEGORIES = {
    "GST Certificate": [
        "form gst reg-06",
        "goods and services tax",
        "gstin",
        "registration certificate",
        "legal name",
        "trade name",
        "central board of indirect taxes",
    ],
    "PAN": [
        "income tax department",
        "permanent account number",
        "pan card",
        "govt. of india",
        "income tax pan",
    ],
    "Udyam/MSME Certificate": [
        "udyam registration certificate",
        "ministry of micro, small and medium enterprises",
        "udyam-",
        "type of enterprise",
        "micro, small",
        "msme",
    ],
    "Company Registration": [
        "certificate of incorporation",
        "ministry of corporate affairs",
        "corporate identity number",
        "registrar of companies",
        "companies act",
    ],
    "OEM Authorization": [
        "manufacturer's authorization form",
        "oem authorization",
        "authorized reseller",
        "original equipment manufacturer",
        "maf certificate",
    ],
    "Startup India Certificate": [
        "department for promotion of industry and internal trade",
        "dpiit",
        "certificate of recognition",
        "startup india",
    ],
    "NSIC Certificate": [
        "national small industries corporation",
        "nsic",
        "single point registration scheme",
        "sprs",
    ],
    "EPFO": [
        "employees' provident fund organisation",
        "epfo",
        "electronic challan cum return",
        "establishment code",
        "provident fund",
    ],
    "ESIC": [
        "employees' state insurance corporation",
        "esic",
        "employer code",
        "state insurance",
    ],
    "Product Certificate": [
        "bis registration",
        "iso 9001",
        "iso 27001",
        "ce certification",
        "rohs compliant",
        "product quality certificate",
    ],
    "Technical Bid": [
        "technical bid",
        "technical specification",
        "processor",
        "ram",
        "ssd",
        "warranty",
        "local content",
        "bill of materials",
        "offered specification",
    ],
    "Tender Document": [
        "notice inviting tender",
        "request for proposal",
        "gem bid number",
        "eligibility criteria",
        "tender requirement",
        "closing date",
    ],
}

REGEX_SIGNATURES = {
    "GST Certificate": re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"),
    "Udyam/MSME Certificate": re.compile(r"\bUDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}\b", re.IGNORECASE),
    "PAN": re.compile(r"\bPermanent Account Number\b|\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
}


def classify_document(text: str, filename: str = "", declared_type: str = ""):
    """
    Identifies document category using content-based Regex signatures, keyword matching,
    RapidFuzz fuzzy matching, and document metadata.
    Does not rely solely on filename, while accurately mapping filenames like
    'Udyam Registration Certificate.pdf' -> 'Udyam/MSME Certificate'.
    Returns (detected_category, confidence_score).
    """
    combined_text = (text or "").lower()
    clean_filename = (filename or "").lower()
    clean_declared = (declared_type or "").strip()

    scores = {cat: 0.0 for cat in DOCUMENT_CATEGORIES}

    # 1. Content-based keyword & RapidFuzz scoring
    for category, keywords in DOCUMENT_CATEGORIES.items():
        matched_keywords = 0
        for kw in keywords:
            if kw in combined_text:
                scores[category] += 22.0
                matched_keywords += 1
            else:
                ratio = fuzz.partial_ratio(kw, combined_text[:2000])
                if ratio >= 85:
                    scores[category] += 12.0

        # Filename & metadata signal as secondary evidence
        for kw in keywords:
            if kw in clean_filename or fuzz.partial_ratio(kw, clean_filename) >= 85:
                scores[category] += 18.0

        if clean_declared and fuzz.token_set_ratio(category.lower(), clean_declared.lower()) >= 80:
            scores[category] += 25.0

    # 2. Strong Regex Pattern Boosts
    if REGEX_SIGNATURES["Udyam/MSME Certificate"].search(text or "") or "udyam" in clean_filename:
        scores["Udyam/MSME Certificate"] += 45.0
    if REGEX_SIGNATURES["GST Certificate"].search(text or "") and ("gst" in combined_text or "gst" in clean_filename):
        scores["GST Certificate"] += 45.0
    if "income tax" in combined_text or "permanent account number" in combined_text or "pan" in clean_filename:
        scores["PAN"] += 40.0

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score < 18.0:
        if clean_declared in DOCUMENT_CATEGORIES:
            return clean_declared, 0.78
        return "Other", 0.60

    confidence = min(0.99, round(0.65 + (best_score / 180.0), 2))
    return best_category, confidence
