from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.db.models import Q

from chat.models import ChatRoom
from chat.forms import RoomCreationForm
from .base import AsyncFormView
from chat.services.rooms import (
    create_room,
    join_room_sync,
    get_room_details_sync,
    JOIN_AUTH_REQUIRED,
    JOIN_NOT_FOUND,
    JOIN_FORBIDDEN,
    APPLICATION_REQUIRED,
    APPLICATION_PENDING,
    JOIN_OK,
    JOIN_ALREADY_MEMBER,
    ROOM_NOT_FOUND,
    ROOM_FORBIDDEN,
    ROOM_NOT_MEMBER,
)

class RoomCreationView(AsyncFormView):
    form_class = RoomCreationForm
    template_name = "rooms/new_room.html"
    success_url = reverse_lazy('view_chats')

    async def form_valid(self, form):
        room_name = form.cleaned_data['room_name']
        if room_name == '':
            form.add_error('room_name', "Room name cannot be empty.")
            return await self.form_invalid(form)

        await create_room(room_name, self.request.user, form.cleaned_data['room_type'])
        return await super().form_valid(form)

@login_required
def search_rooms_view(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"public_rooms": [], "joined_rooms": []})

    joined_rooms = ChatRoom.objects.filter(
        memberships__user=request.user,
        name__icontains=query
    ).distinct()[:10]

    public_rooms = ChatRoom.objects.filter(
        room_type=ChatRoom.RoomTypes.PUBLIC,
        name__icontains=query
    ).exclude(
        memberships__user=request.user
    ).distinct()[:10]

    data = {
        "joined_rooms": [{"name": r.name, "is_public": r.room_type == ChatRoom.RoomTypes.PUBLIC} for r in joined_rooms],
        "public_rooms": [{"name": r.name} for r in public_rooms],
    }
    return JsonResponse(data)

@login_required
def list_rooms(request):
    rooms = list(
        ChatRoom.objects.filter(memberships__user=request.user)
        .values("id", "name", "room_type")
        .distinct()
    )
    return JsonResponse(rooms, safe=False)

@login_required
def room_details(request, room_name):
    data, status = get_room_details_sync(room_name, request.user)
    if status == ROOM_NOT_FOUND:
        return JsonResponse({"error": "not_found"}, status=404)
    if status == ROOM_FORBIDDEN:
        return JsonResponse({"error": "forbidden"}, status=403)
    if status == ROOM_NOT_MEMBER:
        return JsonResponse({"error": "not_member"}, status=403)
    return JsonResponse(data)

@login_required
@require_POST
def leave_room_view(request, room_name):
    room = ChatRoom.objects.filter(name=room_name).first()
    if not room: return JsonResponse({"error": "not_found"}, status=404)
    if not room.members.filter(pk=request.user.pk).exists(): 
        return JsonResponse({"error": "not_member"}, status=403)
    room.members.remove(request.user)
    return JsonResponse({"message": "left_room"})

@login_required
@require_POST
def delete_room_view(request, room_name):
    room = ChatRoom.objects.filter(name=room_name).first()
    if not room: return JsonResponse({"error": "not_found"}, status=404)
    if room.owner_id != request.user.pk: return JsonResponse({"error": "forbidden"}, status=403)
    room.delete()
    return JsonResponse({"message": "room_deleted"})

@login_required
@require_POST
def join_room_view(request):
    room_name = request.POST.get('room_name', '').strip()
    room, status = join_room_sync(room_name, request.user)

    if status == JOIN_AUTH_REQUIRED: return JsonResponse({'error': 'auth_required'}, status=401)
    if status == JOIN_NOT_FOUND: return JsonResponse({'error': 'not_found'}, status=404)
    if status == JOIN_FORBIDDEN: return JsonResponse({'error': 'forbidden'}, status=403)
    if status == APPLICATION_REQUIRED: return JsonResponse({'warning': 'app_required'}, status=403)
    if status == APPLICATION_PENDING: return JsonResponse({'warning': 'app_pending'}, status=403)

    return JsonResponse({
        'name': room.name,
        'room_type': room.room_type,
        'joined': status in (JOIN_OK, JOIN_ALREADY_MEMBER),
        'already_member': status == JOIN_ALREADY_MEMBER,
    })