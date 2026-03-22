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
    # permission_templates 和 invite_codes: 有 created_at + updated_at
    for table in ['permission_templates', 'invite_codes']:
        op.alter_column(table, 'created_at', server_default=sa.func.now())
        op.alter_column(table, 'updated_at', server_default=sa.func.now())
    # user_overrides: 只有 updated_at
    op.alter_column('user_overrides', 'updated_at', server_default=sa.func.now())
    # invite_usages: 没有 created_at/updated_at，只有 used_at，跳过


def downgrade() -> None:
    for table in ['permission_templates', 'invite_codes']:
        op.alter_column(table, 'created_at', server_default=None)
        op.alter_column(table, 'updated_at', server_default=None)
    op.alter_column('user_overrides', 'updated_at', server_default=None)
