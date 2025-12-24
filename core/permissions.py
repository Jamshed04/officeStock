"""
Система ролей и разрешений.

Роли в системе:
- admin: Полный доступ ко всем функциям (объединяет суперпользователя и админа)
- hr-manager: Управление пользователями, просмотр отчетов
- economist: Работа с заказами, чеками, финансовыми данными
- director: Просмотр всех данных, утверждение заявок
"""

from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr-manager"
    ECONOMIST = "economist"
    DIRECTOR = "director"


class Permission(str, Enum):
    # Управление пользователями
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_CHANGE_PASSWORD = "user:change_password"

    # Управление ролями
    ROLE_ASSIGN = "role:assign"
    ROLE_REVOKE = "role:revoke"

    # Управление заказами
    ORDER_CREATE = "order:create"
    ORDER_READ = "order:read"
    ORDER_UPDATE = "order:update"
    ORDER_DELETE = "order:delete"

    # Управление чеками
    RECEIPT_CREATE = "receipt:create"
    RECEIPT_READ = "receipt:read"
    RECEIPT_UPDATE = "receipt:update"
    RECEIPT_DELETE = "receipt:delete"

    # Управление складом
    WAREHOUSE_READ = "warehouse:read"
    WAREHOUSE_UPDATE = "warehouse:update"

    # Управление категориями
    CATEGORY_CREATE = "category:create"
    CATEGORY_READ = "category:read"
    CATEGORY_DELETE = "category:delete"

    # Заявки на списание
    WRITEOFF_CREATE = "writeoff:create"
    WRITEOFF_READ = "writeoff:read"
    WRITEOFF_APPROVE = "writeoff:approve"
    WRITEOFF_REJECT = "writeoff:reject"

    # Отчеты
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"


ROLE_PERMISSIONS: dict[RoleEnum, set[Permission]] = {
    RoleEnum.ADMIN: {
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_CHANGE_PASSWORD,
        Permission.ROLE_ASSIGN,
        Permission.ROLE_REVOKE,
        Permission.ORDER_CREATE,
        Permission.ORDER_READ,
        Permission.ORDER_UPDATE,
        Permission.ORDER_DELETE,
        Permission.RECEIPT_CREATE,
        Permission.RECEIPT_READ,
        Permission.RECEIPT_UPDATE,
        Permission.RECEIPT_DELETE,
        Permission.WAREHOUSE_READ,
        Permission.WAREHOUSE_UPDATE,
        Permission.CATEGORY_CREATE,
        Permission.CATEGORY_READ,
        Permission.CATEGORY_DELETE,
        Permission.WRITEOFF_CREATE,
        Permission.WRITEOFF_READ,
        Permission.WRITEOFF_APPROVE,
        Permission.WRITEOFF_REJECT,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
    },
    RoleEnum.HR_MANAGER: {
        Permission.RECEIPT_CREATE,
        Permission.RECEIPT_READ,
        Permission.RECEIPT_UPDATE,
        Permission.RECEIPT_DELETE,
        Permission.WAREHOUSE_READ,
        Permission.WAREHOUSE_UPDATE,
        Permission.CATEGORY_CREATE,
        Permission.CATEGORY_READ,
        Permission.CATEGORY_DELETE,
        Permission.WRITEOFF_CREATE,
        Permission.WRITEOFF_READ,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
    },
    RoleEnum.ECONOMIST: {
        Permission.ORDER_CREATE,
        Permission.ORDER_READ,
        Permission.ORDER_UPDATE,
        Permission.RECEIPT_CREATE,
        Permission.RECEIPT_READ,
        Permission.WAREHOUSE_READ,
        Permission.WAREHOUSE_READ,
        Permission.WAREHOUSE_UPDATE,
        Permission.CATEGORY_CREATE,
        Permission.CATEGORY_READ,
        Permission.CATEGORY_DELETE,
        Permission.WRITEOFF_CREATE,
        Permission.WRITEOFF_READ,
        Permission.REPORTS_VIEW,
    },
    RoleEnum.DIRECTOR: {
        Permission.USER_READ,
        Permission.ORDER_READ,
        Permission.RECEIPT_READ,
        Permission.WAREHOUSE_READ,
        Permission.WRITEOFF_READ,
        Permission.WRITEOFF_APPROVE,
        Permission.WRITEOFF_REJECT,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Проверить, есть ли у роли данное разрешение.
    """
    try:
        role_enum = RoleEnum(role)
        return permission in ROLE_PERMISSIONS.get(role_enum, set())
    except ValueError:
        return False


def get_user_permissions(roles: list[str]) -> set[Permission]:
    """
    Получить все разрешения пользователя на основе его ролей.
    """
    permissions = set()
    for role in roles:
        try:
            role_enum = RoleEnum(role)
            permissions.update(ROLE_PERMISSIONS.get(role_enum, set()))
        except ValueError:
            continue
    return permissions