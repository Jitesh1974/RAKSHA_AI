from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=False)
    op.create_index("ix_devices_token_hash", "devices", ["token_hash"], unique=False)

    op.create_table(
        "security_events",
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("source_app", sa.String(length=128), nullable=False),
        sa.Column("sender", sa.String(length=512), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("event_timestamp", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_security_events_device_id", "security_events", ["device_id"], unique=False)
    op.create_index("ix_security_events_device_created", "security_events", ["device_id", "created_at"], unique=False)

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("scam_category", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["security_events.event_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_analysis_results_event_id", "analysis_results", ["event_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_analysis_results_event_id", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index("ix_security_events_device_created", table_name="security_events")
    op.drop_index("ix_security_events_device_id", table_name="security_events")
    op.drop_table("security_events")
    op.drop_index("ix_devices_token_hash", table_name="devices")
    op.drop_index("ix_devices_device_id", table_name="devices")
    op.drop_table("devices")
