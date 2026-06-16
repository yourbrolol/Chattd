import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db, close_db
from app.chat.routers.auth import router as auth_router
from app.chat.routers.rooms import router as rooms_router
from app.chat.routers.applications import router as applications_router
from app.chat.routers.users import router as users_router
from app.core.websockets import router as ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()
    yield
    # Cleanup DB connection pool
    await close_db()

app = FastAPI(title="SpreadTalk API", lifespan=lifespan)

# Mount media folder for serving avatars
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(applications_router)
app.include_router(users_router)
app.include_router(ws_router)
