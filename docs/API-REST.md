# REST API

Routers are composed in `app/chat/routers/api_router.py` under the `/api` prefix:

- `app/chat/routers/api/auth.py` — register, login, logout
- `app/chat/routers/api/users.py` — user profiles
- `app/chat/routers/api/rooms.py` — room CRUD + membership
- `app/chat/routers/api/applications.py` — join requests for private rooms
- `app/chat/routers/api/frontend.py` — frontend-facing JSON helpers

## Core endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Get JWT token (cookie) |
| `/api/auth/logout` | POST | Revoke JWT (blacklist by `jti`), clear session |
| `/api/rooms/` | GET/POST | List / create rooms |
| `/api/rooms/{name}` | GET/PATCH/DELETE | Room detail, roles: `owner`, `admin`, `moderator`, `member` |
| `/api/applications/` | GET/POST | List / request to join private rooms |

Room types: `PUBLIC`, `UNLISTED`, `PRIVATE`.
Application states: `PENDING`, `APPROVED`, `REJECTED`.

## Interactive reference

Run the app and open the auto-generated OpenAPI UI:

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Auth flow example

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "ada", "password": "s3cret-pw"}'

curl -c cookies.txt -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "ada", "password": "s3cret-pw"}'

curl -b cookies.txt http://127.0.0.1:8000/api/rooms/
```
