from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path('', views.ChatView.as_view(), name='view_chats'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.RegisterView.as_view(), name='login'),
    path("rooms/", views.list_rooms, name="list_rooms")
]