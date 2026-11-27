from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utc_now


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("account_id", "kind", "idempotency_key", name="uq_reading_request"),
        Index("ix_readings_account_created", "account_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    idempotency_key: Mapped[str] = mapped_column(String(80))
    request_data: Mapped[dict] = mapped_column(JSONB)
    result: Mapped[dict] = mapped_column(JSONB)
    rules_version: Mapped[str] = mapped_column(String(32))
    saved: Mapped[bool] = mapped_column(default=False)
    note: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReadingShare(Base):
    __tablename__ = "reading_shares"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reading_id: Mapped[UUID] = mapped_column(
        ForeignKey("readings.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(48))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReadingReport(Base):
    __tablename__ = "reading_reports"
    __table_args__ = (
        UniqueConstraint("account_id", "request_key", name="uq_report_request"),
        Index("ix_reports_account_created", "account_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reading_id: Mapped[UUID | None] = mapped_column(ForeignKey("readings.id", ondelete="SET NULL"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    request_key: Mapped[str] = mapped_column(String(72))
    template: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(48))
    category: Mapped[str] = mapped_column(String(16))
    source: Mapped[dict] = mapped_column(JSONB)
    sections: Mapped[list[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
