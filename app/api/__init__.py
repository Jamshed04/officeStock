from fastapi import APIRouter

from core.config import settings
from .api_v1 import router as router_api_v1
router = APIRouter(
    prefix=settings.api.prefix,
)

from .api_v1.notifications import router as notifications_router


router.include_router(notifications_router, prefix=settings.api.v1.prefix)
router.include_router(router_api_v1)
