"""add emby_webhook_events table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emby_webhook_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("raw_payload", JSONB, nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("emby_user_id", sa.String(256), nullable=True),
        sa.Column("emby_user_name", sa.String(256), nullable=True),
        sa.Column("media_name", sa.String(512), nullable=True),
        sa.Column("media_type", sa.String(64), nullable=True),
        sa.Column("device_name", sa.String(256), nullable=True),
        sa.Column("session_id", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_webhook_events_event_type", "emby_webhook_events", ["event_type"])
    op.create_index("ix_webhook_events_processed", "emby_webhook_events", ["processed"])
    op.create_index("ix_webhook_events_emby_user_id", "emby_webhook_events", ["emby_user_id"])
    op.create_index("ix_webhook_events_event_type_created", "emby_webhook_events", ["event_type", "created_at"])
    op.create_index("ix_webhook_events_user_created", "emby_webhook_events", ["emby_user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("emby_webhook_events")
