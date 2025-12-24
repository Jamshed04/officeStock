from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from core.config import settings
from .admin_users import router as admin_users_router
from .auth import router as auth_router
from .users import router as users_router
from .receipts import router as receipts_router
from .warehouse import router as warehouse_router
from .categories import router as categories_router
from .write_off import router as writeoff_router
from .reports import router as reports_router

http_bearer = HTTPBearer(auto_error=False)
router = APIRouter(
    prefix=settings.api.v1.prefix,
    dependencies=[Depends(http_bearer)],
)
router.include_router(auth_router)
router.include_router(users_router)

router.include_router(receipts_router)
router.include_router(admin_users_router)
router.include_router(warehouse_router)
router.include_router(categories_router)
router.include_router(writeoff_router)
router.include_router(reports_router)