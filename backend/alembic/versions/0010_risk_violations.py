"""add risk_violations table

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_violations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=True),
        sa.Column("client_name", sa.String(128), nullable=True),
        sa.Column("violation_type", sa.String(32), nullable=False),
        sa.Column("violation_count", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("last_action", sa.String(32), nullable=True),
        sa.Column("last_violation_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_violations_user_device", "risk_violations", ["user_id", "device_id"])
    op.create_index("ix_risk_violations_type", "risk_violations", ["violation_type"])


def downgrade() -> None:
    op.drop_index("ix_risk_violations_type", table_name="risk_violations")
    op.drop_index("ix_risk_violations_user_device", table_name="risk_violations")
    op.drop_table("risk_violations")
