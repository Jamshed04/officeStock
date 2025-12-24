from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DECIMAL, Boolean, func, Integer


from .base import Base
from .mixins.id_int_pk import IntIdPkMixin


class Warehouse(IntIdPkMixin, Base):
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )
    rest: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3),
        nullable=False,
        default=0
    )
    last_update: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )

    product: Mapped["Product"] = relationship(
        back_populates="warehouse_records"
    )

    def __repr__(self):
        return f"<Warehouse(id={self.id}, товар_id={self.product_id}, остаток={self.rest})>"


class Receipt(IntIdPkMixin, Base):
    order_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    fiscal_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    fiscal_document: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    fiscal_sign: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    sum: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False
    )
    date_buy: Mapped[datetime] = mapped_column(
        nullable=False
    )
    name_supplier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    date_create: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    # Связи
    uploader: Mapped["User | None"] = relationship(
        back_populates="uploaded_receipts",
        foreign_keys=[user_id]
    )
    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt"
    )

    def __repr__(self):
        return f"<Receipt(id={self.id}, заказ='{self.order_name}', сумма={self.sum})>"


class ReceiptItem(IntIdPkMixin, Base):
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id"),
        nullable=False
    )
    product_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    count_product: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3),
        nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False
    )
    sum: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True
    )

    # Связи
    receipt: Mapped["Receipt"] = relationship(
        back_populates="items"
    )
    product: Mapped["Product | None"] = relationship(
        back_populates="receipt_items"
    )

    def __repr__(self):
        return f"<ReceiptItem(id={self.id}, название='{self.product_name}', кол-во={self.count_product})>"



class WriteOffSchedule(IntIdPkMixin, Base):
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        unique=True  # Один товар - одно расписание
    )
    interval_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Интервал списания в днях (раз в n дней)"
    )
    quantity_per_writeoff: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 3),
        nullable=False,
        default=1,
        comment="Количество товара для списания за раз"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активно ли расписание"
    )
    last_writeoff_date: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Дата последнего списания"
    )
    date_create: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    product: Mapped["Product"] = relationship(
        back_populates="writeoff_schedule"
    )

    def repr(self):
        return f"<WriteOffSchedule(id={self.id}, товар_id={self.product_id}, интервал={self.interval_days} дней)>"