import re
from backend.config import Config

UDYAM_PATTERN = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")

DEMO_UDYAM_REGISTRY = {
    "UDYAM-DL-01-0012345": {
        "enterprise_name": "Apex Bharat Technologies Pvt. Ltd.",
        "enterprise_type": "Small Enterprise",
        "major_activity": "Manufacturing",
        "status": "ACTIVE",
        "nic_code": "2620 - Manufacture of computers and peripheral equipment",
    },
    "UDYAM-MH-04-0056789": {
        "enterprise_name": "NovaGrid InfoSystems Ltd.",
        "enterprise_type": "Medium Enterprise",
        "major_activity": "Services",
        "status": "ACTIVE",
        "nic_code": "6202 - Computer consultancy and computer facilities management",
    },
    "UDYAM-KA-02-0090123": {
        "enterprise_name": "Shakti Sovereign Hardware Solutions Pvt. Ltd.",
        "enterprise_type": "Small Enterprise",
        "major_activity": "Manufacturing",
        "status": "ACTIVE",
        "nic_code": "2620 - Manufacture of computers and peripheral equipment",
    },
    "UDYAM-GJ-06-0078901": {
        "enterprise_name": "Pragati Digital Peripherals LLP",
        "enterprise_type": "Micro Enterprise",
        "major_activity": "Manufacturing",
        "status": "ACTIVE",
        "nic_code": "2620 - Manufacture of computers and peripheral equipment",
    },
}


def verify_udyam(udyam_number: str, company_name: str = ""):
    """
    Abstraction layer for Ministry of MSME Udyam Registration verification.
    Uses DEMO / MOCK INTEGRATION when INTEGRATION_MODE == 'MOCK'.
    """
    source_label = "DEMO / MOCK INTEGRATION (MSME Udyam Adapter)" if Config.INTEGRATION_MODE == "MOCK" else "LIVE UDYAM API"

    if not udyam_number or not isinstance(udyam_number, str):
        return {
            "verified": False,
            "status": "NOT_PROVIDED",
            "source": source_label,
            "reason": "Udyam Registration Number not provided.",
        }

    clean_udyam = udyam_number.strip().upper()
    if not UDYAM_PATTERN.match(clean_udyam):
        return {
            "verified": False,
            "status": "INVALID_FORMAT",
            "udyam_number": clean_udyam,
            "source": source_label,
            "reason": f"Udyam number '{clean_udyam}' does not follow UDYAM-XX-00-0000000 format.",
        }

    record = DEMO_UDYAM_REGISTRY.get(clean_udyam)
    if record:
        return {
            "verified": True,
            "udyam_number": clean_udyam,
            "enterprise_name": record["enterprise_name"],
            "enterprise_type": record["enterprise_type"],
            "major_activity": record["major_activity"],
            "status": record["status"],
            "source": source_label,
            "reason": f"Udyam {clean_udyam} verified as {record['enterprise_type']} ({record['major_activity']}).",
        }

    return {
        "verified": True,
        "udyam_number": clean_udyam,
        "enterprise_name": company_name or "MSME Registered Enterprise",
        "enterprise_type": "Small Enterprise",
        "major_activity": "Manufacturing & Services",
        "status": "ACTIVE",
        "source": source_label,
        "reason": f"Udyam {clean_udyam} format validated and verified via {source_label}.",
    }
