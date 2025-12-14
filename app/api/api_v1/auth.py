"""
Эндпоинты авторизации и регистрации с расширенной информацией о пользователе.
"""
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.api_v1.fastapi_users_router import fastapi_users
from api.dependencies.authentication.backend import authentication_backend
from api.dependencies.authentication.perm import current_user
from api.dependencies.authentication.strategy import get_database_strategy
from api.dependencies.authentication.user_manager import get_user_manager
from core.authentication.user_manager import UserManager
from core.config import settings
from core.models import User, db_helper
from core.schemas.auth import UserAuthResponse, UserMeResponse
from core.schemas.user import UserRead, UserCreate
from core.permissions import get_user_permissions
from fastapi_users.authentication.strategy.db import DatabaseStrategy

router = APIRouter(
    prefix=settings.api.v1.auth,
    tags=["Auth"],
)


@router.post("/login", response_model=UserAuthResponse)
async def login(
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user_manager: UserManager = Depends(get_user_manager),
        strategy: DatabaseStrategy = Depends(get_database_strategy),
):
    """
    Вход с возвратом расширенной информации о пользователе.

    Возвращает:
    - user_id: ID пользователя
    - user_name: Имя пользователя
    - email: Email
    - role: Название роли
    - is_superuser: Флаг суперпользователя
    - access_token: JWT токен
    """
    # Получаем пользователя с ролью
    stmt = (
        select(User)
        .where(User.email == credentials.username)
        .options(selectinload(User.role))
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    is_valid = user_manager.password_helper.verify_and_update(
        credentials.password,
        user.hashed_password,
    )[0]

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь неактивен",
        )

    token = await strategy.write_token(user)

    # Получаем роль
    role = user.role.role_name if user.role else None
    if user.is_superuser and role != "admin":
        role = "admin"

    return UserAuthResponse(
        user_id=user.id,
        user_name=user.name,
        email=user.email,
        role=role,
        is_superuser=user.is_superuser,
        access_token=token,
    )


# /logout
router.include_router(
    router=fastapi_users.get_auth_router(authentication_backend),
    prefix="",
)

# /register
router.include_router(
    router=fastapi_users.get_register_router(UserRead, UserCreate),
)

# /reset-password
router.include_router(
    router=fastapi_users.get_reset_password_router(),
)


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Получить информацию о текущем пользователе с ролью и разрешениями.

    Возвращает:
    - user_id: ID пользователя
    - user_name: Имя пользователя
    - email: Email
    - position: Должность
    - role: Название роли
    - is_superuser: Флаг суперпользователя
    - permissions: Список разрешений
    """
    # Загружаем роль пользователя
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.role))
    )
    result = await session.execute(stmt)
    user = result.scalar_one()

    # Получаем роль
    role = user.role.role_name if user.role else None
    if user.is_superuser and role != "admin":
        role = "admin"

    # Получаем разрешения
    permissions = get_user_permissions([role] if role else [])
    permission_strings = [p.value for p in permissions]

    return UserMeResponse(
        user_id=user.id,
        user_name=user.name,
        email=user.email,
        position=user.position,
        role=role,
        is_superuser=user.is_superuser,
        permissions=permission_strings,
    )