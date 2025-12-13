"""
Расширенные эндпоинты авторизации с информацией о ролях.
"""
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies.authentication.perm import current_user
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from api.dependencies.authentication.strategy import get_database_strategy
from fastapi import Depends
from app.api.dependencies.authentication.user_manager import get_user_manager
from app.core.authentication.user_manager import UserManager
from core.config import settings
from core.models import User, db_helper
from core.schemas.auth import UserAuthResponse, UserMeResponse
from core.permissions import get_user_permissions

router = APIRouter(
    prefix=settings.api.v1.auth,
    tags=["Auth Enhanced"],
)


@router.post("/login-enhanced", response_model=UserAuthResponse)
async def login_with_roles(
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user_manager: UserManager = Depends(get_user_manager),
        strategy: DatabaseStrategy = Depends(get_database_strategy),
):
    """
    Расширенный вход с возвратом информации о ролях.

    Возвращает:
    - user_id: ID пользователя
    - user_name: Имя пользователя
    - email: Email
    - roles: Список ролей
    - is_superuser: Флаг суперпользователя
    - access_token: JWT токен
    """
    # Получаем пользователя с ролями
    stmt = (
        select(User)
        .where(User.email == credentials.username)
        .options(selectinload(User.roles))
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

    # Получаем роли
    roles = [role.role_name for role in user.roles]
    if user.is_superuser and "admin" not in roles:
        roles.append("admin")

    return UserAuthResponse(
        user_id=user.id,
        user_name=user.name,
        email=user.email,
        roles=roles,
        is_superuser=user.is_superuser,
        access_token=token,
    )


@router.get("/me-enhanced", response_model=UserMeResponse)
async def get_current_user_info(
        user: User = Depends(current_user),
):
    """
    Получить информацию о текущем пользователе с ролями и разрешениями.

    Возвращает:
    - user_id: ID пользователя
    - user_name: Имя пользователя
    - email: Email
    - position: Должность
    - roles: Список ролей
    - is_superuser: Флаг суперпользователя
    - permissions: Список разрешений
    """
    # Получаем роли
    roles = [role.role_name for role in user.roles]
    if user.is_superuser and "admin" not in roles:
        roles.append("admin")

    # Получаем разрешения
    permissions = get_user_permissions(roles)
    permission_strings = [p.value for p in permissions]

    return UserMeResponse(
        user_id=user.id,
        user_name=user.name,
        email=user.email,
        position=user.position,
        roles=roles,
        is_superuser=user.is_superuser,
        permissions=permission_strings,
    )