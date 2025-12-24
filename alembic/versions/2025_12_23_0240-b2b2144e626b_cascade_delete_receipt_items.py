"""cascade delete receipt items

Revision ID: b2b2144e626b
Revises: 4b8fb4ab125c
Create Date: 2025-12-23 02:40:12.491590

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2b2144e626b"
down_revision: Union[str, Sequence[str], None] = "4b8fb4ab125c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "receipt_items_receipt_id_fkey",
        "receipt_items",
        type_="foreignkey"
    )
    op.create_foreign_key(
        "receipt_items_receipt_id_fkey",
        "receipt_items",
        "receipts",
        ["receipt_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "receipt_items_receipt_id_fkey",
        "receipt_items",
        type_="foreignkey"
    )
    op.create_foreign_key(
        "receipt_items_receipt_id_fkey",
        "receipt_items",
        "receipts",
        ["receipt_id"],
        ["id"]
    )
