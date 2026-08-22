from app.core.router import APIRouter

from app.chat.routers.api.auth import router as auth_router
from app.chat.routers.api.frontend import router as fe_router
from app.chat.routers.api.rooms import router as rooms_router
from app.chat.routers.api.applications import router as applications_router
from app.chat.routers.api.users import router as users_router

router = APIRouter(prefix="/api", tags=["api"])

router.include_router(auth_router)
router.include_router(fe_router)
router.include_router(rooms_router)
router.include_router(applications_router)
router.include_router(users_router)