"""add_payment_type

Revision ID: 870a627640e6
Revises: cc14b3140121
Create Date: 2025-07-12 18:45:48.851640

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "870a627640e6"
down_revision: str | None = "cc14b3140121"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    payment_type_enum = sa.Enum("RECURRENT", "ONE_TIME", name="paymenttype")
    payment_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "payments",
        sa.Column(
            "payment_type",
            payment_type_enum,
            server_default="ONE_TIME",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("payments", "payment_type")
    sa.Enum(name="paymenttype").drop(op.get_bind(), checkfirst=True)
