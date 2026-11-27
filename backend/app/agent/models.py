from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utc_now

EMBEDDING_DIMENSIONS = 1536


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_account_updated", "account_id", "updated_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(96))
    reading_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("readings.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Turn(Base):
    __tablename__ = "conversation_turns"
    __table_args__ = (
        UniqueConstraint("conversation_id", "client_message_id", name="uq_turn_client_message"),
        Index("ix_turns_conversation_created", "conversation_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    client_message_id: Mapped[UUID]
    attempt_id: Mapped[UUID]
    question: Mapped[str] = mapped_column(Text)
    task: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    reply: Mapped[dict | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    usage: Mapped[dict | None] = mapped_column(JSONB)
    lease_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(32))
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(EMBEDDING_DIMENSIONS))
    embedding_model: Mapped[str | None] = mapped_column(String(240))
