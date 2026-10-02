from backend.app.routers.auth import router as auth_router
from backend.app.routers.vendors import router as vendors_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.verification import router as verification_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.audit import router as audit_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.settings import router as settings_router

__all__ = [
    "auth_router", "vendors_router", "documents_router", "verification_router",
    "dashboard_router", "audit_router", "reports_router", "settings_router"
]
