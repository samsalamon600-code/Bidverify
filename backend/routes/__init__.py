from backend.routes.auth_routes import auth_bp
from backend.routes.tender_routes import tender_bp
from backend.routes.bid_routes import bid_bp
from backend.routes.document_routes import document_bp
from backend.routes.compliance_routes import compliance_bp
from backend.routes.report_routes import report_bp
from backend.routes.audit_routes import audit_bp
from backend.routes.notification_routes import notification_bp

ALL_BLUEPRINTS = [
    auth_bp,
    tender_bp,
    bid_bp,
    document_bp,
    compliance_bp,
    report_bp,
    audit_bp,
    notification_bp,
]

