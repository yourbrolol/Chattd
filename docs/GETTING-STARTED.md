# Getting Started

## Prerequisites

- Python 3.12+
- `pip`, `venv`
- Optional: Docker + Docker Compose

## Local setup (venv)

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

Windows (PowerShell):

```pwsh
.venv\Scripts\Activate
pip install -r app\requirements.txt
```

## Docker setup

```bash
docker compose up
```

`docker-compose.yml` mounts `./app` into the container and runs
`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
The production profile (`spreadtalk-prod`) reuses the same image without `--reload`.

## Verify it works

1. Open `http://127.0.0.1:8000/`
2. Register via `POST /api/auth/register`
3. Log in via `POST /api/auth/login`
4. Open a room and connect to `/ws/chat/{room}/`

## Docs preview (MkDocs)

```bash
pip install -r docs-requirements.txt
mkdocs serve
```

Build a static site with `mkdocs build --strict`.
