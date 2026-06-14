"""
SQLAlchemy ORM Models

These are equivalent to Django models but for SQLAlchemy.
Each class = one database table.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.core.database import Base


class User(Base):
    """
    User model - stores authentication and profile data.

    Equivalent to Django's AbstractBaseUser + PermissionsMixin

    Fields:
        id: Primary key (auto-increment)
        username: Unique username (max 20 chars)
        password_hash: Bcrypt hashed password
        avatar: Path to avatar image file (nullable)
        is_active: Whether user account is active
        is_staff: Whether user can access admin
        is_superuser: Whether user has all permissions
        created_at: Account creation timestamp
        updated_at: Last account update timestamp

    Relationships:
        owned_chatrooms: Rooms owned by this user
        room_memberships: Rooms this user is a member of
        messages: Messages sent by this user
        room_applications: Applications submitted by this user
    """

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    avatar = Column(
        String(255),
        nullable=True,
        default=None,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_staff = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owned_chatrooms = relationship(
        "ChatRoom",
        back_populates="owner",
        foreign_keys="ChatRoom.owner_id",
    )

    room_memberships = relationship(
        "RoomMembership",
        back_populates="user",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="user",
    )

    room_applications = relationship(
        "RoomApplication",
        back_populates="applicant",
    )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<User(id={self.id}, username='{self.username}')>"

    def __str__(self) -> str:
        """Friendly string representation"""
        return self.username

    def to_dict(self) -> dict:
        """Convert model to dictionary (useful for API responses)"""
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "is_staff": self.is_staff,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatRoom(Base):
    """Chat room model - will be fully defined later"""

    class RoomType(str, enum.Enum):
        PUBLIC = 'PUBLIC',
        UNLISTED = 'UNLISTED',
        PRIVATE = 'PRIVATE',

    __tablename__ = "chatrooms"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship(
        "User", back_populates="owned_chatrooms", foreign_keys=[owner_id])
    
    type = Column(
        SQLEnum(RoomType),
        default=RoomType.PUBLIC,
        nullable=False,
    )

    applications = relationship("RoomApplication", back_populates="room")
    members = relationship("RoomMembership", back_populates="room")
    messages = relationship("ChatMessage", back_populates="room")


class RoomMembership(Base):
    """Room membership model - will be fully defined later"""
    __tablename__ = "room_memberships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="room_memberships")
    room_id = Column(Integer, ForeignKey("chatrooms.id"), nullable=True)
    room = relationship("ChatRoom", back_populates="members")


class ChatMessage(Base):
    """Chat message model - will be fully defined later"""
    __tablename__ = "chatmessages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="messages")
    room_id = Column(Integer, ForeignKey("chatrooms.id"))
    room = relationship("ChatRoom", back_populates="messages")
    content = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    # TODO: add hash


class RoomApplication(Base):
    """Room application model - will be fully defined later"""

    class ApplicationStatus(str, enum.Enum):
        PENDING = "PENDING"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"

    __tablename__ = "room_applications"
    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey("users.id"))
    applicant = relationship("User", back_populates="room_applications")
    room_id = Column(Integer, ForeignKey("chatrooms.id"))
    room = relationship("ChatRoom", back_populates="applications")
    status = Column(
        SQLEnum(ApplicationStatus),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )