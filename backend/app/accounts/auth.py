from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated, Literal

from anyio import CapacityLimiter, to_thread
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import Account, LoginSession
from app.core.config import Settings
from app.core.db import DbSession, utc_now
from app.core.errors import ApiError

COOKIE_NAME = "xuanji_session"
DEVELOPMENT_ADMIN_USERNAME = "admin"
type Transport = Literal["web", "bearer"]

_passwords = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)
_password_slots = CapacityLimiter(2)
_dummy_hash = _passwords.hash(token_urlsafe(32))
_bearer = HTTPBearer(auto_error=False)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    username: str | None
    email: str | None
    is_guest: bool
    wechat_linked: bool
    password_set: bool
    is_admin: bool
    details: dict


class SessionOut(BaseModel):
    account: AccountOut
    access_token: str | None = None
    expires_in: int
    handoff_reading_id: str | None = None


def account_out(account: Account) -> AccountOut:
    return AccountOut(
        id=str(account.id),
        display_name=account.display_name,
        username=account.username,
        email=account.email,
        is_guest=account.is_guest,
        wechat_linked=account.wechat_open_id is not None,
        password_set=account.password_hash is not None,
        is_admin=account.is_development_admin,
        details=account.details,
    )


def digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


async def password_hash(password: str) -> str:
    return await to_thread.run_sync(_passwords.hash, password, limiter=_password_slots)


async def provision_development_admin(db: AsyncSession, settings: Settings) -> None:
    password = settings.development_admin_password
    if not settings.development_admin_enabled or password is None:
        return
    if await db.scalar(select(Account.id).where(Account.username == DEVELOPMENT_ADMIN_USERNAME)):
        return
    hashed = await password_hash(password.get_secret_value())
    await db.execute(
        insert(Account)
        .values(
            username=DEVELOPMENT_ADMIN_USERNAME,
            display_name="管理员",
            password_hash=hashed,
            is_development_admin=True,
        )
        .on_conflict_do_nothing(index_elements=[Account.username])
    )
    await db.commit()


async def password_matches(hash_value: str | None, password: str) -> bool:
    try:
        valid = await to_thread.run_sync(
            _passwords.verify, hash_value or _dummy_hash, password, limiter=_password_slots
        )
    except (VerificationError, InvalidHashError):
        return False
    return valid and hash_value is not None


async def issue_session(
    db: DbSession, request: Request, response: Response, account: Account, transport: Transport
) -> SessionOut:
    settings = request.app.state.settings
    if account.is_development_admin and not settings.development_admin_enabled:
        raise ApiError(403, "development_admin_disabled", "开发管理员已停用。")
    ttl = timedelta(days=settings.session_days)
    token = token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=digest(token),
            account_id=account.id,
            transport=transport,
            expires_at=utc_now() + ttl,
        )
    )
    await db.commit()
    if transport == "web":
        response.set_cookie(
            COOKIE_NAME,
            token,
            secure=settings.cookie_secure,
            httponly=True,
            samesite="lax",
            max_age=int(ttl.total_seconds()),
            path="/api",
        )
    return SessionOut(
        account=account_out(account),
        access_token=token if transport == "bearer" else None,
        expires_in=int(ttl.total_seconds()),
    )


async def optional_identity(
    request: Request,
    db: DbSession,
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> tuple[LoginSession, Account] | None:
    return await _presented_identity(request, db, bearer)


async def current_visitor(request: Request, db: DbSession) -> Account | None:
    try:
        result = await _presented_identity(request, db, await _bearer(request))
    except ApiError as error:
        if error.status != 401:
            raise
        return None
    return result[1] if result and result[1].is_guest else None


async def _presented_identity(
    request: Request, db: DbSession, bearer: HTTPAuthorizationCredentials | None
) -> tuple[LoginSession, Account] | None:
    authorization = request.headers.get("Authorization")
    if authorization is not None:
        if bearer is None:
            raise ApiError(401, "invalid_token", "登录凭证无效。")
        token = bearer.credentials
        transport = "bearer"
    else:
        token = request.cookies.get(COOKIE_NAME)
        transport = "web"

    if token is None:
        return None
    if len(token) != 43:
        raise ApiError(401, "invalid_token", "登录凭证无效。")
    if transport == "web" and request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("Origin")
        if origin not in request.app.state.settings.web_origins:
            raise ApiError(403, "invalid_origin", "请求来源未授权。")

    result = (
        await db.execute(
            select(LoginSession, Account)
            .join(Account, Account.id == LoginSession.account_id)
            .where(
                LoginSession.token_hash == digest(token),
                LoginSession.transport == transport,
                LoginSession.expires_at > utc_now(),
            )
        )
    ).one_or_none()
    if result is None:
        raise ApiError(401, "session_expired", "会话已失效，请重新进入。")
    login_session, account = result
    if account.is_development_admin and not request.app.state.settings.development_admin_enabled:
        raise ApiError(401, "session_expired", "会话已失效，请重新进入。")
    return login_session, account


OptionalIdentity = Annotated[tuple[LoginSession, Account] | None, Depends(optional_identity)]


def identity(current: OptionalIdentity) -> tuple[LoginSession, Account]:
    if current is None:
        raise ApiError(401, "session_required", "请先建立访客会话或登录。")
    return current


Identity = Annotated[tuple[LoginSession, Account], Depends(identity)]


def actor(current: Identity) -> Account:
    return current[1]


Actor = Annotated[Account, Depends(actor)]


def member(account: Actor) -> Account:
    if account.is_guest:
        raise ApiError(403, "account_required", "请先登录账号。")
    return account


Member = Annotated[Account, Depends(member)]
