"""add risk_action_logs table

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_action_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("target", sa.String(256), nullable=False),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_action_logs_created_at", "risk_action_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_risk_action_logs_created_at", table_name="risk_action_logs")
    op.drop_table("risk_action_logs")
