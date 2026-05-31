from django.urls import path
from .views import base, auth, users, rooms, applications

urlpatterns = [
    # 1. Base/Core Views
    path('', base.ChatView.as_view(), name='view_chats'),
    
    # 2. Authentication Views
    path('register/', auth.RegisterView.as_view(), name='register'),
    path('login/', auth.LoginView.as_view(), name='login'),
    path('logout/', auth.logout_user, name='logout'),
    
    # 3. User Views
    path('api/users/<int:user_id>/', users.user_get, name='user_get'),
    path('settings/edit/', users.settings_edit, name='settings_edit'), # Added missing trailing slash
    
    # 4. Static Room & Application Views (Must come BEFORE dynamic room_name paths)
    path("rooms/", rooms.list_rooms, name="list_rooms"),
    path("rooms/join/", rooms.join_room_view, name="join_room"),
    path("rooms/create/", rooms.RoomCreationView.as_view(), name="create_room"), # Added missing trailing slash
    path("rooms/apply/", applications.apply_to_room_view, name="apply_to_room"),
    path('rooms/search/', rooms.search_rooms_view, name='room_search'),
    path("rooms/applications/pending/", applications.pending_applications_view, name="pending_applications"),
    path("rooms/applications/<int:application_id>/review/", applications.review_application_view, name="review_application"),
    
    # 5. Dynamic/Parameterized Room Views (Catch-all patterns at the bottom)
    path("rooms/<str:room_name>/", rooms.room_details, name="room_detail"),
    path("rooms/<str:room_name>/leave/", rooms.leave_room_view, name="leave_room"),
    path("rooms/<str:room_name>/delete/", rooms.delete_room_view, name="delete_room"),
    path('rooms/<str:room_name>/applications/', applications.room_pending_applications_view, name='room_pending_applications'),
]