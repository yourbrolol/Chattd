import time

from fastapi import Request, Depends
from app.core.router import APIRouter
from app.core.csrf import CSRF_COOKIE_NAME, get_csrf_token
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.forms.auth import LoginForm
from app.chat.schemas.auth import UserLogin
from app.chat.services.auth import login_user
from app.core.database import get_db

router = APIRouter(prefix="/login", tags=["login"])

templates = Jinja2Templates(directory="app/chat/templates")

@router.get("/", name="login_page", response_class=HTMLResponse, tags=["login_page"])
async def login_page(request: Request):
    form = LoginForm()
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={
            "request": request,
            "form": form,
            "timestamp": int(time.time()),
            "csrf_token": request.cookies.get(CSRF_COOKIE_NAME, "")
        }
    )

@router.post("/", name="login_submit", response_class=RedirectResponse | HTMLResponse, tags=["login_page"])
async def login_page_post(request: Request, db: AsyncSession = Depends(get_db), csrf_token: str = Depends(get_csrf_token)):
    form = LoginForm(await request.form())
    if form.validate():
        token_payload, code = await login_user(db=db, user_data=UserLogin(**form.data))
        if not token_payload or "access_token" not in token_payload:
            return templates.TemplateResponse(
                request=request, name="auth/login.html", context={
                    "request": request,
                    "form": form,
                    "errors": {"username": ["Invalid username or password."]},
                    "timestamp": int(time.time()),
                    "csrf_token": csrf_token
                }
            )
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token_payload["access_token"],
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
                "timestamp": int(time.time()),
                "csrf_token": csrf_token
            }
        )
