import logging

from django.db import IntegrityError, transaction

from chat.models import ChatRoom, RoomMembership, RoomApplication

logger = logging.getLogger(__name__)

APP_OK = "ok"
APP_ALREADY_MEMBER = "already_member"
APP_NOT_FOUND = "not_found"
APP_AUTH_REQUIRED = "auth_required"
APP_ALREADY_PENDING = "already_pending"
APP_ALREADY_APPROVED = "already_approved"


def apply_to_room_sync(room_name, user):
    """
    Create or reuse a RoomApplication for the given room and user.

    Returns (application | None, status_code).
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None, APP_AUTH_REQUIRED

    room_name = (room_name or "").strip()
    if not room_name:
        return None, APP_NOT_FOUND

    try:
        room = ChatRoom.objects.get(name=room_name)
    except ChatRoom.DoesNotExist:
        return None, APP_NOT_FOUND

    if RoomMembership.objects.filter(room=room, user=user).exists():
        return None, APP_ALREADY_MEMBER

    try:
        with transaction.atomic():
            app, created = RoomApplication.objects.select_for_update().get_or_create(
                applicant=user,
                room=room,
                defaults={"status": RoomApplication.Status.PENDING},
            )

            if not created:
                if app.status == RoomApplication.Status.APPROVED:
                    return app, APP_ALREADY_APPROVED
                if app.status == RoomApplication.Status.PENDING:
                    return app, APP_ALREADY_PENDING

                # Previously rejected – let the user re-apply by resetting to PENDING.
                if app.status == RoomApplication.Status.REJECTED:
                    app.status = RoomApplication.Status.PENDING
                    app.save(update_fields=["status"])

    except IntegrityError:
        logger.exception("apply_to_room_sync: integrity error while creating application")
        return None, "error"

    return app, APP_OK


def review_application_sync(application_id, acting_user, approve: bool, auto_create_membership=True):
    """
    Approve or reject a RoomApplication.

    Only the room owner (or a future admin role) may review.
    Returns (application | None, error_code | None).
    """
    try:
        app = RoomApplication.objects.select_related("room", "applicant").get(pk=application_id)
    except RoomApplication.DoesNotExist:
        return None, APP_NOT_FOUND

    room = app.room
    is_owner = room.owner_id == getattr(acting_user, "id", None)
    if not is_owner:
        return None, "forbidden"

    new_status = RoomApplication.Status.APPROVED if approve else RoomApplication.Status.REJECTED

    if app.status == new_status:
        return app, None

    app.status = new_status
    app.save(update_fields=["status"])

    if auto_create_membership and approve:
        RoomMembership.objects.get_or_create(user=app.applicant, room=app.room)

    return app, None

