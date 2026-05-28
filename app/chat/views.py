from django.http import JsonResponse
from chat.models import ChatRoom, User, RoomApplication
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from asgiref.sync import sync_to_async
from .forms import RegistrationForm, LoginForm, RoomCreationForm
from .services.rooms import (
    JOIN_ALREADY_MEMBER,
    JOIN_AUTH_REQUIRED,
    JOIN_FORBIDDEN,
    JOIN_NOT_FOUND,
    JOIN_OK,
    APPLICATION_REQUIRED,
    APPLICATION_PENDING,
    create_room,
    join_room_sync,
)
from .services.applications import (
    APP_ALREADY_MEMBER,
    APP_ALREADY_PENDING,
    APP_ALREADY_APPROVED,
    APP_AUTH_REQUIRED,
    APP_NOT_FOUND,
    APP_OK,
    apply_to_room_sync,
    review_application_sync,
)
from django.urls import reverse_lazy

class AsyncFormView(FormView):
    async def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        context = self.get_context_data(form=form)
        return await sync_to_async(self.render_to_response)(context)

    async def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if await sync_to_async(form.is_valid)():
            return await self.form_valid(form)
        return await self.form_invalid(form)

    async def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return await sync_to_async(self.render_to_response)(context)

    async def form_valid(self, form):
        return await sync_to_async(super().form_valid)(form)

    async def put(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

    async def patch(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

    async def delete(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

    async def head(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

    async def options(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

    async def trace(self, request, *args, **kwargs):
        return await sync_to_async(self.http_method_not_allowed)(request, *args, **kwargs)

class ChatView(TemplateView):
    template_name = "chat/index.html"

class RegisterView(AsyncFormView):
    form_class = RegistrationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy('view_chats')

    async def form_valid(self, form):
        await sync_to_async(form.save)()
        return await super().form_valid(form)

class LoginView(AsyncFormView):
    form_class = LoginForm
    template_name = "auth/login.html"
    success_url = reverse_lazy('view_chats')

    async def form_valid(self, form):
        user = await sync_to_async(authenticate)(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is None:
            form.add_error(None, "Invalid username or password.")
            return await self.form_invalid(form)

        await sync_to_async(login)(self.request, user)
        return await super().form_valid(form)

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

async def logout_user(request):
    await sync_to_async(logout)(request)
    return redirect('login')

async def add_room(request):
    room = await create_room("el-room")
    return redirect(reverse_lazy('view_chats'))

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
    room = ChatRoom.objects.filter(name=room_name).first()
    if not room:
        return JsonResponse({"error": "not_found"}, status=404)

    is_member = room.members.filter(pk=request.user.pk).exists()

    if room.room_type == ChatRoom.RoomTypes.PRIVATE and not is_member:
        return JsonResponse({"error": "forbidden"}, status=403)

    if not is_member:
        return JsonResponse({"error": "not_found"}, status=404)

    data = {
        "id": room.id,
        "name": room.name,
        "room_type": room.room_type,
        "owner": room.owner.username if room.owner else None,
        "members_data": list(room.memberships.values("user__username", "role")),
    }
    return JsonResponse(data)

@login_required
@require_POST
def leave_room_view(request, room_name):
    room = ChatRoom.objects.filter(name=room_name).first()
    if not room: return JsonResponse({"error": "not_found"}, status=404)

    if not room.members.filter(pk=request.user.pk).exists(): return JsonResponse({"error": "not_member"}, status=403)

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

    if status == JOIN_AUTH_REQUIRED:
        return JsonResponse({'error': 'auth_required'}, status=401)
    if status == JOIN_NOT_FOUND:
        return JsonResponse({'error': 'not_found'}, status=404)
    if status == JOIN_FORBIDDEN:
        return JsonResponse({'error': 'forbidden'}, status=403)
    if status == APPLICATION_REQUIRED:
        return JsonResponse({'warning': 'app_required'}, status=403)
    if status == APPLICATION_PENDING:
        return JsonResponse({'warning': 'app_pending'}, status=403)

    return JsonResponse({
        'name': room.name,
        'room_type': room.room_type,
        'joined': status in (JOIN_OK, JOIN_ALREADY_MEMBER),
        'already_member': status == JOIN_ALREADY_MEMBER,
    })


@login_required
@require_POST
def apply_to_room_view(request):
    room_name = request.POST.get("room_name", "").strip()
    app, status = apply_to_room_sync(room_name, request.user)

    if status == APP_AUTH_REQUIRED:
        return JsonResponse({"error": "auth_required"}, status=401)
    if status == APP_NOT_FOUND:
        return JsonResponse({"error": "not_found"}, status=404)
    if status == APP_ALREADY_MEMBER:
        return JsonResponse({"error": "already_member"}, status=400)
    if status == APP_ALREADY_APPROVED:
        return JsonResponse({"warning": "already_approved"}, status=200)
    if status == APP_ALREADY_PENDING:
        return JsonResponse({"warning": "already_pending"}, status=200)
    if status != APP_OK:
        return JsonResponse({"error": "unknown_error"}, status=400)

    return JsonResponse(
        {
            "id": app.id,
            "room": app.room.name,
            "status": app.status,
        },
        status=201,
    )


@login_required
@require_POST
def review_application_view(request, application_id: int):
    action = request.POST.get("action", "").strip().lower()
    if action not in ("approve", "reject"):
        return JsonResponse({"error": "invalid_action"}, status=400)

    approve = action == "approve"
    app, error = review_application_sync(application_id, request.user, approve)

    if error == APP_NOT_FOUND or app is None:
        return JsonResponse({"error": "not_found"}, status=404)
    if error == "forbidden":
        return JsonResponse({"error": "forbidden"}, status=403)

    return JsonResponse(
        {
            "id": app.id,
            "room": app.room.name,
            "status": app.status,
        }
    )


@login_required
def pending_applications_view(request):
    """Return pending applications for rooms owned by the current user."""
    apps = (
        RoomApplication.objects.filter(
            room__owner=request.user,
            status=RoomApplication.Status.PENDING,
        )
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