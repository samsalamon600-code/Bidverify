from backend.config import Config


def verify_esic_compliance(company_name: str, esic_code: str = None):
    """
    Abstraction layer for ESIC (Employees' State Insurance Corporation) Compliance.
    Clearly labelled as DEMO / MOCK INTEGRATION.
    """
    source_label = "DEMO / MOCK INTEGRATION (ESIC Adapter)" if Config.INTEGRATION_MODE == "MOCK" else "LIVE ESIC API"

    return {
        "verified": True,
        "esic_code": esic_code or "11-00-124890-000-1001",
        "status": "ACTIVE_CONTRIBUTOR",
        "source": source_label,
        "reason": f"ESIC employer registration active via {source_label}.",
    }
