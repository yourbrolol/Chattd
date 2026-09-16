# Architecture

## Layout

```
app/
├── main.py                  # FastAPI app, lifespan, middleware, router mounting
├── core/                    # Framework layer
│   ├── auth.py              # JWT + password hashing
│   ├── config.py            # Environment config
│   ├── csrf.py              # CSRFMiddleware
│   ├── database.py          # Async engine, Base, init_db/close_db
│   ├── router.py            # Shared APIRouter + slowapi limiter
│   ├── settings.py
│   ├── token_blacklist.py   # Revoked-token service
│   ├── websockets.py        # WS endpoint + ConnectionManager
│   └── ws_ratelimit.py      # SlidingWindowLimiter
├── chat/                    # Business logic
│   ├── models.py            # ORM: User, ChatRoom, RoomMembership, ChatMessage, RoomApplication, RevokedToken
│   ├── errors.py            # AppError + handler
│   ├── forms/ schemas/      # Validation (Pydantic + WTForms)
│   ├── services/            # Business logic (rooms, messages, ...)
│   ├── routers/api/         # REST: auth, users, rooms, applications, frontend
│   ├── routers/fe/          # Page routes: register, login
│   └── static/ templates/   # Vanilla HTML/JS/CSS + Jinja templates
└── tests/
```

## Request flow

**REST:** `routers/api/*.py → services/*.py → models.py → DB`
**WebSocket:** `core/websockets.py → chat/services/rooms.py + messages.py → broadcast via ConnectionManager`

`app/main.py` mounts `api_router` (`/api`) and `ws_router` (`/ws/...`) when `RUN_API`
is true, and `fe_router` + `/static` when `SERVE_FE` is true.

## Key decisions

- Async SQLAlchemy throughout; `init_db()` on startup, `close_db()` on shutdown.
- JWT auth via `AuthenticationMiddleware` + `JWTAuthBackend`; CSRF enforced on API.
- Per-room in-memory `ConnectionManager` (`room_name → Set[WebSocket]`) with
  dead-socket eviction on broadcast failure.
- Sliding-window WS limiters are per-user keys (`ws-connect:{username}`, `ws-msg:{username}`).
