from backend.config import Config

# Synthetic public watchlist / debarment list for SIH demonstration
DEMO_WATCHLIST = {
    "33AABCV4321F1Z9": {
        "reason": "Flagged on GeM Incident Watchlist for past delivery default (Requires Procurement Officer Review).",
        "status": "WATCHLIST_ALERT",
    }
}


def check_debarment_status(gstin: str, pan: str, company_name: str):
    """
    Checks permitted public/authoritative debarment & incident lists.
    Clearly labelled as DEMO / MOCK INTEGRATION.
    """
    source_label = (
        "DEMO / MOCK INTEGRATION (GeM / DoE Public Debarment List Adapter)"
        if Config.INTEGRATION_MODE == "MOCK"
        else "LIVE DEBARMENT WATCHLIST API"
    )

    clean_gstin = (gstin or "").strip().upper()
    if clean_gstin in DEMO_WATCHLIST:
        entry = DEMO_WATCHLIST[clean_gstin]
        return {
            "clear": False,
            "status": entry["status"],
            "source": source_label,
            "reason": f"{entry['reason']} [{source_label}]",
        }

    return {
        "clear": True,
        "status": "NO_ADVERSE_RECORD",
        "source": source_label,
        "reason": f"No active debarment or blacklisting record found for {company_name or clean_gstin} via {source_label}.",
    }
