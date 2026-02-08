"""add_sub_duration

Revision ID: cc14b3140121
Revises: 11701b1cff60
Create Date: 2025-07-06 04:17:48.375196

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc14b3140121"
down_revision: str | None = "11701b1cff60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    paidentity_enum = sa.Enum("ONE_MONTH_SUBSCRIPTION", "ONE_YEAR_SUBSCRIPTION", name="paidentity")
    paidentity_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "subscription_duration",
            paidentity_enum,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "subscription_duration")
    sa.Enum(name="paidentity").drop(op.get_bind(), checkfirst=True)
