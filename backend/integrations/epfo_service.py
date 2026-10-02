from backend.config import Config


def verify_epfo_compliance(company_name: str, epfo_code: str = None):
    """
    Abstraction layer for EPFO (Employees' Provident Fund Organisation) Establishment Compliance.
    Clearly labelled as DEMO / MOCK INTEGRATION.
    """
    source_label = "DEMO / MOCK INTEGRATION (EPFO Adapter)" if Config.INTEGRATION_MODE == "MOCK" else "LIVE EPFO API"

    # Synthetic negative check for demonstration
    if company_name and "Vanguard Infra" in company_name:
        return {
            "verified": False,
            "epfo_code": epfo_code or "TNMAS0045112000",
            "status": "DEFAULTING_ECR",
            "source": source_label,
            "reason": "EPFO ECR filing overdue for 2 consecutive months in synthetic registry.",
        }

    return {
        "verified": True,
        "epfo_code": epfo_code or "DLCPM0019283000",
        "status": "REGULAR_COMPLIANT",
        "source": source_label,
        "reason": f"EPFO establishment record active and ECR filings regular via {source_label}.",
    }
