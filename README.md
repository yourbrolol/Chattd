# Chattd — pronounced "Chatted" — "Chat Daemon"

A real-time chat application with WebSocket support, rate limiting, and role-based room access.

## Stack

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy (async) + Alembic
- WebSockets
- Vanilla HTML / JS / CSS

## Quick Start

```bash
git clone <repo-url> Chattd
cd Chattd
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r app/requirements.txt
cp app/.env.example app/.env
alembic upgrade head
uvicorn app.main:app --reload
```

<details>
<summary>Windows setup</summary>

```pwsh
.venv\Scripts\Activate
pip install -r app\requirements.txt
```
</details>

<details>
<summary>Docker setup</summary>

```bash
docker compose up
```
</details>

## Configuration

All configuration is done via environment variables in `app/.env`. Copy `app/.env.example` to get started.

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `hyper_secret_key` | JWT signing key. **Change this in production.** |
| `SECURE` | `False` | Set to `True` for HTTPS-only cookies |
| `CSRF_MAX_AGE` | `2592000` (30 days) | CSRF token lifetime in seconds |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | JWT token expiry |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./app/db.sqlite3` | Async database connection string |

### WebSocket Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_CONNECT_MAX_EVENTS` | `3` | Max connection attempts per window |
| `WS_CONNECT_PER_SECONDS` | `3` | Connection rate limit window (seconds) |
| `WS_MESSAGE_MAX_EVENTS` | `1` | Max messages per window |
| `WS_MESSAGE_PER_SECONDS` | `1` | Message rate limit window (seconds) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL_MAIN` | `INFO` | Log level for application code |
| `LOG_LEVEL_SEC` | `WARNING` | Log level for third-party packages |

## Architecture

```
app/
├── core/                  # Framework layer
│   ├── auth.py            # JWT + password hashing
│   ├── config.py          # Environment config
│   ├── websockets.py      # WebSocket connection manager
│   └── ws_ratelimit.py    # Sliding window rate limiter
├── chat/                  # Business logic
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # Business logic
│   └── routers/           # FastAPI route handlers
│       ├── api/           # REST endpoints (/api/...)
│       └── fe/            # Frontend page routes
└── tests/                 # Test suites
```

**Request flow:** `Router → Service → Database`

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Get JWT token |
| `/api/auth/logout` | POST | Clear session |
| `/ws/chat/{room}/` | WS | Real-time chat |

## Frontend

Frontend files live in `app/chat/static/`. The app requires JavaScript enabled in the browser.

- `*.html` — Page templates
- `*.css` — Stylesheets
- `*.js` — Client-side logic
