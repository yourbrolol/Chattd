from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class ChatRoom(models.Model):
    class RoomTypes(models.TextChoices):
        PUBLIC = 'PUBLIC'
        UNLISTED = 'UNLISTED'
        PRIVATE = 'PRIVATE'

    name = models.CharField(max_length=20, unique=True)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="owned_chatrooms")
    room_type = models.CharField(max_length=10, choices=RoomTypes.choices, default=RoomTypes.PUBLIC)
    whitelisted = models.ManyToManyField(User, blank=True, related_name="whitelisted_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.room}] {self.content[:30]}"