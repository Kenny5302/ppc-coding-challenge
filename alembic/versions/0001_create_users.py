"""create users table"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("age", sa.Integer, nullable=False),
        sa.Column("birth_state", sa.String(2), nullable=False),
    )
    op.create_index("ix_users_birth_state", "users", ["birth_state"])


def downgrade() -> None:
    op.drop_index("ix_users_birth_state", table_name="users")
    op.drop_table("users")
