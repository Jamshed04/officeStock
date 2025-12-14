from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, ForeignKey, func
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.id_int_pk import IntIdPkMixin

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.models import AccessToken, Receipt, Role


class Role(IntIdPkMixin, Base):
    role_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    # Связь с пользователями (один ко многим)
    users: Mapped[list["User"]] = relationship(
        back_populates="role",
        lazy="raise"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, название='{self.role_name}')>"


class User(Base, IntIdPkMixin, SQLAlchemyBaseUserTable[int]):
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    position: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    date_join: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    # Внешний ключ на роль
    role_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True
    )

    # Связи
    role:  Mapped[Optional["Role"]] = relationship(
        back_populates="users",
        lazy="raise"
    )
    uploaded_receipts: Mapped[list["Receipt"]] = relationship(
        back_populates="uploader",
        foreign_keys="[Receipt.user_id]",
        lazy="raise"
    )

    @classmethod
    def get_db(cls, session: "AsyncSession"):
        return SQLAlchemyUserDatabase(session, cls)


    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"