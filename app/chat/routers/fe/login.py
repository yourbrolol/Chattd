import time

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
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
            "csrf_token": "your_csrf_token_here"
        }
    )

@router.post("/", name="login_submit", response_class=HTMLResponse, tags=["login_page"])
async def login_page_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = LoginForm(await request.form())
    if form.validate():
        token, code = await login_user(db=db, user_data=UserLogin(**form.data))
        response = JSONResponse(content={"message": "Login successful"})
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
                "timestamp": int(time.time()),
                "csrf_token": "your_csrf_token_here"
            }
        )