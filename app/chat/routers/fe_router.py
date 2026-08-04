import time

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.forms.auth import RegistrationForm, LoginForm
from app.chat.schemas.auth import UserCreate, UserLogin
from app.chat.services.auth import register_user, login_user
from app.core.database import get_db

router = APIRouter(prefix="", tags=["frontend"])

templates = Jinja2Templates(directory="app/chat/templates")

@router.get("/", response_class=HTMLResponse, tags=["main_page"])
async def home_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="chat/index.html", context={
            "request": request,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

@router.get("/register/", name="reg_page", response_class=HTMLResponse, tags=["register_page"])
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

@router.post("/register/", name="reg_submit", response_class=HTMLResponse, tags=["register_page"])
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

@router.get("/login/", name="login_page", response_class=HTMLResponse, tags=["login_page"])
async def login_page(request: Request):
    form = LoginForm()
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={
            "request": request,
            "form": form,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

@router.post("/login/", name="login_submit", response_class=HTMLResponse, tags=["login_page"])
async def login_page_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = LoginForm(await request.form())
    if form.validate():
        token, code = await login_user(db=db, user_data=UserLogin(**form.data))
        response = JSONResponse(content={"message": "Login successful"})
        # Note: The secure flag on cookies ensures they're only sent over encrypted HTTPS connections. For local development (HTTP) set it to False
        response.set_cookie(
            key="jwt_token",
            value=token,
            httponly=True,
            max_age=3600,
            expires=3600,
            samesite="lax",
            #secure=True, enable in prod
            domain=None,
        )
        return response
    else:
        return templates.TemplateResponse(
            request=request, name="auth/login.html", context={
                "request": request,
                "form": form,
                "errors": form.errors,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )