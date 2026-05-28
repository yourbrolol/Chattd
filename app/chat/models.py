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

class RoomMembership(models.Model):
    """Through model for room membership with per-user roles."""

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        MEMBER = 'member', 'Member'
        MODERATOR = 'moderator', 'Moderator'
        ADMIN = 'admin', 'Admin'

    room = models.ForeignKey(
        'ChatRoom',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='room_memberships',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_room_user_membership',
            ),
        ]

    def __str__(self):
        username = self.user.username if self.user else '(deleted user)'
        return f"{username} in {self.room.name} ({self.role})"

class ChatRoom(models.Model):
    class RoomTypes(models.TextChoices):
        PUBLIC = 'PUBLIC'
        UNLISTED = 'UNLISTED'
        PRIVATE = 'PRIVATE'

    name = models.CharField(max_length=20, unique=True)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="owned_chatrooms")
    room_type = models.CharField(max_length=10, choices=RoomTypes.choices, default=RoomTypes.PUBLIC)
    members = models.ManyToManyField(
        User,
        through=RoomMembership,
        blank=True,
        related_name='member_chatrooms',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class RoomApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        APPROVED = 'APPROVED'
        REJECTED = 'REJECTED'

    applicant = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)
    room = models.ForeignKey(ChatRoom, null=True, blank=False, on_delete=models.SET_NULL, related_name='applications')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

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