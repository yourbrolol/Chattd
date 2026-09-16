# Configuration

All configuration is done via environment variables in `app/.env`.
Copy `app/.env.example` to get started.

## Feature flags (`app/main.py`)

| Variable | Default | Effect |
|----------|---------|--------|
| `RUN_API` | `True` | Mounts `/api/*`, `/media`, `/ws/*`, JWT + CSRF middleware |
| `SERVE_FE` | `True` | Mounts `/static` (`app/chat/static`) and frontend page routes |

## Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `hyper_secret_key` | JWT signing key. **Change in production.** |
| `SECURE` | `False` | Set `True` for HTTPS-only cookies |
| `CSRF_MAX_AGE` | `2592000` (30 days) | CSRF token lifetime, seconds |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | JWT expiry |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./app/db.sqlite3` | Async SQLAlchemy connection string |

## WebSocket rate limiting (`app/core/ws_ratelimit.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_CONNECT_MAX_EVENTS` | `3` | Max connection attempts per window |
| `WS_CONNECT_PER_SECONDS` | `3` | Connection rate-limit window (s) |
| `WS_MESSAGE_MAX_EVENTS` | `1` | Max messages per window |
| `WS_MESSAGE_PER_SECONDS` | `1` | Message rate-limit window (s) |

See [Websockets](API-WEBSOCKETS.md) for close codes and `rate_limited` / `quota_left` frames.

## Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL_MAIN` | `INFO` | App code log level |
| `LOG_LEVEL_SEC` | `WARNING` | Third-party log level |
