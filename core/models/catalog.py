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

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id",
        back_populates="children",
        passive_deletes = True
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent"
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="category",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Category(id={self.id}, название='{self.name}')>"


class Product(IntIdPkMixin, Base):
    name: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True
    )

    category: Mapped["Category | None"] = relationship(
        back_populates="products"
    )
    warehouse_records: Mapped[list["Warehouse"]] = relationship(
        back_populates="product"
    )
    receipt_items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="product"
    )
    writeoff_schedule: Mapped["WriteOffSchedule | None"] = relationship(
        back_populates="product",
        uselist=False
    )

    def __repr__(self):
        return f"<Product(id={self.id}, название='{self.name}')>"