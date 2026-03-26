"""create quality_items and quality_ignore tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"


def upgrade():
    op.create_table(
        "quality_items",
        sa.Column("item_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("path", sa.Text, nullable=True),
        sa.Column("resolution", sa.String(16), nullable=False),  # 4K / 1080P / 720P / SD
        sa.Column("video_range", sa.String(16), nullable=False, server_default="SDR"),  # DV / HDR10 / SDR
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("item_type", sa.String(32), nullable=False),  # Movie / Episode
        sa.Column("poster_url", sa.Text, nullable=True),
        sa.Column("is_ignored", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quality_items_resolution", "quality_items", ["resolution"])
    op.create_index("ix_quality_items_video_range", "quality_items", ["video_range"])
    op.create_index("ix_quality_items_is_ignored", "quality_items", ["is_ignored"])


def downgrade():
    op.drop_table("quality_items")
