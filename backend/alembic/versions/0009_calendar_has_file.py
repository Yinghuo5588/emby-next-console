"""add has_file to calendar_entries

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("calendar_entries", sa.Column("has_file", sa.Boolean(), server_default="false"))


def downgrade() -> None:
    op.drop_column("calendar_entries", "has_file")
