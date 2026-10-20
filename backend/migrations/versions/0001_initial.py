"""Initial frozen schema. No runtime model imports: future models cannot change this migration."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("price_inr", sa.Integer, nullable=False),
        sa.Column("cpu_label", sa.String(100), nullable=False),
        sa.Column("cpu_tier", sa.Integer, nullable=False),
        sa.Column("ram_gb", sa.Integer, nullable=False),
        sa.Column("storage_gb", sa.Integer, nullable=False),
        sa.Column("storage_type", sa.String(30), nullable=False),
        sa.Column("gpu_label", sa.String(100), nullable=False),
        sa.Column("gpu_tier", sa.Integer, nullable=False),
        sa.Column("dedicated_gpu", sa.Boolean),
        sa.Column("vram_gb", sa.Integer),
        sa.Column("weight_kg", sa.Float),
        sa.Column("battery_hours", sa.Float),
        sa.Column("use_case_tags", postgresql.JSONB, nullable=False),
        sa.Column("feature_tags", postgresql.JSONB, nullable=False),
        sa.Column("is_synthetic", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_inr > 0 AND ram_gb > 0 AND storage_gb > 0", name="positive_product_values"),
        sa.CheckConstraint("cpu_tier BETWEEN 1 AND 5 AND gpu_tier BETWEEN 0 AND 5", name="valid_tiers"),
        sa.CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="positive_weight"),
        sa.CheckConstraint("battery_hours IS NULL OR battery_hours > 0", name="positive_battery"),
        sa.CheckConstraint("vram_gb IS NULL OR vram_gb >= 0", name="nonnegative_vram"),
    )
    op.create_index("ix_products_category_price", "products", ["category", "price_inr"])
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("requirements", postgresql.JSONB, nullable=False),
        sa.Column("state_version", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.String(16000), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("client_message_id", sa.String(36)),
        sa.Column("response", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("conversation_id", "sequence", name="uq_message_sequence"),
        sa.UniqueConstraint("conversation_id", "client_message_id", name="uq_client_message"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("source_message_id", sa.String(36), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("requirement_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("products", postgresql.JSONB, nullable=False),
        sa.Column("evidence", postgresql.JSONB, nullable=False),
        sa.Column("eligible_count", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendation_runs_conversation_id", "recommendation_runs", ["conversation_id"])


def downgrade():
    op.drop_table("recommendation_runs")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("products")
