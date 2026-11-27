from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utc_now


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("wechat_app_id", "wechat_open_id", name="uq_account_wechat"),
        UniqueConstraint("username", name="uq_account_username"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    username: Mapped[str | None] = mapped_column(String(24))
    is_development_admin: Mapped[bool] = mapped_column(default=False, server_default="false")
    password_hash: Mapped[str | None] = mapped_column(Text)
    wechat_app_id: Mapped[str | None] = mapped_column(String(32))
    wechat_open_id: Mapped[str | None] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(48), default="访客")
    details: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def is_guest(self) -> bool:
        return self.username is None and self.email is None and self.wechat_open_id is None


class LoginSession(Base):
    __tablename__ = "login_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    transport: Mapped[str] = mapped_column(String(8))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class BirthProfile(Base):
    __tablename__ = "birth_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(48))
    birth: Mapped[dict] = mapped_column(JSONB)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (UniqueConstraint("account_id", "entry_date", name="uq_journal_account_date"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    entry_date: Mapped[date]
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    reading_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("readings.id", ondelete="SET NULL"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EmailChallenge(Base):
    __tablename__ = "email_challenges"

    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(20), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    nonce: Mapped[UUID] = mapped_column(default=uuid4)
    attempts: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resend_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PasswordAttempt(Base):
    __tablename__ = "password_attempts"

    identifier: Mapped[str] = mapped_column(String(254), primary_key=True)
    attempts: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
