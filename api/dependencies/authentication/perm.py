from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.api_v1.fastapi_users_router import fastapi_users
from core.models import User, db_helper, Role
from core.permissions import Permission, has_permission, RoleEnum

# Базовые зависимости без загрузки ролей
_current_user_base = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


async def current_user(
    user: User = Depends(_current_user_base),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> User:
    """
    Получить текущего пользователя с загруженной ролью.
    """
    # Перезагружаем пользователя с ролью
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.role))
    )
    result = await session.execute(stmt)
    user_with_role = result.scalar_one_or_none()

    if not user_with_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    return user_with_role


async def get_user_roles(user: User = Depends(current_user)) -> list[str]:
    """
    Получить роль текущего пользователя.

    Если пользователь - суперпользователь, автоматически возвращается роль admin.
    """
    # Суперпользователь автоматически получает роль admin
    if user.is_superuser:
        return [RoleEnum.ADMIN.value]

    # Возвращаем роль пользователя, если она есть
    if user.role:
        return [user.role.role_name]

    return []


def require_permission(permission: Permission) -> Callable:
    """
    Декоратор для проверки разрешения.

    Использование:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_permission(Permission.USER_CREATE))
        ):
            ...
    """

    async def permission_checker(
            user: User = Depends(current_user)
    ) -> User:
        # Суперпользователь имеет все разрешения
        if user.is_superuser:
            return user

        # Получаем роль пользователя
        user_role = user.role.role_name if user.role else None

        # Проверяем наличие разрешения
        if not user_role or not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав для выполнения операции. Требуется: {permission.value}",
            )

        return user

    return permission_checker


def require_role(required_role: RoleEnum) -> Callable:
    """
    Декоратор для проверки роли.

    Использование:
        @router.get("/hr")
        async def hr_endpoint(
            user: User = Depends(require_role(RoleEnum.HR_MANAGER))
        ):
            ...
    """

    async def role_checker(
            user: User = Depends(current_user)
    ) -> User:
        # Суперпользователь имеет доступ ко всем эндпоинтам
        if user.is_superuser:
            return user

        # Проверяем наличие роли
        user_role = user.role.role_name if user.role else None

        if user_role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {required_role.value}",
            )

        return user

    return role_checker


def require_any_role(*required_roles: RoleEnum) -> Callable:
    """
    Декоратор для проверки наличия хотя бы одной из ролей.

    Использование:
        @router.get("/reports")
        async def reports_endpoint(
            user: User = Depends(require_any_role(RoleEnum.ECONOMIST, RoleEnum.DIRECTOR))
        ):
            ...
    """

    async def role_checker(
            user: User = Depends(current_user)
    ) -> User:
        # Суперпользователь имеет доступ ко всем эндпоинтам
        if user.is_superuser:
            return user

        # Проверяем наличие хотя бы одной из требуемых ролей
        user_role = user.role.role_name if user.role else None
        required_role_values = [r.value for r in required_roles]

        if user_role not in required_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {', '.join(required_role_values)}",
            )

        return user

    return role_checker