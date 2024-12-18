"""crete users table

Revision ID: f96bc3b2d67d
Revises: 
Create Date: 2024-12-17 18:43:01.950384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f96bc3b2d67d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("users",
                    sa.Column("id", sa.Integer(), nullable=False),
                    sa.Column("chat_id", sa.BigInteger(), nullable=False),
                    sa.Column("full_name", sa.String(), nullable=False),
                    sa.Column("username", sa.String(), nullable=False),
                    sa.Column("is_busy", sa.Boolean(), nullable=False),
                    sa.Column("created_at", sa.DateTime(), nullable=False),
                    sa.Column("last_activity_at", sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint("id"),
                    sa.UniqueConstraint("chat_id"),
                    )


def downgrade() -> None:
    op.drop_table("users")
