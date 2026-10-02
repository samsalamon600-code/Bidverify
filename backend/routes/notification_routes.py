from flask import Blueprint, request, g
from backend.extensions import db
from backend.models.models import Notification, Tender
from backend.auth.decorators import jwt_required
from backend.utils.responses import api_success, api_error

notification_bp = Blueprint("notification_bp", __name__, url_prefix="/api/notifications")


@notification_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user = g.current_user
    # Fetch notifications targeted to this user specifically, or to their role, or broadcast to ALL
    query = Notification.query.filter(
        db.or_(
            Notification.user_id == user.id,
            Notification.role == user.role_name,
            Notification.role == "ALL",
        )
    ).order_by(Notification.created_at.desc())

    notifications = query.limit(40).all()
    unread_count = sum(1 for n in notifications if not n.is_read)

    return api_success({
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": unread_count,
        "total": len(notifications),
    })


@notification_bp.route("/<int:notification_id>/read", methods=["POST", "PUT"])
@jwt_required()
def mark_read(notification_id):
    notif = db.session.get(Notification, notification_id)
    if not notif:
        return api_error("Notification not found.", "INVALID_NOTIFICATION", 404)

    notif.is_read = True
    db.session.commit()
    return api_success({"id": notif.id, "is_read": True}, message="Notification marked as read.")


@notification_bp.route("/mark-all-read", methods=["POST"])
@jwt_required()
def mark_all_read():
    user = g.current_user
    notifications = Notification.query.filter(
        db.or_(
            Notification.user_id == user.id,
            Notification.role == user.role_name,
            Notification.role == "ALL",
        ),
        Notification.is_read == False
    ).all()

    for n in notifications:
        n.is_read = True
    db.session.commit()
    return api_success({"marked_count": len(notifications)}, message="All notifications marked as read.")
