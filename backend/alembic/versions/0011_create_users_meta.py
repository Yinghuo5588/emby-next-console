"""create users_meta table

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"


def upgrade():
    op.create_table(
        "users_meta",
        sa.Column("user_id", sa.String(128), primary_key=True),
        sa.Column("expire_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_concurrent", sa.Integer, nullable=False, server_default="2"),
        sa.Column("is_vip", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("template_name", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("users_meta")
