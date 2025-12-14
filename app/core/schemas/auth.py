from pydantic import BaseModel


class RoleInfo(BaseModel):
    """Информация о роли"""
    id: int
    role_name: str

    class Config:
        from_attributes = True


class UserAuthResponse(BaseModel):
    """Ответ при успешной авторизации"""
    user_id: int
    user_name: str
    email: str
    role: str | None
    is_superuser: bool
    access_token: str


class UserMeResponse(BaseModel):
    """Информация о текущем пользователе"""
    user_id: int
    user_name: str
    email: str
    position: str | None
    role: str | None
    is_superuser: bool
    permissions: list[str]

    class Config:
        from_attributes = True