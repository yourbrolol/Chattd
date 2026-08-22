import secrets
from app.chat.models import User, ChatRoom, RoomMembership, RoomApplication
from app.core.auth import hash_password

class Credentials:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        userlen: int = 8,
        passlen: int = 12
    ):
        _username, _password = self.initialize(userlen=userlen, passlen=passlen)
        self.username = username if username is not None else _username
        self.password = password if password is not None else _password

    def as_dict(self):
        return {'username': self.username, 'password': self.password}

    @staticmethod
    def initialize(
        userlen: int = 8,
        passlen: int = 12
    ):
        # Generate pseudo-random hexadecimal string of length n
        return secrets.token_hex(userlen), secrets.token_hex(passlen)


def user_payload_factory(username=None, password=None):
    """Generates user registration payload dict."""
    return Credentials(username, password).as_dict()


async def user_db_factory(db_session, username=None, password=None, is_active=True) -> User:
    """Inserts a User into the database and returns the User object."""
    cred = Credentials(username, password)
    user = User(
        username=cred.username,
        password_hash=hash_password(cred.password),
        is_active=is_active
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    # Store raw password on the model temporarily for test reference
    user.raw_password = cred.password
    return user


def room_payload_factory(room_name=None, room_type="PUBLIC"):
    """Generates room creation payload dict."""
    if not room_name:
        room_name = f"room_{secrets.token_hex(4)}"
    return {"room_name": room_name, "room_type": room_type}


async def room_db_factory(db_session, owner_id, room_name=None, room_type="PUBLIC") -> ChatRoom:
    """Inserts a ChatRoom into the database and returns it."""
    if not room_name:
        room_name = f"room_{secrets.token_hex(4)}"
    room = ChatRoom(
        name=room_name,
        owner_id=owner_id,
        type=room_type
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)
    return room


async def member_db_factory(db_session, room_id, user_id, role="member") -> RoomMembership:
    """Inserts a RoomMembership into the database and returns it."""
    membership = RoomMembership(
        room_id=room_id,
        user_id=user_id,
        role=role
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


async def application_db_factory(db_session, applicant_id, room_id, status="PENDING") -> RoomApplication:
    """Inserts a RoomApplication into the database and returns it."""
    app = RoomApplication(
        applicant_id=applicant_id,
        room_id=room_id,
        status=status
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    return app

