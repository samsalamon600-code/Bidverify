from flask import Blueprint, request
from backend.models.models import AuditLog
from backend.auth.decorators import jwt_required
from backend.utils.responses import api_success

audit_bp = Blueprint("audit_bp", __name__)


@audit_bp.route("/api/audit-logs", methods=["GET"])
@jwt_required(allowed_roles=["PROCUREMENT_OFFICER"])
def list_audit_logs():
    bid_id = request.args.get("bid_id", type=int)
    tender_id = request.args.get("tender_id", type=int)
    action_filter = request.args.get("action")
    limit = request.args.get("limit", default=100, type=int)

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if bid_id:
        query = query.filter_by(bid_id=bid_id)
    if tender_id:
        query = query.filter_by(tender_id=tender_id)
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    logs = query.limit(limit).all()
    return api_success({
        "audit_logs": [lg.to_dict() for lg in logs],
        "total": len(logs),
    })
