import re
from typing import Optional

def normalize_company_name(name: Optional[str]) -> str:
    """
    Normalizes company names:
    - Lowercase
    - Removes punctuation and extra whitespace
    - Normalizes legal suffixes like 'Private Limited', 'Pvt. Ltd.', 'Ltd', 'LLP'
    """
    if not name:
        return ""

    text = name.lower().strip()

    # Replace common abbreviations and suffixes
    text = re.sub(r'\bprivate\s+limited\b', 'pvt ltd', text)
    text = re.sub(r'\bpvt\.?\s*ltd\.?\b', 'pvt ltd', text)
    text = re.sub(r'\bpvt\.?\s*limited\b', 'pvt ltd', text)
    text = re.sub(r'\blimited\b', 'ltd', text)
    text = re.sub(r'\bltd\.?\b', 'ltd', text)
    text = re.sub(r'\blimited\s+liability\s+partnership\b', 'llp', text)
    text = re.sub(r'\bl\.?l\.?p\.?\b', 'llp', text)
    text = re.sub(r'\bcorporation\b', 'corp', text)
    text = re.sub(r'\bcorp\.?\b', 'corp', text)
    text = re.sub(r'\btechnologies\b', 'tech', text)
    text = re.sub(r'\btechnology\b', 'tech', text)
    text = re.sub(r'\bsolutions\b', 'soln', text)
    text = re.sub(r'\bsolution\b', 'soln', text)
    text = re.sub(r'\bservices\b', 'services', text)
    text = re.sub(r'\benterprises\b', 'enterprises', text)

    # Remove non-alphanumeric characters except spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_address(address: Optional[str]) -> str:
    """
    Normalizes address strings:
    - Lowercase
    - Removes punctuation
    - Normalizes common road/street abbreviations
    """
    if not address:
        return ""

    text = address.lower().strip()
    text = re.sub(r'\broad\b', 'rd', text)
    text = re.sub(r'\bstreet\b', 'st', text)
    text = re.sub(r'\bavenue\b', 'ave', text)
    text = re.sub(r'\bbuilding\b', 'bldg', text)
    text = re.sub(r'\bfloor\b', 'flr', text)
    text = re.sub(r'\bsector\b', 'sec', text)
    text = re.sub(r'\bplot\s*(no\.?)?\b', 'plot', text)
    text = re.sub(r'\bflat\s*(no\.?)?\b', 'flat', text)
    text = re.sub(r'\bnear\b', 'nr', text)
    text = re.sub(r'\bopposite\b', 'opp', text)

    # Remove non-alphanumeric except spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_pan(pan: Optional[str]) -> str:
    if not pan:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', pan).upper()
    return clean

def normalize_gstin(gstin: Optional[str]) -> str:
    if not gstin:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', gstin).upper()
    return clean

def normalize_cin(cin: Optional[str]) -> str:
    if not cin:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', cin).upper()
    return clean

def normalize_udyam(udyam: Optional[str]) -> str:
    if not udyam:
        return ""
    # Format: UDYAM-XX-00-0000000
    clean = re.sub(r'[^a-zA-Z0-9]', '', udyam).upper()
    if clean.startswith("UDYAM") and len(clean) >= 19:
        return f"UDYAM-{clean[5:7]}-{clean[7:9]}-{clean[9:16]}"
    return clean

def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = re.sub(r'\D', '', phone)
    if len(digits) > 10:
        return digits[-10:]
    return digits
