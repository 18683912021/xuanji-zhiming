import hmac
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage
from secrets import randbelow
from typing import Literal
from uuid import UUID, uuid4

from anyio import CapacityLimiter, to_thread
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import EmailChallenge, PasswordAttempt
from app.core.config import Settings
from app.core.db import utc_now
from app.core.errors import ApiError

type Purpose = Literal["bind_email", "reset_password"]

COOLDOWN = 30
TTL = timedelta(minutes=5)
MAX_ATTEMPTS = 5
mail_slots = CapacityLimiter(2)
LABELS = {"bind_email": "绑定邮箱", "reset_password": "重设密码"}


def _secret(settings: Settings) -> bytes:
    if not settings.email_codes_enabled or settings.auth_code_secret is None:
        raise ApiError(503, "email_unavailable", "邮件验证码服务暂不可用。")
    return settings.auth_code_secret.get_secret_value().encode()


def _code_hash(
    secret: bytes, email: str, purpose: Purpose, code: str, nonce: UUID, owner: UUID | None
) -> str:
    scope = f"{purpose}:{email}:{nonce}:{code}"
    if owner is not None:
        scope += f":{owner}"
    return hmac.digest(secret, scope.encode(), "sha256").hex()


def _send_smtp(settings: Settings, email: str, purpose: Purpose, code: str):
    message = EmailMessage()
    message["Subject"] = "玄机知命 · " + LABELS[purpose] + "验证码"
    message["From"] = settings.smtp_sender
    message["To"] = email
    message.set_content(f"你的{LABELS[purpose]}验证码为 {code}，5 分钟内有效。")
    context = ssl.create_default_context()
    if settings.smtp_security == "tls":
        connection = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=6, context=context
        )
    else:
        connection = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=6)
    with connection as smtp:
        if settings.smtp_security == "starttls":
            smtp.starttls(context=context)
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        smtp.send_message(message)


async def deliver_code(settings: Settings, email: str, purpose: Purpose, code: str):
    await to_thread.run_sync(_send_smtp, settings, email, purpose, code, limiter=mail_slots)


async def issue_code(
    db: AsyncSession,
    settings: Settings,
    email: str,
    purpose: Purpose,
    entitled: bool,
    *,
    owner: UUID | None = None,
):
    secret = _secret(settings)
    now = utc_now()
    code = f"{randbelow(1_000_000):06}"
    nonce = uuid4()
    data = {
        "code_hash": _code_hash(secret, email, purpose, code, nonce, owner),
        "nonce": nonce,
        "attempts": 0,
        "expires_at": now + TTL if entitled else now,
        "resend_at": now + timedelta(seconds=COOLDOWN),
    }
    challenge = await db.scalar(
        insert(EmailChallenge)
        .values(email=email, purpose=purpose, **data)
        .on_conflict_do_update(
            index_elements=[EmailChallenge.email, EmailChallenge.purpose],
            set_=data,
            where=EmailChallenge.resend_at <= now,
        )
        .returning(EmailChallenge.nonce)
    )
    if challenge is None:
        raise ApiError(429, "code_cooldown", "验证码发送过于频繁，请稍后再试。")
    await db.commit()

    if not entitled:
        # Reserve the same cooldown without sending mail for an inapplicable action.
        return
    try:
        await deliver_code(settings, email, purpose, code)
    except (OSError, smtplib.SMTPException) as error:
        await db.execute(
            delete(EmailChallenge).where(
                EmailChallenge.email == email,
                EmailChallenge.purpose == purpose,
                EmailChallenge.nonce == nonce,
            )
        )
        await db.commit()
        raise ApiError(503, "email_delivery_failed", "邮件暂时不能发送，请稍后重试。") from error


async def consume_code(
    db: AsyncSession,
    settings: Settings,
    email: str,
    purpose: Purpose,
    code: str,
    *,
    owner: UUID | None = None,
):
    secret = _secret(settings)
    row = await db.get(EmailChallenge, (email, purpose), with_for_update=True)
    if row is None or row.expires_at <= utc_now():
        raise ApiError(401, "code_expired", "验证码无效或已过期，请重新获取。")
    if row.attempts >= MAX_ATTEMPTS:
        raise ApiError(429, "code_attempts_exceeded", "验证码尝试次数已用完，请重新获取。")
    if not hmac.compare_digest(
        row.code_hash, _code_hash(secret, email, purpose, code, row.nonce, owner)
    ):
        row.attempts += 1
        await db.commit()
        raise ApiError(401, "code_invalid", "验证码不正确。")
    await db.delete(row)


async def password_window(
    db: AsyncSession, identifier: str, *, enforce: bool = True
) -> PasswordAttempt:
    now = utc_now()
    await db.execute(
        insert(PasswordAttempt)
        .values(identifier=identifier, attempts=0, expires_at=now + TTL)
        .on_conflict_do_nothing(index_elements=[PasswordAttempt.identifier])
    )
    row = await db.get(PasswordAttempt, identifier, with_for_update=True)
    assert row is not None
    if row.expires_at <= now:
        row.attempts = 0
        row.expires_at = now + TTL
    if enforce and row.attempts >= MAX_ATTEMPTS:
        raise ApiError(
            429, "password_attempts_exceeded", "密码尝试次数过多，请稍后重试或找回密码。"
        )
    return row
