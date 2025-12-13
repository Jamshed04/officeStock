from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, DECIMAL, func

from .base import Base
from .mixins.id_int_pk import IntIdPkMixin


class WriteOffRequest(IntIdPkMixin, Base):
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )
    count_write_off: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3),
        nullable=False
    )
    reason_write_off: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    status_application: Mapped[str] = mapped_column(
        String(50),
        default='ожидание'
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    date_create: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    date_execution: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    # Связи
    product: Mapped["Product"] = relationship(
        back_populates="write_off_requests"
    )
    creator: Mapped["User"] = relationship(
        back_populates="write_off_requests",
        foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<WriteOffRequest(id={self.id}, товар_id={self.product_id}, статус='{self.status_application}')>"