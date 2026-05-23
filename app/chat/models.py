from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    username = models.CharField(max_length=20, unique=True, null=False, blank=False, default="qwerty")
    avatar = models.ImageField(upload_to='photos/avatars/')
    USERNAME_FIELD = 'username'

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
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