import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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

@router.get("/register/", response_class=HTMLResponse, tags=["register_page"])
async def reg_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={
            "request": request,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

@router.get("/login/", response_class=HTMLResponse, tags=["login_page"])
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={
            "request": request,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )