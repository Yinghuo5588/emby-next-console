"""add invite_codes permission_templates user_overrides

Revision ID: 0003
Revises: 0002_add_webhook_events
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002_add_webhook_events'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'permission_templates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('library_access', postgresql.JSONB(), nullable=True),
        sa.Column('policy_json', postgresql.JSONB(), nullable=True),
        sa.Column('configuration_json', postgresql.JSONB(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_permission_templates_name', 'permission_templates', ['name'])
    
    op.create_table(
        'invite_codes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(32), nullable=False, unique=True),
        sa.Column('template_emby_user_id', sa.String(128), nullable=True),
        sa.Column('permission_template_id', sa.BigInteger(), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('concurrent_limit', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['permission_template_id'], ['permission_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_invite_codes_code', 'invite_codes', ['code'])
    op.create_index('ix_invite_codes_status', 'invite_codes', ['status'])
    op.create_index('ix_invite_codes_created_by', 'invite_codes', ['created_by'])
    
    op.create_table(
        'invite_usages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('invite_id', sa.BigInteger(), nullable=False),
        sa.Column('emby_user_id', sa.String(128), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invite_id'], ['invite_codes.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_invite_usages_invite_id', 'invite_usages', ['invite_id'])
    
    op.create_table(
        'user_overrides',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('emby_user_id', sa.String(128), nullable=False, unique=True),
        sa.Column('concurrent_limit', sa.Integer(), nullable=True),
        sa.Column('max_bitrate', sa.Integer(), nullable=True),
        sa.Column('allow_transcode', sa.Boolean(), nullable=True),
        sa.Column('client_blacklist', postgresql.JSONB(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_overrides_emby_user_id', 'user_overrides', ['emby_user_id'])


def downgrade():
    op.drop_table('user_overrides')
    op.drop_table('invite_usages')
    op.drop_table('invite_codes')
    op.drop_table('permission_templates')