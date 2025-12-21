"""add_writeoff

Revision ID: cfa7e0571ebb
Revises: 09050c3764e1
Create Date: 2025-12-17 13:26:06.618538

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cfa7e0571ebb"
down_revision: Union[str, Sequence[str], None] = "09050c3764e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "write_off_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantity_per_writeoff", sa.DECIMAL(10, 3), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_writeoff_date", sa.DateTime(), nullable=True),
        sa.Column("date_create", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("write_off")
