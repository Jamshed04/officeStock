"""set null on delete for relations

Revision ID: 4b8fb4ab125c
Revises: cfa7e0571ebb
Create Date: 2025-12-23 01:43:27.520018

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b8fb4ab125c"
down_revision: Union[str, Sequence[str], None] = "cfa7e0571ebb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "products",
        "category_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.drop_constraint(
        "products_category_id_fkey",
        "products",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint(
        "categories_parent_id_fkey",
        "categories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "categories_parent_id_fkey",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column(
        "receipts",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.drop_constraint(
        "receipts_user_id_fkey",
        "receipts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "receipts_user_id_fkey",
        "receipts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "receipts_user_id_fkey",
        "receipts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "receipts_user_id_fkey",
        "receipts",
        "users",
        ["user_id"],
        ["id"],
    )

    op.alter_column(
        "receipts",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint(
        "categories_parent_id_fkey",
        "categories",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "categories_parent_id_fkey",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
    )

    op.drop_constraint(
        "products_category_id_fkey",
        "products",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )

    op.alter_column(
        "products",
        "category_id",
        existing_type=sa.Integer(),
        nullable=False,
    )