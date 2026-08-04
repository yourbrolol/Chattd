import time

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.forms.auth import RegistrationForm
from app.chat.schemas.auth import UserCreate
from app.chat.services.auth import register_user
from app.core.database import get_db

router = APIRouter(prefix="/register", tags=["register"])

templates = Jinja2Templates(directory="app/chat/templates")

@router.get("/", name="reg_page", response_class=HTMLResponse, tags=["register_page"])
async def reg_page(request: Request):
    form = RegistrationForm()
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={
            "request": request,
            "form": form,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

@router.post("/", name="reg_submit", response_class=HTMLResponse, tags=["register_page"])
async def reg_page_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = RegistrationForm(await request.form())
    if form.validate():
        user, code = await register_user(db=db, user_data=UserCreate(**form.data))
        if code == "ok": return HTMLResponse(f"{code} - User {user.username} registered successfully!")
    else:
        return templates.TemplateResponse(
            request=request, name="auth/register.html", context={
                "request": request,
                "form": form,
                "errors": form.errors,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )