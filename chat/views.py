from django.http import JsonResponse
from chat.models import ChatRoom, User
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView
from .forms import UserForm
from django.urls import reverse_lazy

class ChatView(TemplateView):
    template_name = "chat/index.html"

class RegisterView(CreateView):
    model = User
    form_class = UserForm
    template_name = "auth/register.html"
    success_url = reverse_lazy('')

class LoginView(FormView):
    model = User
    form_class = UserForm
    template_name = "auth/register.html"
    success_url = reverse_lazy('')

def list_rooms(request):
    rooms = list(ChatRoom.objects.values("id", "name"))
    return JsonResponse(rooms, safe=False)