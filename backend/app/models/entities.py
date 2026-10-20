"""SQLAlchemy tables; PostgreSQL uses JSONB, unit tests may use SQLite JSON."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


J = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_inr > 0 AND ram_gb > 0 AND storage_gb > 0", name="positive_product_values"),
        CheckConstraint("cpu_tier BETWEEN 1 AND 5 AND gpu_tier BETWEEN 0 AND 5", name="valid_tiers"),
        CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="positive_weight"),
        CheckConstraint("battery_hours IS NULL OR battery_hours > 0", name="positive_battery"),
        CheckConstraint("vram_gb IS NULL OR vram_gb >= 0", name="nonnegative_vram"),
        Index("ix_products_category_price", "category", "price_inr"),
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(30), default="laptop")
    price_inr: Mapped[int] = mapped_column(Integer)
    cpu_label: Mapped[str] = mapped_column(String(100))
    cpu_tier: Mapped[int] = mapped_column(Integer)
    ram_gb: Mapped[int] = mapped_column(Integer)
    storage_gb: Mapped[int] = mapped_column(Integer)
    storage_type: Mapped[str] = mapped_column(String(30))
    gpu_label: Mapped[str] = mapped_column(String(100))
    gpu_tier: Mapped[int] = mapped_column(Integer)
    dedicated_gpu: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    vram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    use_case_tags: Mapped[list] = mapped_column(J)
    feature_tags: Mapped[list] = mapped_column(J)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    requirements: Mapped[dict] = mapped_column(J, default=dict)
    state_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence", name="uq_message_sequence"),
        UniqueConstraint("conversation_id", "client_message_id", name="uq_client_message"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(String(16000))
    sequence: Mapped[int] = mapped_column(Integer)
    client_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    response: Mapped[dict | None] = mapped_column(J, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    source_message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    requirement_snapshot: Mapped[dict] = mapped_column(J)
    products: Mapped[list] = mapped_column(J)
    evidence: Mapped[dict] = mapped_column(J)
    eligible_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
