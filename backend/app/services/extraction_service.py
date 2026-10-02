import re
from typing import Dict, Any, Optional
from backend.app.services.normalization_service import normalize_pan, normalize_gstin, normalize_cin, normalize_udyam

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Chandigarh", "Puducherry", "Goa"
]

def extract_pan(text: str) -> Optional[str]:
    # Standard Indian PAN format: 5 letters, 4 digits, 1 letter
    match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text, re.IGNORECASE)
    if match:
        return normalize_pan(match.group(1))
    return None

def extract_gstin(text: str) -> Optional[str]:
    # Standard GSTIN format: 2 digit state code, 10 char PAN, 1 entity code, Z, 1 check digit
    match = re.search(r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b', text, re.IGNORECASE)
    if match:
        return normalize_gstin(match.group(1))
    return None

def extract_cin(text: str) -> Optional[str]:
    # Standard Indian CIN: [UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}
    match = re.search(r'\b([UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6})\b', text, re.IGNORECASE)
    if match:
        return normalize_cin(match.group(1))
    return None

def extract_udyam(text: str) -> Optional[str]:
    # Format: UDYAM-XX-00-0000000
    match = re.search(r'\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7})\b', text, re.IGNORECASE)
    if match:
        return normalize_udyam(match.group(1))
    # Or without hyphens
    match2 = re.search(r'\b(UDYAM[A-Z]{2}[0-9]{9})\b', text, re.IGNORECASE)
    if match2:
        return normalize_udyam(match2.group(1))
    return None

def extract_pincode(text: str) -> Optional[str]:
    # 6 digit Indian pincode
    match = re.search(r'\b([1-9][0-9]{5})\b', text)
    if match:
        return match.group(1)
    return None

def extract_state(text: str) -> Optional[str]:
    for state in INDIAN_STATES:
        if re.search(r'\b' + re.escape(state) + r'\b', text, re.IGNORECASE):
            return state
    return None

def extract_dates(text: str) -> Optional[str]:
    # Formats like DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
    match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', text)
    if match:
        return match.group(1)
    match_iso = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if match_iso:
        return match_iso.group(1)
    return None

def extract_company_name(text: str) -> Optional[str]:
    # Look for keywords like "M/s", "Company Name:", "Legal Name:", "Name of Enterprise"
    patterns = [
        r'(?:M/s\.?|Name of Enterprise|Legal Name|Trade Name|Company Name)\s*[:\-]?\s*([A-Za-z0-9\s.,&\-\(\)]+?)(?=\n|\r|GSTIN|PAN|Address|Date|$)',
        r'([A-Za-z0-9\s.,&\-]+(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Corporation))'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Clean up line breaks and trailing symbols
            candidate = re.split(r'[\r\n]', candidate)[0].strip()
            if len(candidate) > 3 and not candidate.lower().startswith(("government", "certificate", "income tax")):
                return candidate
    return None

def extract_address(text: str) -> Optional[str]:
    # Look for address block following keywords
    pattern = r'(?:Address|Registered Office|Principal Place of Business)\s*[:\-]?\s*([^\n\r]+(?:[\r\n]+[^\n\r]+){0,3})'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        addr = match.group(1).strip()
        # Clean multi lines
        cleaned = ' '.join(addr.split())
        return cleaned[:300]
    return None

def extract_business_type(text: str) -> Optional[str]:
    types = [
        "Private Limited Company", "Public Limited Company",
        "Proprietorship", "Partnership Firm", "Limited Liability Partnership",
        "Micro Enterprise", "Small Enterprise", "Medium Enterprise"
    ]
    for b_type in types:
        if re.search(r'\b' + re.escape(b_type) + r'\b', text, re.IGNORECASE):
            return b_type
    return None

def extract_structured_fields(raw_text: str) -> Dict[str, Any]:
    """
    Extracts all standard compliance fields from OCR/parsed text.
    """
    if not raw_text:
        return {}

    gstin = extract_gstin(raw_text)
    pan = extract_pan(raw_text)

    # Derive PAN from GSTIN if PAN wasn't explicitly extracted
    if not pan and gstin and len(gstin) >= 12:
        pan = gstin[2:12]

    cin = extract_cin(raw_text)
    udyam = extract_udyam(raw_text)
    pincode = extract_pincode(raw_text)
    state = extract_state(raw_text)
    company_name = extract_company_name(raw_text)
    address = extract_address(raw_text)
    reg_date = extract_dates(raw_text)
    b_type = extract_business_type(raw_text)

    return {
        "company_name": company_name,
        "gstin": gstin,
        "pan": pan,
        "cin": cin,
        "udyam_number": udyam,
        "address": address,
        "state": state,
        "pincode": pincode,
        "registration_date": reg_date,
        "business_type": b_type
    }
