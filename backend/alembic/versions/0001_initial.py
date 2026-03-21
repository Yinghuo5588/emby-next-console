"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
 # ── users ──────────────────────────────────────────────────────────────
 op.create_table(
 "users",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("emby_user_id", sa.String(128), unique=True, nullable=True),
 sa.Column("username", sa.String(128), nullable=False, unique=True),
 sa.Column("hashed_password", sa.String(256), nullable=True),
 sa.Column("display_name", sa.String(128), nullable=True),
 sa.Column("role", sa.String(32), nullable=False, server_default="user"),
 sa.Column("status", sa.String(32), nullable=False, server_default="active"),
 sa.Column("source", sa.String(32), nullable=False, server_default="local"),
 sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_users_username", "users", ["username"])
 op.create_index("ix_users_status", "users", ["status"])

 # ── user_profiles ───────────────────────────────────────────────────────
 op.create_table(
 "user_profiles",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
 sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("note", sa.Text(), nullable=True),
 sa.Column("is_vip", sa.Boolean(), nullable=False, server_default="false"),
 sa.Column("max_concurrent", sa.Integer(), nullable=True),
 sa.Column("avatar_url", sa.String(512), nullable=True),
 sa.Column("tags_json", JSONB(), nullable=True),
 sa.Column("metadata_json", JSONB(), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_user_profiles_expire_at", "user_profiles", ["expire_at"])
 op.create_index("ix_user_profiles_is_vip", "user_profiles", ["is_vip"])

 # ── playback_events ─────────────────────────────────────────────────────
 op.create_table(
 "playback_events",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
 sa.Column("emby_session_id", sa.String(256), nullable=True),
 sa.Column("media_id", sa.String(256), nullable=False),
 sa.Column("media_type", sa.String(64), nullable=False),
 sa.Column("media_name", sa.String(512), nullable=False),
 sa.Column("series_name", sa.String(512), nullable=True),
 sa.Column("season_number", sa.Integer(), nullable=True),
 sa.Column("episode_number", sa.Integer(), nullable=True),
 sa.Column("client_name", sa.String(128), nullable=True),
 sa.Column("device_name", sa.String(256), nullable=True),
 sa.Column("device_id", sa.String(256), nullable=True),
 sa.Column("ip_address", sa.String(64), nullable=True),
 sa.Column("play_duration_sec", sa.Integer(), nullable=False, server_default="0"),
 sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
 sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_playback_events_user_id", "playback_events", ["user_id"])
 op.create_index("ix_playback_events_media_id", "playback_events", ["media_id"])
 op.create_index("ix_playback_events_started_at", "playback_events", ["started_at"])
 op.create_index("ix_playback_events_user_started", "playback_events", ["user_id", "started_at"])
 op.create_index("ix_playback_events_mediatype_started", "playback_events", ["media_type", "started_at"])

 # ── playback_sessions ───────────────────────────────────────────────────
 op.create_table(
 "playback_sessions",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
 sa.Column("emby_session_id", sa.String(256), unique=True, nullable=False),
 sa.Column("status", sa.String(32), nullable=False, server_default="active"),
 sa.Column("media_id", sa.String(256), nullable=False),
 sa.Column("media_name", sa.String(512), nullable=False),
 sa.Column("client_name", sa.String(128), nullable=True),
 sa.Column("device_name", sa.String(256), nullable=True),
 sa.Column("device_id", sa.String(256), nullable=True),
 sa.Column("ip_address", sa.String(64), nullable=True),
 sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
 sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
 sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_playback_sessions_user_id", "playback_sessions", ["user_id"])
 op.create_index("ix_playback_sessions_status", "playback_sessions", ["status"])
 op.create_index("ix_playback_sessions_last_seen_at", "playback_sessions", ["last_seen_at"])

 # ── risk_rules ──────────────────────────────────────────────────────────
 op.create_table(
 "risk_rules",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("rule_key", sa.String(128), unique=True, nullable=False),
 sa.Column("rule_name", sa.String(256), nullable=False),
 sa.Column("rule_type", sa.String(64), nullable=False),
 sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
 sa.Column("severity", sa.String(32), nullable=False, server_default="medium"),
 sa.Column("config_json", JSONB(), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )

 # ── risk_events ─────────────────────────────────────────────────────────
 op.create_table(
 "risk_events",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
 sa.Column("rule_id", sa.BigInteger(), sa.ForeignKey("risk_rules.id", ondelete="SET NULL"), nullable=True),
 sa.Column("event_type", sa.String(64), nullable=False),
 sa.Column("severity", sa.String(32), nullable=False, server_default="medium"),
 sa.Column("status", sa.String(32), nullable=False, server_default="open"),
 sa.Column("title", sa.String(512), nullable=False),
 sa.Column("description", sa.Text(), nullable=True),
 sa.Column("context_json", JSONB(), nullable=True),
 sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
 sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_risk_events_user_id", "risk_events", ["user_id"])
 op.create_index("ix_risk_events_status", "risk_events", ["status"])
 op.create_index("ix_risk_events_severity", "risk_events", ["severity"])
 op.create_index("ix_risk_events_detected_at", "risk_events", ["detected_at"])

 # ── notifications ───────────────────────────────────────────────────────
 op.create_table(
 "notifications",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
 sa.Column("type", sa.String(64), nullable=False),
 sa.Column("title", sa.String(512), nullable=False),
 sa.Column("message", sa.Text(), nullable=False),
 sa.Column("level", sa.String(32), nullable=False, server_default="info"),
 sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
 sa.Column("action_url", sa.String(512), nullable=True),
 sa.Column("source_type", sa.String(64), nullable=True),
 sa.Column("source_id", sa.String(128), nullable=True),
 sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
 op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
 op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
 op.create_index("ix_notifications_user_is_read", "notifications", ["user_id", "is_read"])

 # ── system_settings ─────────────────────────────────────────────────────
 op.create_table(
 "system_settings",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("setting_key", sa.String(128), unique=True, nullable=False),
 sa.Column("setting_group", sa.String(64), nullable=False, server_default="general"),
 sa.Column("value_json", JSONB(), nullable=True),
 sa.Column("description", sa.Text(), nullable=True),
 sa.Column("updated_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
 sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
 )
 op.create_index("ix_system_settings_setting_group", "system_settings", ["setting_group"])

 # ── job_runs ─────────────────────────────────────────────────────────────
 op.create_table(
 "job_runs",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("job_type", sa.String(128), nullable=False),
 sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
 sa.Column("payload_json", JSONB(), nullable=True),
 sa.Column("result_json", JSONB(), nullable=True),
 sa.Column("error_message", sa.Text(), nullable=True),
 sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_job_runs_job_type", "job_runs", ["job_type"])
 op.create_index("ix_job_runs_status", "job_runs", ["status"])
 op.create_index("ix_job_runs_created_at", "job_runs", ["created_at"])

 # ── audit_logs ───────────────────────────────────────────────────────────
 op.create_table(
 "audit_logs",
 sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
 sa.Column("actor_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
 sa.Column("action_type", sa.String(128), nullable=False),
 sa.Column("target_type", sa.String(128), nullable=False),
 sa.Column("target_id", sa.String(256), nullable=False),
 sa.Column("detail_json", JSONB(), nullable=True),
 sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
 )
 op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
 op.create_index("ix_audit_logs_action_type", "audit_logs", ["action_type"])
 op.create_index("ix_audit_logs_target_type_id", "audit_logs", ["target_type", "target_id"])
 op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

def downgrade() -> None:
 op.drop_table("audit_logs")
 op.drop_table("job_runs")
 op.drop_table("system_settings")
 op.drop_table("notifications")
 op.drop_table("risk_events")
 op.drop_table("risk_rules")
 op.drop_table("playback_sessions")
 op.drop_table("playback_events")
 op.drop_table("user_profiles")
 op.drop_table("users")