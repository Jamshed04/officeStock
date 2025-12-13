from typing import Callable
from fastapi import Depends, HTTPException, status

from api.api_v1.fastapi_users_router import fastapi_users
from core.models import User
from core.permissions import Permission, has_permission, RoleEnum

# Базовые зависимости
current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


async def get_user_roles(user: User = Depends(current_user)) -> list[str]:
    """
    Получить список ролей текущего пользователя.

    Если пользователь - суперпользователь, автоматически добавляется роль admin.
    """
    roles = [role.role_name for role in user.roles]

    # Суперпользователь автоматически получает роль admin
    if user.is_superuser and RoleEnum.ADMIN.value not in roles:
        roles.append(RoleEnum.ADMIN.value)

    return roles


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

        # Получаем роли пользователя
        user_roles = [role.role_name for role in user.roles]

        # Проверяем наличие разрешения
        has_perm = any(
            has_permission(role, permission)
            for role in user_roles
        )

        if not has_perm:
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
        user_roles = [role.role_name for role in user.roles]

        if required_role.value not in user_roles:
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

        # Проверяем наличие хотя бы одной роли
        user_roles = [role.role_name for role in user.roles]
        required_role_values = [r.value for r in required_roles]

        has_role = any(role in required_role_values for role in user_roles)

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {', '.join(required_role_values)}",
            )

        return user

    return role_checker