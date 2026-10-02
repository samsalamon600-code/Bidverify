import os
import re
from werkzeug.utils import secure_filename
from backend.config import Config

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
UDYAM_REGEX = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_file_upload(file_storage, existing_filenames=None):
    """
    Validates uploaded file for:
    - Non-empty filename
    - Allowed file extension
    - Non-empty content (0 bytes check)
    - Max file size restriction
    - Duplicate filename check within the same bid
    Returns (is_valid, error_message, error_code, safe_name, ext, size_bytes)
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided or empty filename", "MISSING_FILE", None, None, 0

    original_name = file_storage.filename.strip()
    safe_name = secure_filename(original_name)
    if not safe_name or "." not in safe_name:
        return False, f"Invalid filename: {original_name}", "INVALID_FILENAME", None, None, 0

    ext = safe_name.rsplit(".", 1)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return (
            False,
            f"Invalid document format '.{ext}'. Allowed formats: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}",
            "INVALID_FILE_TYPE",
            None,
            None,
            0,
        )

    if existing_filenames and original_name.lower() in {f.lower() for f in existing_filenames}:
        return (
            False,
            f"Duplicate filename detected: '{original_name}' has already been uploaded for this bid.",
            "DUPLICATE_FILENAME",
            None,
            None,
            0,
        )

    # Check file size by seeking to end
    file_storage.stream.seek(0, os.SEEK_END)
    size_bytes = file_storage.stream.tell()
    file_storage.stream.seek(0)

    if size_bytes == 0:
        return False, f"Uploaded file '{original_name}' is empty (0 bytes).", "EMPTY_FILE", None, None, 0

    if size_bytes > Config.MAX_CONTENT_LENGTH:
        return (
            False,
            f"File '{original_name}' exceeds maximum size of {Config.MAX_CONTENT_LENGTH_MB} MB.",
            "FILE_TOO_LARGE",
            None,
            None,
            size_bytes,
        )

    return True, "Valid file", None, safe_name, ext, size_bytes


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validates password criteria:
    1. Must contain >= 4 characters
    2. Must contain at least 1 symbol
    3. Overall must contain <= 8 characters
    """
    if not password or not isinstance(password, str):
        return False, "Password cannot be empty."
    if len(password) < 4:
        return False, "Password must contain at least 4 characters."
    if len(password) > 8:
        return False, "Password must not exceed 8 characters."
    if not re.search(r"[^a-zA-Z0-9\s]", password):
        return False, "Password must contain at least 1 symbol (e.g. @, #, $, %, etc.)."
    return True, ""
