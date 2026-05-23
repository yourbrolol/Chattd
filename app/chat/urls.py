from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChatView.as_view(), name='view_chats'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path("rooms/", views.list_rooms, name="list_rooms")
]