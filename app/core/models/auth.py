from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Table, Column, Integer, ForeignKey, func
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.id_int_pk import IntIdPkMixin

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.models import AccessToken, Order, Receipt, WriteOffRequest, Role

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class Role(IntIdPkMixin, Base):
    role_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    # Связь с пользователями через промежуточную таблицу
    users: Mapped[list["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles"
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

    # Связи
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="raise"
    )
    created_orders: Mapped[list["Order"]] = relationship(
        back_populates="creator",
        foreign_keys="[Order.user_id]",
        lazy="raise"
    )
    uploaded_receipts: Mapped[list["Receipt"]] = relationship(
        back_populates="uploader",
        foreign_keys="[Receipt.user_id]",
        lazy="raise"
    )
    write_off_requests: Mapped[list["WriteOffRequest"]] = relationship(
        back_populates="creator",
        foreign_keys="[WriteOffRequest.user_id]",
        lazy="raise"
    )

    @classmethod
    def get_db(cls, session: "AsyncSession"):
        return SQLAlchemyUserDatabase(session, cls)


    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"