from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.id_int_pk import IntIdPkMixin


class Category(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True
    )

    # Связи для иерархии
    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent"
    )

    # Связь с товарами
    products: Mapped[list["Product"]] = relationship(
        back_populates="category"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, название='{self.name}')>"


class Product(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    # Связи
    category: Mapped["Category"] = relationship(
        back_populates="products"
    )
    warehouse_records: Mapped[list["Warehouse"]] = relationship(
        back_populates="product"
    )
    receipt_items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="product"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, название='{self.name}')>"