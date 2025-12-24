from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users.password import PasswordHelper
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status
from sqlalchemy.orm import selectinload

from api.api_v1.fastapi_users_router import current_super_user
from api.dependencies.authentication.perm import require_permission
from core.config import settings
from core.models import db_helper, User, Role
from core.schemas.user import UserRead, UserCreateAdmin, UserUpdateAdmin
from core.permissions import Permission
router = APIRouter(

    prefix=settings.api.v1.admin_users,
    tags=["Admin Users"],
    dependencies=[Depends(current_super_user)],
)

@router.get("/", response_model=list[UserRead])
async def get_all_users(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    skip: int = 0,
    limit: int = 100,
):
    stmt = select(User).options(selectinload(User.role)).offset(skip).limit(limit)
    result = await session.execute(stmt)
    users = result.scalars().all()

    users_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "position": user.position,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "role_id": user.role_id,
            "role_name": user.role.role_name if user.role else None,
        }
        users_list.append(UserRead(**user_dict))

    return users_list


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    user_data: UserCreateAdmin,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: User = Depends(require_permission(Permission.USER_CREATE)),
):
    stmt = select(User).where(User.email == user_data.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    password_helper = PasswordHelper()
    password_hash = password_helper.hash(user_data.password)

    if user_data.role_name:
        stmt = select(Role).where(Role.role_name == user_data.role_name)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Роль не найдена",
            )
        role_id = role.id

    new_user = User(
        email=str(user_data.email),
        hashed_password=password_hash,
        name=user_data.name,
        position=user_data.position,
        is_superuser=user_data.is_superuser,
        role_id=role_id,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user, ["role"])

    return UserRead(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        position=new_user.position,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        is_verified=new_user.is_verified,
        role_id=new_user.role_id,
        role_name=new_user.role.role_name if new_user.role else None,
    )


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_by_admin(
    user_id: int,
    user_update: UserUpdateAdmin,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: User = Depends(require_permission(Permission.USER_UPDATE)),
):
    stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user_update.email and user_update.email != user.email:
        stmt = select(User).where(User.email == user_update.email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )

    if user_update.role_name is not None:
        stmt = select(Role).where(Role.role_name == user_update.role_name)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Роль не найдена",
            )
        user.role_id = role.id

    update_data = user_update.model_dump(exclude_unset=True, exclude={"role_name"})
    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user, ["role"])

    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        position=user.position,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        role_id=user.role_id,
        role_name=user.role.role_name if user.role else None,
    )


@router.post("/{user_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password_by_admin(
    user_id: int,
    new_password: str,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: User = Depends(require_permission(Permission.USER_CHANGE_PASSWORD)),
):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    password_helper = PasswordHelper()
    password_hash = password_helper.hash(new_password)

    user.hashed_password = password_hash

    await session.commit()

    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_admin(
    user_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя",
        )

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    await session.delete(user)
    await session.commit()

    return None