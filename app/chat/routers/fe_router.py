import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.chat.forms.auth import RegistrationForm, LoginForm

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
    form = RegistrationForm()
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={
            "request": request,
            "form": form,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

@router.post("/register/", response_class=HTMLResponse, tags=["register_page"])
async def reg_page_post(request: Request):
    form = RegistrationForm(await request.form())
    if form.validate():
        # Handle successful registration logic here
        return templates.TemplateResponse(
            request=request, name="auth/register_success.html", context={
                "request": request,
                "username": form.username.data,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )
    else:
        # Handle form errors
        return templates.TemplateResponse(
            request=request, name="auth/register.html", context={
                "request": request,
                "form": form,
                "errors": form.errors,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )

@router.get("/login/", response_class=HTMLResponse, tags=["login_page"])
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

@router.post("/login/", response_class=HTMLResponse, tags=["login_page"])
async def login_page_post(request: Request):
    form = LoginForm(await request.form())
    if form.validate():
        # Handle successful login logic here
        return templates.TemplateResponse(
            request=request, name="auth/login_success.html", context={
                "request": request,
                "username": form.username.data,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )
    else:
        # Handle form errors
        return templates.TemplateResponse(
            request=request, name="auth/login.html", context={
                "request": request,
                "form": form,
                "errors": form.errors,
                "timestamp": int(time.time()), # Replaces {% now "U" %}
                "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
            }
        )