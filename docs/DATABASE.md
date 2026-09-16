# Database

Models live in `app/chat/models.py`. Migrations use Alembic (`alembic.ini`, `alembic/`).

## Tables

- `users` — `User`: `username` (unique), `password_hash`, `avatar`, `is_active/staff/superuser`, timestamps.
- `chatrooms` — `ChatRoom`: `name` (unique), `owner_id → users.id` (nullable), `type` (`PUBLIC/UNLISTED/PRIVATE`).
- `room_memberships` — `RoomMembership`: `(room_id, user_id)` unique, `role` (`owner/member/moderator/admin`).
- `chatmessages` — `ChatMessage`: `room_id → chatrooms.id` (CASCADE), `user_id → users.id`, `content` (≤1000), `timestamp`.
- `room_applications` — `RoomApplication`: `applicant_id`, `room_id`, `status` (`PENDING/APPROVED/REJECTED`).
- `revoked_tokens` — `RevokedToken`: PK `jti`, `user_id`, indexed `expires_at`, `revoked_at`.

## Relationships

- `User.owned_chatrooms ↔ ChatRoom.owner`
- `User.room_memberships ↔ RoomMembership.user ↔ ChatRoom.members`
- `User.messages ↔ ChatMessage.user ↔ ChatRoom.messages`
- `User.room_applications ↔ RoomApplication.applicant ↔ ChatRoom.applications`

Deleting a room cascades to members and messages (`passive_deletes=True` + `ondelete="CASCADE"`).
Deleting a user nulls ownership/membership/application FKs (`SET NULL`).

## Migrations

```bash
alembic upgrade head        # apply
alembic revision --autogenerate -m "add xyz"   # new migration
alembic downgrade -1        # roll back one
```

Default dev DB is SQLite (`sqlite+aiosqlite:///./app/db.sqlite3`);
set `DATABASE_URL` for Postgres in production.

## Reference

::: app.chat.models.User
::: app.chat.models.ChatRoom
::: app.chat.models.RoomMembership
::: app.chat.models.ChatMessage
::: app.chat.models.RoomApplication
::: app.chat.models.RevokedToken
