import os
import sys

# Prevent OpenMP multiple runtime conflict on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, send_from_directory, request
from sqlalchemy import create_engine, text

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import Config
from backend.extensions import db
from backend.routes import ALL_BLUEPRINTS
from backend.utils.responses import api_error, api_success
from backend.seed_demo import seed_demo_data


def _resolve_database_uri(app_config) -> str:
    """
    Attempts to connect to the configured PostgreSQL DATABASE_URL.
    If PostgreSQL is not running locally and ALLOW_SQLITE_FALLBACK is true,
    transparently falls back to SQLite so the prototype runs out-of-the-box.
    """
    primary_uri = app_config.get("SQLALCHEMY_DATABASE_URI") or Config.DATABASE_URL
    if primary_uri.startswith("sqlite"):
        return primary_uri

    try:
        engine = create_engine(primary_uri, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return primary_uri
    except Exception:
        if Config.ALLOW_SQLITE_FALLBACK:
            return Config.SQLITE_FALLBACK_URI
        return primary_uri


def _auto_migrate_sqlite_schema(app):
    """Automatically adds any missing columns to SQLite tables on startup."""
    with app.app_context():
        engine = db.engine
        if "sqlite" in str(engine.url):
            from sqlalchemy import inspect, text
            try:
                inspector = inspect(engine)
                for table_name, table in db.metadata.tables.items():
                    if inspector.has_table(table_name):
                        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                        for col in table.columns:
                            if col.name not in existing_cols:
                                col_type = col.type.compile(engine.dialect)
                                default_clause = ""
                                if col.default is not None and hasattr(col.default, "arg"):
                                    if isinstance(col.default.arg, (int, float)):
                                        default_clause = f" DEFAULT {col.default.arg}"
                                    elif isinstance(col.default.arg, str):
                                        default_clause = f" DEFAULT '{col.default.arg}'"
                                with engine.connect() as conn:
                                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"))
                                    conn.commit()
            except Exception:
                pass


def create_app(test_config=None):
    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = _resolve_database_uri(app.config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)

    db.init_app(app)
    _auto_migrate_sqlite_schema(app)

    # Register CORS headers on all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return "", 204

    # Register REST API Blueprints
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # System Health & Metadata Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        db_engine = "PostgreSQL" if "postgresql" in db_uri else "SQLite (PostgreSQL Compatible ORM Mode)"
        return api_success({
            "platform": "AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement",
            "problem_statement": "SIH26100",
            "decision_support_only": True,
            "database_engine": db_engine,
            "ocr_primary": Config.PRIMARY_OCR_ENGINE,
            "ocr_fallback": Config.FALLBACK_OCR_ENGINE,
            "ml_engine": "Scikit-learn IsolationForest",
            "integration_mode": Config.INTEGRATION_MODE,
            "compliance_weights": Config.COMPLIANCE_WEIGHTS,
        })

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(err):
        if request.path.startswith("/api/"):
            return api_error("Requested API endpoint not found.", "ENDPOINT_NOT_FOUND", 404)
        return send_from_directory(frontend_dir, "index.html")

    @app.errorhandler(413)
    def request_entity_too_large(err):
        return api_error(
            f"Uploaded file exceeds the maximum allowed limit of {Config.MAX_CONTENT_LENGTH_MB} MB.",
            "FILE_TOO_LARGE",
            413,
        )

    @app.errorhandler(500)
    def internal_server_error(err):
        return api_error("Internal server error occurred.", "DATABASE_OR_SERVER_FAILURE", 500)

    # Frontend Static File Serving
    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def serve_static_pages(filename):
        target = os.path.join(frontend_dir, filename)
        if os.path.isfile(target):
            return send_from_directory(frontend_dir, filename)
        if os.path.isfile(target + ".html"):
            return send_from_directory(frontend_dir, filename + ".html")
        return send_from_directory(frontend_dir, "index.html")

    with app.app_context():
        db.create_all()
        try:
            from backend.models.models import Tender
            if Tender.query.count() == 0:
                from backend.seed_tender_data import seed_procurement_data
                seed_procurement_data()
        except Exception as seed_err:
            print(f"Auto-seed check: {seed_err}")

    return app


if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", "5000"))
    application.run(host="0.0.0.0", port=port, debug=True)
