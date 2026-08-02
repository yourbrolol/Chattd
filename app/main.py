from sqlalchemy.engine import default
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db, close_db
from app.core.websockets import router as ws_router

from decouple import config

RUN_API = config("RUN_API", default=True)
SERVE_FE = config("SERVE_FE", default=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()
    yield
    # Cleanup DB connection pool
    await close_db()

app = FastAPI(title="SpreadTalk API", lifespan=lifespan)

if RUN_API:
    from app.chat.routers.api_router import router as api_router
    from app.core.auth import JWTAuthBackend
    from starlette.middleware.authentication import AuthenticationMiddleware
    
    app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())
    
    os.makedirs("media", exist_ok=True)
    app.mount("/media", StaticFiles(directory="media"), name="media")

    app.include_router(api_router)
    app.include_router(ws_router)

if SERVE_FE:
    from app.chat.routers.fe_router import router as fe_router
    
    app.mount("/static", StaticFiles(directory="app/chat/static"), name="static")
    
    app.include_router(fe_router)