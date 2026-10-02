from flask import Blueprint, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db
from backend.models.models import Role, User, Officer, Company
from backend.auth.decorators import generate_jwt_token, jwt_required, REVOKED_TOKENS
from backend.services.audit_service import record_audit_log
from backend.utils.responses import api_success, api_error
from backend.utils.validators import validate_email, validate_password

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role_name = (data.get("role") or "COMPANY").strip().upper()

    if not validate_email(email):
        return api_error("Please provide a valid email address.", "INVALID_EMAIL", 400)
    is_valid_pw, pw_err = validate_password(password)
    if not is_valid_pw:
        return api_error(pw_err, "INVALID_PASSWORD_POLICY", 400)
    if not full_name:
        return api_error("Full name is required.", "MISSING_NAME", 400)
    if role_name not in ("PROCUREMENT_OFFICER", "COMPANY"):
        return api_error("Invalid role. Must be PROCUREMENT_OFFICER or COMPANY.", "INVALID_ROLE", 400)

    if User.query.filter_by(email=email).first():
        return api_error("An account with this email already exists.", "EMAIL_ALREADY_EXISTS", 409)

    role_obj = Role.query.filter_by(name=role_name).first()
    if not role_obj:
        role_obj = Role(name=role_name, description=f"{role_name} Role")
        db.session.add(role_obj)
        db.session.flush()

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        role_id=role_obj.id,
        role_name=role_name,
    )
    db.session.add(user)
    db.session.flush()

    if role_name == "PROCUREMENT_OFFICER":
        emp_id = (data.get("employee_id") or f"GEM-OFF-{user.id:04d}").strip()
        if Officer.query.filter_by(employee_id=emp_id).first():
            emp_id = f"{emp_id}-{user.id}"
        officer = Officer(
            user_id=user.id,
            employee_id=emp_id,
            department=(data.get("department") or "Central Procurement Division").strip(),
            designation=(data.get("designation") or "Senior Procurement Officer").strip(),
            ministry=(data.get("ministry") or "Ministry of Commerce & Industry (GeM)").strip(),
            phone=(data.get("phone") or "+91-11-23061000").strip(),
        )
        db.session.add(officer)
    else:
        company = Company(
            user_id=user.id,
            company_name=(data.get("company_name") or f"{full_name} Enterprises Pvt. Ltd.").strip(),
            registration_number=(data.get("registration_number") or f"U72200DL2020PTC{100000 + user.id}").strip(),
            gstin=(data.get("gstin") or "07AABCA1234C1Z5").strip().upper(),
            pan=(data.get("pan") or "AABCA1234C").strip().upper(),
            udyam_number=(data.get("udyam_number") or "UDYAM-DL-01-0012345").strip().upper(),
            enterprise_type=(data.get("enterprise_type") or "Small Enterprise").strip(),
            incorporation_year=int(data.get("incorporation_year") or 2019),
            local_content_percent=float(data.get("local_content_percent") or 65.0),
            address=(data.get("address") or "Plot 42, Industrial Area, New Delhi").strip(),
            contact_phone=(data.get("phone") or "+91-9810012345").strip(),
            is_msme=bool(data.get("is_msme", True)),
            is_startup=bool(data.get("is_startup", False)),
        )
        db.session.add(company)

    db.session.commit()
    record_audit_log("User Registered", user=user, result_status="SUCCESS")

    token = generate_jwt_token(user)
    return api_success(
        {"token": token, "user": user.to_dict()},
        message="Registration completed successfully.",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return api_error("Email and password are required.", "MISSING_CREDENTIALS", 400)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return api_error("Invalid email or password.", "INVALID_CREDENTIALS", 401)

    if not user.is_active:
        return api_error("This account has been deactivated.", "ACCOUNT_INACTIVE", 403)

    token = generate_jwt_token(user)
    record_audit_log("User Logged In", user=user, result_status="SUCCESS")

    return api_success(
        {"token": token, "user": user.to_dict()},
        message="Login successful.",
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    token = getattr(g, "current_token", None)
    if token:
        REVOKED_TOKENS.add(token)
    record_audit_log("User Logged Out", user=g.current_user, result_status="SUCCESS")
    return api_success(message="Logged out successfully.")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    return api_success({"user": g.current_user.to_dict()})


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = g.current_user
    data = request.get_json(silent=True) or {}

    if data.get("full_name"):
        user.full_name = data["full_name"].strip()

    if user.role_name == "PROCUREMENT_OFFICER" and user.officer_profile:
        prof = user.officer_profile
        for field in ("department", "designation", "ministry", "phone"):
            if field in data and data[field] is not None:
                setattr(prof, field, str(data[field]).strip())

    elif user.role_name == "COMPANY" and user.company_profile:
        comp = user.company_profile
        for field in (
            "company_name",
            "registration_number",
            "gstin",
            "pan",
            "udyam_number",
            "enterprise_type",
            "address",
            "contact_phone",
        ):
            if field in data and data[field] is not None:
                val = str(data[field]).strip()
                if field in ("gstin", "pan", "udyam_number"):
                    val = val.upper()
                setattr(comp, field, val)
        if "local_content_percent" in data:
            comp.local_content_percent = float(data["local_content_percent"] or 0.0)
        if "incorporation_year" in data:
            comp.incorporation_year = int(data["incorporation_year"] or 2018)
        if "is_msme" in data:
            comp.is_msme = bool(data["is_msme"])
        if "is_startup" in data:
            comp.is_startup = bool(data["is_startup"])

    db.session.commit()
    record_audit_log("Profile Updated", user=user, result_status="SUCCESS")
    return api_success({"user": user.to_dict()}, message="Profile updated successfully.")
