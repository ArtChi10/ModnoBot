"""change period_started_at to timestamptz

Revision ID: bb1aaeb0fb1c
Revises: 94dd16ebce46
Create Date: 2025-05-05 20:39:06.713112

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bb1aaeb0fb1c"
down_revision: str | None = "94dd16ebce46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE user_counters ALTER COLUMN period_started_at TYPE TIMESTAMP WITH TIME ZONE;")


def downgrade() -> None:
    op.execute("ALTER TABLE user_counters ALTER COLUMN period_started_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
