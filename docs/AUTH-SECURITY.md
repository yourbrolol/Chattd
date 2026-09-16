# Auth Security

## Components

- `app/core/auth.py` — `JWTAuthBackend`, password hashing (bcrypt/passlib), `get_current_ws_user`.
- `app/core/csrf.py` — `CSRFMiddleware` on the API stack (`CSRF_MAX_AGE`).
- `app/core/token_blacklist.py` + `RevokedToken` model — logout revocation keyed by JWT `jti`.
- `app/chat/errors.py` — `AppError` + `app_error_handler`.

## Flows

- **Register/login:** `POST /api/auth/register`, `POST /api/auth/login` issue a JWT
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 24h) stored in a cookie.
  Set `SECURE=True` in production for HTTPS-only cookies.
- **Request auth:** `AuthenticationMiddleware` populates `request.user` / `websocket.user`.
- **Logout:** persists the token `jti` in `revoked_tokens` until `expires_at`;
  expired rows are pruned so the table stays bounded.
- **Rooms:** `chat/services/rooms.py` enforces membership + roles
  (`owner`, `admin`, `moderator`, `member`); private rooms additionally gate via `RoomApplication`.
- **WS:** unauthenticated sockets close with `WS_CLOSE_AUTH_REQUIRED`
  (see [Websockets](API-WEBSOCKETS.md)); HTTP rate limits via slowapi (`core/router.py`).

## Production checklist

1. Change `SECRET_KEY`.
2. Set `SECURE=True`, serve behind HTTPS.
3. Use a server-grade `DATABASE_URL` (not dev SQLite).
4. Tighten `WS_*` limits and slowapi limits for your traffic.
5. Confirm Alembic is at `head` on deploy.

## Reference

::: app.core.auth.JWTAuthBackend
::: app.core.token_blacklist
