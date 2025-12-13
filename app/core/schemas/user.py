from fastapi_users import schemas
from pydantic import EmailStr, Field


class UserRead(schemas.BaseUser[int]):
    name: str
    position: str | None = None
    roles: list[str] = []

    @classmethod
    def from_orm(cls, obj):
        """Преобразование ORM объекта с ролями"""
        data = super().from_orm(obj)
        if hasattr(obj, 'roles'):
            data.roles = [role.role_name for role in obj.roles]
        return data

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    name: str
    position: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    name: str | None = None
    position: str | None = None


class UserCreateAdmin(schemas.BaseUserCreate):
    name: str = Field(..., min_length=1, max_length=255)
    position: str | None = Field(None, max_length=255)
    is_superuser: bool = False
    role_ids: list[int] | None = Field(None, description="ID ролей для назначения")


class UserUpdateAdmin(schemas.BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    position: str | None = Field(None, max_length=255)
    is_superuser: bool | None = None
    role_ids: list[int] | None = Field(None, description="ID ролей (заменяет текущие)")


class ChangePasswordRequest(schemas.BaseModel):
    new_password: str = Field(..., min_length=8, max_length=255)