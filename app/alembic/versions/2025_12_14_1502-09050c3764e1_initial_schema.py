"""initial schema

Revision ID: 09050c3764e1
Revises:
Create Date: 2025-12-14 15:02:43.645554

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy


# revision identifiers, used by Alembic.
revision: str = "09050c3764e1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ========================================================================
    # РОЛИ
    # ========================================================================
    op.create_table(
        "roles",
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_name"),
    )

    # ========================================================================
    # ПОЛЬЗОВАТЕЛИ
    # ========================================================================
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=True),
        sa.Column("date_join", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ========================================================================
    # ТОКЕНЫ ДОСТУПА
    # ========================================================================
    op.create_table(
        "access_tokens",
        sa.Column("token", sa.String(length=43), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            fastapi_users_db_sqlalchemy.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(
        op.f("ix_access_tokens_created_at"),
        "access_tokens",
        ["created_at"],
        unique=False,
    )

    # ========================================================================
    # ТОВАРЫ
    # ========================================================================
    op.create_table(
        "products",
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ========================================================================
    # ЧЕКИ
    # ========================================================================
    op.create_table(
        "receipts",
        sa.Column("order_name", sa.String(length=255), nullable=True),
        sa.Column("fiscal_number", sa.String(length=50), nullable=True),
        sa.Column("fiscal_document", sa.String(length=50), nullable=True),
        sa.Column("fiscal_sign", sa.String(length=50), nullable=True),
        sa.Column("sum", sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column("date_buy", sa.DateTime(), nullable=False),
        sa.Column("name_supplier", sa.String(length=255), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date_create", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================================
    # ПОЗИЦИИ ЧЕКА
    # ========================================================================
    op.create_table(
        "receipt_items",
        sa.Column("receipt_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=500), nullable=False),
        sa.Column("count_product", sa.DECIMAL(precision=10, scale=3), nullable=False),
        sa.Column("unit_price", sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column("sum", sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================================
    # СКЛАД
    # ========================================================================
    op.create_table(
        "warehouses",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("rest", sa.DECIMAL(precision=10, scale=3), nullable=False),
        sa.Column(
            "last_update",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("warehouses")
    op.drop_table("receipt_items")
    op.drop_table("receipts")
    op.drop_table("products")
    op.drop_index(op.f("ix_access_tokens_created_at"), table_name="access_tokens")
    op.drop_table("access_tokens")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("categories")
    pass
