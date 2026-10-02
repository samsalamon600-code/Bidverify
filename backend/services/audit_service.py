from flask import request
from backend.extensions import db
from backend.models.models import AuditLog


def record_audit_log(
    action: str,
    user=None,
    tender_id=None,
    bid_id=None,
    document_id=None,
    result_status="SUCCESS",
    review_comments=None,
    commit=True,
):
    """Records an immutable audit trail entry in the database."""
    ip_addr = "127.0.0.1"
    try:
        if request:
            ip_addr = request.remote_addr or "127.0.0.1"
    except RuntimeError:
        pass

    user_id = user.id if user else None
    user_name = user.full_name if user else "System Automated Pipeline"
    user_role = user.role_name if user else "SYSTEM"

    log_entry = AuditLog(
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        action=action,
        tender_id=tender_id,
        bid_id=bid_id,
        document_id=document_id,
        result_status=result_status,
        review_comments=review_comments,
        ip_address=ip_addr,
    )
    db.session.add(log_entry)
    if commit:
        db.session.commit()
    return log_entry
