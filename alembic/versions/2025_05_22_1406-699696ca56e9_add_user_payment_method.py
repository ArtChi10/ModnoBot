"""add_user_payment_method

Revision ID: 699696ca56e9
Revises: bb1aaeb0fb1c
Create Date: 2025-05-22 14:06:42.907152

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "699696ca56e9"
down_revision: str | None = "bb1aaeb0fb1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_autopayment_enabled",
            sa.BOOLEAN(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column("users", sa.Column("payment_method_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "payment_method_id")
    op.drop_column("users", "is_autopayment_enabled")
