from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.id_int_pk import IntIdPkMixin


class OrderStatus(IntIdPkMixin, Base):
    status_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Связь с заказами
    orders: Mapped[list["Order"]] = relationship(
        back_populates="status"
    )

    def __repr__(self):
        return f"<OrderStatus(id={self.id}, название='{self.status_name}')>"


class Order(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("order_statuses.id"),
        default=1
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    date_create: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )

    # Связи
    status: Mapped["OrderStatus"] = relationship(
        back_populates="orders"
    )
    creator: Mapped["User"] = relationship(
        back_populates="created_orders",
        foreign_keys=[user_id]
    )
    receipts: Mapped[list["Receipt"]] = relationship(
        back_populates="order"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, название='{self.name}')>"