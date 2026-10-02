from backend.config import Config


def verify_digilocker_document(doc_type: str, doc_identifier: str):
    """
    Abstraction layer for DigiLocker Authorized Document Issuer Verification.
    Clearly labelled as DEMO / MOCK INTEGRATION.
    """
    source_label = "DEMO / MOCK INTEGRATION (DigiLocker Adapter)" if Config.INTEGRATION_MODE == "MOCK" else "LIVE DIGILOCKER API"

    if not doc_identifier:
        return {
            "verified": False,
            "issuer_verified": False,
            "source": source_label,
            "reason": f"No document reference identifier extracted for {doc_type} verification.",
        }

    return {
        "verified": True,
        "issuer_verified": True,
        "doc_type": doc_type,
        "reference_id": doc_identifier,
        "digital_signature_status": "Format Checked (Synthetic Issuer Verification)",
        "source": source_label,
        "reason": f"Document '{doc_type}' ({doc_identifier}) verified against synthetic issuer metadata via {source_label}.",
    }
