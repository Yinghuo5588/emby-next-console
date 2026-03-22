"""notification system refactoring

Revision ID: 0006
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notification_channels',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('channel_type', sa.String(32), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'notification_templates',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('template_type', sa.String(32), nullable=False),
        sa.Column('title_template', sa.String(512), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('variables', postgresql.JSONB(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'notification_rules',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), sa.ForeignKey('notification_channels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', sa.BigInteger(), sa.ForeignKey('notification_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_notification_rules_event', 'notification_rules', ['event_type'])

    op.create_table(
        'user_notification_prefs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('quiet_hours_start', sa.Integer(), nullable=True),
        sa.Column('quiet_hours_end', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'event_type', name='ix_user_notif_prefs_user_event'),
    )

    op.create_table(
        'notification_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), sa.ForeignKey('notification_channels.id'), nullable=True),
        sa.Column('template_id', sa.BigInteger(), sa.ForeignKey('notification_templates.id'), nullable=True),
        sa.Column('recipient_user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(16), server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_notification_logs_event', 'notification_logs', ['event_type'])
    op.create_index('ix_notification_logs_status', 'notification_logs', ['status'])
    op.create_index('ix_notification_logs_created', 'notification_logs', ['created_at'])


def downgrade():
    op.drop_table('notification_logs')
    op.drop_table('user_notification_prefs')
    op.drop_table('notification_rules')
    op.drop_table('notification_templates')
    op.drop_table('notification_channels')