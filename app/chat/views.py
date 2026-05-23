from django.http import JsonResponse
from chat.models import ChatRoom, User
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView
from .forms import RegistrationForm, LoginForm
from django.urls import reverse_lazy

class ChatView(TemplateView):
    template_name = "chat/index.html"

class RegisterView(FormView):
    form_class = RegistrationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy('view_chats')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class LoginView(FormView):
    form_class = LoginForm
    template_name = "auth/login.html"
    success_url = reverse_lazy('view_chats')

def list_rooms(request):
    rooms = list(ChatRoom.objects.values("id", "name"))
    return JsonResponse(rooms, safe=False)