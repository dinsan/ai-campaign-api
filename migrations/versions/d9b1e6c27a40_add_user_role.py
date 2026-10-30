"""add role to users

Revision ID: d9b1e6c27a40
Revises: c4e7f3a9d215
Create Date: 2026-10-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9b1e6c27a40"
down_revision: Union[str, Sequence[str], None] = "c4e7f3a9d215"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="viewer",
        ),
    )

    # Accounts created before roles existed could already edit and delete.
    # Keep that ability so the upgrade does not lock anyone out; newly
    # registered users start as read-only viewers. Promote the first
    # administrator manually, e.g.:
    #   UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
    op.execute("UPDATE users SET role = 'editor'")


def downgrade() -> None:
    op.drop_column("users", "role")
