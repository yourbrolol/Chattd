from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from asgiref.sync import sync_to_async

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

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = "chat/index.html"