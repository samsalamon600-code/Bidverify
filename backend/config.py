import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))

    # PostgreSQL primary database URL; automatic fallback check happens in app factory
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gem_compliance_db"
    )
    ALLOW_SQLITE_FALLBACK = os.getenv("ALLOW_SQLITE_FALLBACK", "true").lower() == "true"
    SQLITE_FALLBACK_URI = f"sqlite:///{os.path.join(BASE_DIR, 'gem_compliance.db')}"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports_output")
    MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "25"))
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = set(
        os.getenv("ALLOWED_EXTENSIONS", "pdf,png,jpg,jpeg,txt,doc,docx").split(",")
    )

    # EasyOCR & NLP Configuration
    PRIMARY_OCR_ENGINE = "EasyOCR"
    FALLBACK_OCR_ENGINE = "Direct Text Stream (PyPDF)"
    OCR_ENGINE = "EasyOCR"
    OCR_USE_GPU = os.getenv("OCR_USE_GPU", "false").lower() == "true"
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.60"))
    OCR_LANGUAGES = [lang.strip() for lang in os.getenv("OCR_LANGUAGES", "en").split(",") if lang.strip()]
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")

    # Configurable Compliance Scoring Weights
    COMPLIANCE_WEIGHTS = {
        "DOCUMENT": float(os.getenv("WEIGHT_DOCUMENT_COMPLIANCE", "0.25")),
        "STATUTORY": float(os.getenv("WEIGHT_STATUTORY_COMPLIANCE", "0.25")),
        "TECHNICAL": float(os.getenv("WEIGHT_TECHNICAL_COMPLIANCE", "0.30")),
        "TENDER": float(os.getenv("WEIGHT_TENDER_COMPLIANCE", "0.20")),
    }

    # External Government Integrations Mode
    INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "MOCK")
