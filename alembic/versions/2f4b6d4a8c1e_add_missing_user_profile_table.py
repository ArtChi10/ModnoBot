"""add missing user_profile table

Revision ID: 2f4b6d4a8c1e
Revises: 667fd9ee58ce
Create Date: 2026-02-09 10:25:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f4b6d4a8c1e"
down_revision: Union[str, None] = "667fd9ee58ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "user_profile"
INDEX_NAME = "ix_user_profile_user_id"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table(TABLE_NAME):
        op.create_table(
            TABLE_NAME,
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("city", sa.String(), nullable=True),
            sa.Column("lat", sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column("lon", sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column("allow_location", sa.BOOLEAN(), server_default="false", nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes(TABLE_NAME)}
    if INDEX_NAME not in existing_indexes:
        op.create_index(INDEX_NAME, TABLE_NAME, ["user_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table(TABLE_NAME):
        existing_indexes = {index["name"] for index in inspector.get_indexes(TABLE_NAME)}
        if INDEX_NAME in existing_indexes:
            op.drop_index(INDEX_NAME, table_name=TABLE_NAME)
        op.drop_table(TABLE_NAME)