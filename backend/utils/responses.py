from flask import jsonify


def api_success(data=None, message="Success", status_code=200):
    payload = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def api_error(message="An unexpected error occurred", error_code="INTERNAL_ERROR", status_code=400, details=None):
    payload = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code
