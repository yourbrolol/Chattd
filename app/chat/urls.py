from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChatView.as_view(), name='view_chats'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path("rooms/", views.list_rooms, name="list_rooms"),
    path("rooms/join/", views.join_room_view, name="join_room"),
    path("rooms/create", views.RoomCreationView.as_view(), name="create_room"),
    path("rooms/apply/", views.apply_to_room_view, name="apply_to_room"),
    path("rooms/applications/<int:application_id>/review/", views.review_application_view, name="review_application"),
    path("rooms/applications/pending/", views.pending_applications_view, name="pending_applications"),
]