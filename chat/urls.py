from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path('', lambda request: render(request, 'chat/index.html')),
    path("rooms/", views.list_rooms, name="list_rooms")
]