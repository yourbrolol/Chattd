"""
SQLAlchemy ORM Models - Fully Type-Checked Edition

Each class = one database table, fully annotated for Pyrefly / type checkers.
"""

from datetime import datetime
import enum
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User model - stores authentication and profile data.
    """
    __tablename__ = "users"

    # Primary key and core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Optional field (Pyrefly sees this as Optional[str] / str | None)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)

    # Boolean flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps (mapped to python datetime objects)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (Using List[...] tells Pyrefly it's an iterable collection)
    owned_chatrooms: Mapped[List["ChatRoom"]] = relationship(
        "ChatRoom",
        back_populates="owner",
        foreign_keys="ChatRoom.owner_id",
    )
    room_memberships: Mapped[List["RoomMembership"]] = relationship(
        "RoomMembership",
        back_populates="user",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="user",
    )
    room_applications: Mapped[List["RoomApplication"]] = relationship(
        "RoomApplication",
        back_populates="applicant",
    )
    
    @property
    def is_authenticated(self) -> bool: return True
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"

    def __str__(self) -> str:
        return self.username

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "is_staff": self.is_staff,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatRoom(Base):
    """Chat room model - matches Django's ChatRoom"""

    class RoomType(str, enum.Enum):
        PUBLIC = 'PUBLIC'
        UNLISTED = 'UNLISTED'
        PRIVATE = 'PRIVATE'

    __tablename__ = "chatrooms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # owner_id can be None/Null if the owner deletes their account
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="owned_chatrooms", foreign_keys=[owner_id]
    )
    
    type: Mapped[RoomType] = mapped_column(
        SQLEnum(RoomType),
        default=RoomType.PUBLIC,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    applications: Mapped[List["RoomApplication"]] = relationship("RoomApplication", back_populates="room")
    members: Mapped[List["RoomMembership"]] = relationship("RoomMembership", back_populates="room")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="room")


class RoomMembership(Base):
    """Through model for room membership with per-user roles."""

    class Role(str, enum.Enum):
        OWNER = 'owner'
        MEMBER = 'member'
        MODERATOR = 'moderator'
        ADMIN = 'admin'

    __tablename__ = "room_memberships"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="room_memberships")
    
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="members")
    
    role: Mapped[str] = mapped_column(
        String(20),
        default=Role.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name='unique_room_user_membership'),
    )


class ChatMessage(Base):
    """Chat message model - stores room messages."""
    __tablename__ = "chatmessages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="messages")
    
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")
    
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class RoomApplication(Base):
    """Room application model - user requests to join private rooms."""

    class ApplicationStatus(str, enum.Enum):
        PENDING = "PENDING"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"

    __tablename__ = "room_applications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    applicant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    applicant: Mapped[Optional["User"]] = relationship("User", back_populates="room_applications")
    
    room_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chatrooms.id", ondelete="SET NULL"), nullable=True)
    room: Mapped[Optional["ChatRoom"]] = relationship("ChatRoom", back_populates="applications")
    
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)