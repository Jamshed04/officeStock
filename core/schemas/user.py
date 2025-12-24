from fastapi_users import schemas
from pydantic import EmailStr, Field


class UserRead(schemas.BaseUser[int]):
    name: str
    position: str | None = None
    role_id: int | None = None
    role_name: str | None = None

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    name: str
    role_id: int | None = None

class UserCreateWithRole(UserCreate):
    role_name: str | None = Field(None, description="Название роли пользователя")


class UserUpdate(schemas.BaseUserUpdate):
    name: str | None = None
    position: str | None = None


class UserCreateAdmin(schemas.BaseUserCreate):
    name: str = Field(..., min_length=1, max_length=255)
    position: str | None = Field(None, max_length=255)
    is_superuser: bool = False
    role_name: str | None = Field(None, description="Название роли для назначения")


class UserUpdateAdmin(schemas.BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    position: str | None = Field(None, max_length=255)
    is_superuser: bool | None = None
    role_name: str | None = Field(None, description="Название роли")


class ChangePasswordRequest(schemas.BaseModel):
    new_password: str = Field(..., min_length=8, max_length=255)