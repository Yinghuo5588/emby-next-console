"""add calendar tables

Revision ID: 0005
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'calendar_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('emby_item_id', sa.String(64), index=True),
        sa.Column('series_name', sa.String(256)),
        sa.Column('season_number', sa.Integer()),
        sa.Column('episode_number', sa.Integer()),
        sa.Column('episode_title', sa.String(256)),
        sa.Column('air_date', sa.Date(), index=True),
        sa.Column('backdrop_url', sa.String(512)),
        sa.Column('overview', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        'content_subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), index=True),
        sa.Column('emby_item_id', sa.String(64)),
        sa.Column('series_name', sa.String(256)),
        sa.Column('notification_methods', postgresql.JSONB(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('content_subscriptions')
    op.drop_table('calendar_entries')