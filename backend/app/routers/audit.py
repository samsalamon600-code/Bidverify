import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models.models import AuditLog
from backend.app.schemas.schemas import AuditLogResponse

router = APIRouter(tags=["Audit Trail"])

@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_trail(
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if vendor_id:
        query = query.filter(AuditLog.vendor_id == vendor_id)

    logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    res = []
    for l in logs:
        details = None
        if l.details_json:
            try:
                details = json.loads(l.details_json)
            except Exception:
                details = {"raw": l.details_json}
        res.append(AuditLogResponse(
            id=l.id,
            user_email=l.user_email,
            vendor_id=l.vendor_id,
            vendor_name=l.vendor_name,
            action=l.action,
            details=details,
            timestamp=l.timestamp
        ))
    return res

@router.get("/vendors/{vendor_id}/audit", response_model=List[AuditLogResponse])
def get_vendor_audit_trail(vendor_id: int, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.vendor_id == vendor_id).order_by(desc(AuditLog.timestamp)).all()
    res = []
    for l in logs:
        details = None
        if l.details_json:
            try:
                details = json.loads(l.details_json)
            except Exception:
                details = {"raw": l.details_json}
        res.append(AuditLogResponse(
            id=l.id,
            user_email=l.user_email,
            vendor_id=l.vendor_id,
            vendor_name=l.vendor_name,
            action=l.action,
            details=details,
            timestamp=l.timestamp
        ))
    return res
