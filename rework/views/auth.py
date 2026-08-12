from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from asgiref.sync import sync_to_async

from chat.forms import RegistrationForm, LoginForm
from .base import AsyncFormView  # Relative import from base.py

class RegisterView(AsyncFormView):
    form_class = RegistrationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy('view_chats')

    async def form_valid(self, form):
        await sync_to_async(form.save)()
        user = await sync_to_async(authenticate)(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user:
            await sync_to_async(login)(self.request, user)
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

@login_required
async def logout_user(request):
    await sync_to_async(logout)(request)
    return redirect('login')