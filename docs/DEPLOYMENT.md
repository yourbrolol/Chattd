# Deployment

## Docker (recommended)

```bash
docker compose up                      # dev (reload, ./app bind-mount)
docker compose --profile production up --build   # prod service
```

- Image: `python:3.12-slim`, deps from `app/requirements.txt`, serves with
  `uvicorn app.main:app --host 0.0.0.0 --port 8000` (`Dockerfile`).
- Env comes from `./app/.env` (`env_file` in `docker-compose.yml`).

## Manual deploy

```bash
pip install -r app/requirements.txt
cp app/.env.example app/.env   # then edit SECRET_KEY, SECURE, DATABASE_URL
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Lifespan (`app/main.py`) runs `init_db()` on startup and `close_db()` on shutdown;
`media/` is created if missing.

## Production notes

- `SECRET_KEY` must be unique; `SECURE=True` (HTTPS-only cookies).
- Point `DATABASE_URL` at Postgres; back up `media/` (avatars).
- Put Uvicorn behind a reverse proxy for TLS; scale WS with sticky sessions
  (the `ConnectionManager` is per-process memory).
