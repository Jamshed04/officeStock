from pydantic import BaseModel


class RoleInfo(BaseModel):
    id: int
    role_name: str

    class Config:
        from_attributes = True


class UserAuthResponse(BaseModel):
    user_id: int
    user_name: str
    email: str
    role: str | None
    is_superuser: bool
    access_token: str


class UserMeResponse(BaseModel):
    user_id: int
    user_name: str
    email: str
    position: str | None
    role: str | None
    is_superuser: bool
    permissions: list[str]

    class Config:
        from_attributes = True