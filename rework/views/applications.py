from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from chat.models import ChatRoom, RoomApplication

from chat.models import RoomApplication
from chat.services.applications import (
    apply_to_room_sync,
    review_application_sync,
    APP_AUTH_REQUIRED,
    APP_NOT_FOUND,
    APP_ALREADY_MEMBER,
    APP_ALREADY_APPROVED,
    APP_ALREADY_PENDING,
    APP_OK,
)

@login_required
@require_POST
def apply_to_room_view(request):
    room_name = request.POST.get("room_name", "").strip()
    app, status = apply_to_room_sync(room_name, request.user)

    if status == APP_AUTH_REQUIRED: return JsonResponse({"error": "auth_required"}, status=401)
    if status == APP_NOT_FOUND: return JsonResponse({"error": "not_found"}, status=404)
    if status == APP_ALREADY_MEMBER: return JsonResponse({"error": "already_member"}, status=400)
    if status == APP_ALREADY_APPROVED: return JsonResponse({"warning": "already_approved"}, status=200)
    if status == APP_ALREADY_PENDING: return JsonResponse({"warning": "already_pending"}, status=200)
    if status != APP_OK: return JsonResponse({"error": "unknown_error"}, status=400)

    return JsonResponse({"id": app.id, "room": app.room.name, "status": app.status}, status=201)

@login_required
@require_POST
def review_application_view(request, application_id: int):
    action = request.POST.get("action", "").strip().lower()
    if action not in ("approve", "reject"): return JsonResponse({"error": "invalid_action"}, status=400)

    approve = action == "approve"
    app, error = review_application_sync(application_id, request.user, approve)

    if error == APP_NOT_FOUND or app is None: return JsonResponse({"error": "not_found"}, status=404)
    if error == "forbidden": return JsonResponse({"error": "forbidden"}, status=403)

    return JsonResponse({"id": app.id, "room": app.room.name, "status": app.status})

@login_required
def pending_applications_view(request):
    apps = (
        RoomApplication.objects.filter(room__owner=request.user, status=RoomApplication.Status.PENDING)
        .select_related("applicant", "room")
        .order_by("created_at")
    )
    data = [
        {
            "id": a.id,
            "room": a.room.name,
            "applicant": a.applicant.username if a.applicant else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]
    return JsonResponse(data, safe=False)

@login_required
def room_pending_applications_view(request, room_name: str):
    """
    Fetch pending applications specifically for a single room.
    Only allows access if the requesting user is the room owner.
    """
    room = get_object_or_404(ChatRoom, name=room_name)
    if room.owner != request.user:
        return JsonResponse({"error": "forbidden"}, status=403)

    apps = (
        RoomApplication.objects.filter(room=room, status=RoomApplication.Status.PENDING)
        .select_related("applicant")
        .order_by("created_at")
    )
    
    data = [
        {
            "id": a.id,
            "room": room.name,
            "applicant": a.applicant.username if a.applicant else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]
    return JsonResponse(data, safe=False)