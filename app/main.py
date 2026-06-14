from fastapi import FastAPI
from app.chat.auth import router as auth_router
from app.chat.rooms import router as rooms_router
from app.chat.applications import router as applications_router
from app.chat.users import router as users_router

app = FastAPI(title="SpreadTalk API")

app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(applications_router)
app.include_router(users_router)
