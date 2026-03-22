"""fix add server_default to timestamp columns

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ['invite_codes', 'permission_templates', 'invite_usages', 'user_overrides']:
        op.alter_column(table, 'created_at', server_default=sa.func.now())
        op.alter_column(table, 'updated_at', server_default=sa.func.now())


def downgrade() -> None:
    for table in ['invite_codes', 'permission_templates', 'invite_usages', 'user_overrides']:
        op.alter_column(table, 'created_at', server_default=None)
        op.alter_column(table, 'updated_at', server_default=None)
