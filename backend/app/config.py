import os

class Settings:
    PROJECT_NAME: str = "Bidverify - AI Vendor Compliance & Risk Engine"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-procurement-key-for-jwt-bidverify-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./bidverify.db")

    # Storage paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_ROOT: str = os.path.dirname(BASE_DIR)
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(PROJECT_ROOT, "uploads"))
    REPORT_DIR: str = os.getenv("REPORT_DIR", os.path.join(PROJECT_ROOT, "reports"))

    # Scoring Weights (Configurable)
    WEIGHT_IDENTITY_MISMATCH: float = 0.25
    WEIGHT_DOCUMENT_ISSUES: float = 0.20
    WEIGHT_REGISTRATION_ISSUES: float = 0.20
    WEIGHT_ADDRESS_MISMATCH: float = 0.15
    WEIGHT_ML_ANOMALY: float = 0.10
    WEIGHT_MISSING_INFO: float = 0.10

    # Compliance Weights
    COMPLIANCE_REQ_DOCS: float = 0.20
    COMPLIANCE_IDENTITY: float = 0.20
    COMPLIANCE_REGISTRATION: float = 0.20
    COMPLIANCE_NAME_MATCH: float = 0.15
    COMPLIANCE_ADDRESS_MATCH: float = 0.10
    COMPLIANCE_DOC_VALIDITY: float = 0.15

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
