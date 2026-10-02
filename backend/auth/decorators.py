from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import request, g
from backend.config import Config
from backend.extensions import db
from backend.models.models import User
from backend.utils.responses import api_error

# In-memory token blocklist for logged-out tokens
REVOKED_TOKENS = set()


def generate_jwt_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role_name,
        "iat": now,
        "exp": now + timedelta(hours=Config.JWT_ACCESS_TOKEN_EXPIRES_HOURS),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def decode_jwt_token(token: str):
    if token in REVOKED_TOKENS:
        raise jwt.InvalidTokenError("Token has been revoked (logged out)")
    return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])


def extract_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    # Also support query param ?token= for direct PDF report downloads in browser
    token_param = request.args.get("token", "").strip()
    if token_param:
        return token_param
    return None


def jwt_required(allowed_roles=None):
    """
    Decorator for JWT authentication and role-based authorization.
    allowed_roles: None (any authenticated user) or list/tuple of roles e.g. ["PROCUREMENT_OFFICER"]
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = extract_bearer_token()
            if not token:
                return api_error(
                    "Authentication token is missing. Please log in.",
                    error_code="MISSING_TOKEN",
                    status_code=401,
                )
            try:
                payload = decode_jwt_token(token)
            except jwt.ExpiredSignatureError:
                return api_error(
                    "Authentication token has expired. Please log in again.",
                    error_code="TOKEN_EXPIRED",
                    status_code=401,
                )
            except jwt.InvalidTokenError as exc:
                return api_error(
                    f"Invalid authentication token: {str(exc)}",
                    error_code="INVALID_TOKEN",
                    status_code=401,
                )

            user_id = payload.get("user_id")
            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return api_error(
                    "User account not found or inactive.",
                    error_code="USER_NOT_FOUND",
                    status_code=401,
                )

            if allowed_roles and user.role_name not in allowed_roles:
                return api_error(
                    f"Unauthorized access. Role '{user.role_name}' cannot access this resource. Required: {', '.join(allowed_roles)}",
                    error_code="UNAUTHORIZED_ROLE",
                    status_code=403,
                )

            g.current_user = user
            g.current_token = token
            return fn(*args, **kwargs)

        return wrapper
    return decorator
