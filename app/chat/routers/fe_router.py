import logging
import time

from fastapi import Request
from app.core.router import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.chat.routers.fe.register import router as reg_router
from app.chat.routers.fe.login import router as login_router

router = APIRouter(prefix="", tags=["frontend"])

templates = Jinja2Templates(directory="app/chat/templates")

logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse, tags=["main_page"])
async def home_page(request: Request):
    #TEST: logger.warning(request.user)
    return templates.TemplateResponse(
        request=request, name="chat/index.html", context={
            "request": request,
            "timestamp": int(time.time()), # Replaces {% now "U" %}
            "csrf_token": "your_csrf_token_here" # Pass your CSRF token if using security middleware
        }
    )

router.include_router(reg_router)
router.include_router(login_router)