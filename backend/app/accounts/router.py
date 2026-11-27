from datetime import date, datetime
from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.accounts import wechat
from app.accounts.auth import (
    COOKIE_NAME,
    DEVELOPMENT_ADMIN_USERNAME,
    AccountOut,
    Identity,
    Member,
    OptionalIdentity,
    SessionOut,
    Transport,
    account_out,
    current_visitor,
    issue_session,
    password_hash,
    password_matches,
)
from app.accounts.models import Account, BirthProfile, JournalEntry, LoginSession, PasswordAttempt
from app.accounts.verification import COOLDOWN, consume_code, issue_code, password_window
from app.core.config import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.core.db import DbSession, utc_now
from app.core.errors import ApiError
from app.readings.bazi import BirthInput
from app.readings.models import Reading

router = APIRouter(prefix="/auth", tags=["账号"])
private = APIRouter(prefix="/me", tags=["个人资料"])

type Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=48)]
type Password = Annotated[
    str, StringConstraints(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
]
type CurrentPassword = Annotated[
    str, StringConstraints(min_length=1, max_length=MAX_PASSWORD_LENGTH)
]
type Username = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-zA-Z][a-zA-Z0-9_]{2,23}$")
]
type WeChatCode = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)
]
type ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=48)]


class GuestInput(BaseModel):
    transport: Transport = "web"


type Code = Annotated[str, StringConstraints(pattern=r"^[0-9]{6}$")]


class LoginTarget(GuestInput):
    carry_reading_id: UUID | None = None


class LoginInput(LoginTarget):
    identifier: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=254)
    ] = Field(validation_alias=AliasChoices("identifier", "email"))
    password: CurrentPassword


class EmailInput(BaseModel):
    email: EmailStr


class ResetInput(EmailInput):
    code: Code
    password: Password


class RegisterInput(GuestInput):
    username: Username
    password: Password
    display_name: Name | None = None


class CredentialsInput(BaseModel):
    username: Username | None = None
    password: Password | None = None
    current_password: CurrentPassword | None = None
    wechat_code: WeChatCode | None = None

    @model_validator(mode="after")
    def validate_change(self) -> "CredentialsInput":
        if self.username is None and self.password is None:
            raise ValueError("请输入用户名或新密码。")
        if (self.current_password is None) == (self.wechat_code is None):
            raise ValueError("请选择一种身份验证方式。")
        return self


class BindEmailInput(EmailInput):
    code: Code
    current_password: CurrentPassword


class WeChatInput(BaseModel):
    code: WeChatCode
    carry_reading_id: UUID | None = None


@router.get("/status")
async def auth_status(request: Request) -> dict[str, bool]:
    settings = request.app.state.settings
    return {
        "email_codes": settings.email_codes_enabled,
        "wechat_login": settings.wechat_login_enabled,
    }


@router.post("/send-code")
async def send_reset_code(payload: EmailInput, request: Request, db: DbSession) -> dict:
    email = payload.email.casefold()
    exists = await db.scalar(select(Account.id).where(Account.email == email)) is not None
    await issue_code(db, request.app.state.settings, email, "reset_password", exists)
    return {"cooldown": COOLDOWN, "expires_in": 300}


@router.post("/email/code")
async def send_bind_code(
    payload: EmailInput, request: Request, db: DbSession, member: Member
) -> dict:
    require_unbound_email(member)
    email = payload.email.casefold()
    exists = await db.scalar(select(Account.id).where(Account.email == email)) is not None
    if exists:
        raise ApiError(409, "email_in_use", "此邮箱已绑定其他账号。")
    await issue_code(db, request.app.state.settings, email, "bind_email", True, owner=member.id)
    return {"cooldown": COOLDOWN, "expires_in": 300}


@router.post("/guest", status_code=201)
async def guest(
    payload: GuestInput, request: Request, response: Response, db: DbSession
) -> SessionOut:
    account = Account()
    db.add(account)
    await db.flush()
    return await issue_session(db, request, response, account, payload.transport)


def normalize_new_username(value: str) -> str:
    username = value.lower()
    if username == DEVELOPMENT_ADMIN_USERNAME:
        raise ApiError(409, "username_in_use", "该用户名已被使用，请换一个。")
    return username


@router.post("/register", status_code=201)
async def register(
    payload: RegisterInput,
    request: Request,
    response: Response,
    db: DbSession,
    current: OptionalIdentity,
) -> SessionOut:
    username = normalize_new_username(payload.username)
    hashed = await password_hash(payload.password)
    if current is None:
        account = Account()
        db.add(account)
    else:
        _, existing = current
        account = await db.get(Account, existing.id, with_for_update=True, populate_existing=True)
        if account is None or not account.is_guest:
            raise ApiError(409, "account_already_registered", "当前已登录，请先退出再注册新账号。")
        await db.execute(delete(LoginSession).where(LoginSession.account_id == account.id))
    account.username = username
    account.display_name = payload.display_name or payload.username
    account.password_hash = hashed
    try:
        await db.flush()
        return await issue_session(db, request, response, account, payload.transport)
    except IntegrityError as error:
        await db.rollback()
        raise ApiError(409, "username_in_use", "该用户名已被使用，请换一个。") from error


def throttle_key(account: Account | None, identifier: str = "") -> str:
    if account is not None:
        return f"account:{account.id}"
    return "unknown:" + sha256(identifier.encode()).hexdigest()


async def verify_account_password(
    db: DbSession, account: Account | None, password: str, *, identifier: str = ""
):
    window = await password_window(db, throttle_key(account, identifier))
    if not await password_matches(account.password_hash if account else None, password):
        window.attempts += 1
        await db.commit()
        raise ApiError(401, "invalid_credentials", "用户名、邮箱或密码不正确。")
    await db.delete(window)


@router.post("/login")
async def login(
    payload: LoginInput, request: Request, response: Response, db: DbSession
) -> SessionOut:
    identifier = payload.identifier.casefold()
    field = Account.email if "@" in identifier else Account.username
    account = await db.scalar(select(Account).where(field == identifier).with_for_update())
    await verify_account_password(db, account, payload.password, identifier=identifier)
    assert account is not None
    return await finish_login(
        db, request, response, account, payload.transport, payload.carry_reading_id
    )


@router.put("/credentials")
async def update_credentials(
    payload: CredentialsInput,
    request: Request,
    response: Response,
    db: DbSession,
    current: Identity,
) -> SessionOut:
    session, member = current
    if member.is_guest:
        raise ApiError(403, "account_required", "请先登录账号。")
    settings = request.app.state.settings
    open_id = None
    if payload.wechat_code is not None:
        if session.transport != "bearer" or not member.wechat_open_id:
            raise ApiError(403, "wechat_required", "请在小程序使用已绑定的微信验证。")
        open_id = await wechat.exchange_code(settings, payload.wechat_code)

    account = await db.get(Account, member.id, with_for_update=True, populate_existing=True)
    if account is None:
        raise ApiError(401, "session_expired", "当前会话已失效，请重新登录。")
    if open_id is not None:
        if account.wechat_app_id != settings.wechat_app_id or account.wechat_open_id != open_id:
            raise ApiError(403, "wechat_identity_mismatch", "请使用与当前账号绑定的微信授权。")
        await db.execute(
            delete(PasswordAttempt).where(PasswordAttempt.identifier == throttle_key(account))
        )
    else:
        assert payload.current_password is not None
        await verify_account_password(db, account, payload.current_password)
    if account.username is None:
        if payload.username is None:
            raise ApiError(422, "username_required", "请先设置跨端登录用户名。")
        account.username = normalize_new_username(payload.username)
    elif payload.username is not None and account.username != payload.username.lower():
        raise ApiError(409, "username_already_set", "当前账号已设置用户名。")
    if payload.password is not None:
        account.password_hash = await password_hash(payload.password)
    if account.password_hash is None:
        raise ApiError(422, "password_required", "请设置跨端登录密码。")
    try:
        await db.flush()
        await db.execute(delete(LoginSession).where(LoginSession.account_id == account.id))
        return await issue_session(db, request, response, account, session.transport)
    except IntegrityError as error:
        await db.rollback()
        raise ApiError(409, "username_in_use", "该用户名已被使用，请换一个。") from error


def require_unbound_email(account: Account):
    if account.email is not None:
        raise ApiError(409, "email_already_bound", "当前账号已绑定邮箱。")
    if account.password_hash is None:
        raise ApiError(409, "password_required", "请先设置登录密码。")


@router.post("/email/bind")
async def bind_email(
    payload: BindEmailInput, request: Request, db: DbSession, member: Member
) -> AccountOut:
    account = await db.get(Account, member.id, with_for_update=True, populate_existing=True)
    if account is None:
        raise ApiError(401, "session_expired", "当前会话已失效，请重新登录。")
    require_unbound_email(account)
    await verify_account_password(db, account, payload.current_password)
    email = payload.email.casefold()
    await consume_code(
        db, request.app.state.settings, email, "bind_email", payload.code, owner=account.id
    )
    account.email = email
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise ApiError(409, "email_in_use", "此邮箱已绑定其他账号。") from error
    return account_out(account)


@router.post("/reset-password", status_code=204)
async def reset_password(payload: ResetInput, request: Request, response: Response, db: DbSession):
    email = payload.email.casefold()
    await consume_code(db, request.app.state.settings, email, "reset_password", payload.code)
    account = await db.scalar(select(Account).where(Account.email == email).with_for_update())
    if account is None:
        raise ApiError(401, "code_expired", "验证码无效或已过期，请重新获取。")
    account.password_hash = await password_hash(payload.password)
    await db.execute(delete(LoginSession).where(LoginSession.account_id == account.id))
    await db.execute(
        delete(PasswordAttempt).where(PasswordAttempt.identifier == throttle_key(account))
    )
    await db.commit()
    response.delete_cookie(
        COOKIE_NAME, path="/api", secure=request.app.state.settings.cookie_secure
    )


@router.post("/wechat")
async def wechat_login(
    payload: WeChatInput, request: Request, response: Response, db: DbSession
) -> SessionOut:
    settings = request.app.state.settings
    open_id = await wechat.exchange_code(settings, payload.code)
    account = await wechat.linked_account(db, settings.wechat_app_id, open_id)
    if account is not None:
        return await finish_login(
            db, request, response, account, "bearer", payload.carry_reading_id
        )

    visitor = await current_visitor(request, db)
    account = (
        await db.get(Account, visitor.id, with_for_update=True, populate_existing=True)
        if visitor
        else None
    )
    if account is not None and not account.is_guest:
        raise ApiError(409, "wechat_link_required", "当前访客已完成账号绑定，请重新登录。")
    if account is None:
        account = Account()
        db.add(account)
    account.display_name = "微信用户"
    account.wechat_app_id = settings.wechat_app_id
    account.wechat_open_id = open_id
    try:
        # Rotate guest credentials before this account gains member privileges.
        await db.flush()
        await db.execute(delete(LoginSession).where(LoginSession.account_id == account.id))
        return await issue_session(db, request, response, account, "bearer")
    except IntegrityError as error:
        await db.rollback()
        raise ApiError(409, "wechat_retry", "微信账号绑定状态已变更，请重新发起登录。") from error


@router.post("/wechat/bind")
async def bind_wechat(
    payload: WeChatInput, request: Request, db: DbSession, member: Member
) -> AccountOut:
    settings = request.app.state.settings
    open_id = await wechat.exchange_code(settings, payload.code)
    account = await db.get(Account, member.id, with_for_update=True, populate_existing=True)
    if account is None:
        raise ApiError(401, "session_expired", "当前会话已失效，请重新登录。")
    if account.wechat_open_id is not None and (
        account.wechat_app_id != settings.wechat_app_id or account.wechat_open_id != open_id
    ):
        raise ApiError(409, "wechat_already_linked", "此账号已经绑定另一个微信。")
    account.wechat_app_id = settings.wechat_app_id
    account.wechat_open_id = open_id
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise ApiError(409, "wechat_already_linked", "微信已绑定其他账号。") from error
    return account_out(account)


async def finish_login(
    db: DbSession,
    request: Request,
    response: Response,
    account: Account,
    transport: Transport,
    carry_reading_id: UUID | None,
) -> SessionOut:
    carried = None
    if carry_reading_id is not None:
        visitor = await current_visitor(request, db)
        if visitor is not None:
            carried = await carry_reading(db, visitor, account, carry_reading_id)
    result = await issue_session(db, request, response, account, transport)
    return result.model_copy(update={"handoff_reading_id": str(carried) if carried else None})


async def carry_reading(db: DbSession, visitor: Account, account: Account, reading_id: UUID):
    item = await db.scalar(
        select(Reading)
        .where(Reading.account_id == visitor.id, Reading.id == reading_id)
        .with_for_update()
    )
    if item is None:
        return None
    if item.kind != "daily":
        item.account_id = account.id
        item.idempotency_key = "import-" + item.id.hex
        return item.id

    copied = await db.scalar(
        insert(Reading)
        .values(
            account_id=account.id,
            kind=item.kind,
            idempotency_key=item.idempotency_key,
            request_data=item.request_data,
            result=item.result,
            rules_version=item.rules_version,
            created_at=item.created_at,
        )
        .on_conflict_do_nothing(constraint="uq_reading_request")
        .returning(Reading.id)
    )
    if copied is not None:
        return copied
    return await db.scalar(
        select(Reading.id).where(
            Reading.account_id == account.id,
            Reading.kind == "daily",
            Reading.idempotency_key == item.idempotency_key,
        )
    )


@router.get("/session")
async def session(current: Identity) -> AccountOut:
    return account_out(current[1])


@router.delete("/session", status_code=204)
async def logout(request: Request, response: Response, db: DbSession, current: Identity):
    await db.delete(current[0])
    await db.commit()
    response.delete_cookie(
        COOKIE_NAME, path="/api", secure=request.app.state.settings.cookie_secure
    )


class ProfileDetails(BaseModel):
    relation: ShortText = "本人"
    gender: ShortText = "暂不填写"
    city: ShortText = ""
    current_city: ShortText = ""


class ProfileInput(BaseModel):
    name: Name
    birth: BirthInput
    details: ProfileDetails = ProfileDetails()


class ProfileOut(ProfileInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


async def owned_profile(db: DbSession, account: Account, profile_id: UUID) -> BirthProfile:
    profile = await db.scalar(
        select(BirthProfile).where(
            BirthProfile.id == profile_id, BirthProfile.account_id == account.id
        )
    )
    if profile is None:
        raise ApiError(404, "profile_not_found", "出生档案不存在。")
    return profile


@private.get("/profiles")
async def list_profiles(
    db: DbSession, account: Member, limit: Annotated[int, Query(ge=1, le=100)] = 30
) -> list[ProfileOut]:
    records = await db.scalars(
        select(BirthProfile)
        .where(BirthProfile.account_id == account.id)
        .order_by(BirthProfile.created_at.desc(), BirthProfile.id.desc())
        .limit(limit)
    )
    return [ProfileOut.model_validate(record) for record in records]


@private.post("/profiles", status_code=201)
async def create_profile(payload: ProfileInput, db: DbSession, account: Member) -> ProfileOut:
    profile = BirthProfile(
        account_id=account.id,
        name=payload.name,
        birth=payload.birth.model_dump(mode="json"),
        details=payload.details.model_dump(),
    )
    db.add(profile)
    await db.commit()
    return ProfileOut.model_validate(profile)


@private.get("/profiles/{profile_id}")
async def read_profile(profile_id: UUID, db: DbSession, account: Member) -> ProfileOut:
    return ProfileOut.model_validate(await owned_profile(db, account, profile_id))


@private.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: UUID, payload: ProfileInput, db: DbSession, account: Member
) -> ProfileOut:
    profile = await owned_profile(db, account, profile_id)
    profile.name = payload.name
    profile.birth = payload.birth.model_dump(mode="json")
    profile.details = payload.details.model_dump()
    await db.commit()
    return ProfileOut.model_validate(profile)


@private.delete("/profiles/{profile_id}", status_code=204)
async def delete_profile(profile_id: UUID, db: DbSession, account: Member):
    await db.delete(await owned_profile(db, account, profile_id))
    await db.commit()


class AccountDetails(BaseModel):
    bio: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] = ""
    birth: date | None = None
    mbti: ShortText = ""
    theme: ShortText = "紫宸夜"
    public_birthday: bool = False
    public_sign: bool = False
    public_mbti: bool = False


class AccountUpdate(BaseModel):
    display_name: Name
    details: AccountDetails


@private.put("")
async def update_account(payload: AccountUpdate, db: DbSession, account: Member) -> AccountOut:
    account.display_name = payload.display_name
    account.details = payload.details.model_dump(mode="json")
    await db.commit()
    return account_out(account)


class JournalInput(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)]
    reading_id: UUID | None = None


class JournalOut(JournalInput):
    model_config = ConfigDict(from_attributes=True)

    entry_date: date
    updated_at: datetime


@private.get("/journal")
async def list_journal(
    db: DbSession,
    account: Member,
    before: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[JournalOut]:
    query = select(JournalEntry).where(JournalEntry.account_id == account.id)
    if before is not None:
        query = query.where(JournalEntry.entry_date < before)
    entries = await db.scalars(query.order_by(JournalEntry.entry_date.desc()).limit(limit))
    return [JournalOut.model_validate(entry) for entry in entries]


@private.put("/journal/{entry_date}")
async def put_journal(
    entry_date: date, payload: JournalInput, db: DbSession, account: Member
) -> JournalOut:
    if payload.reading_id is not None and not await db.scalar(
        select(Reading.id).where(Reading.id == payload.reading_id, Reading.account_id == account.id)
    ):
        raise ApiError(404, "reading_not_found", "体验记录不存在。")
    values = {**payload.model_dump(), "updated_at": utc_now()}
    entry = await db.scalar(
        insert(JournalEntry)
        .values(account_id=account.id, entry_date=entry_date, **values)
        .on_conflict_do_update(constraint="uq_journal_account_date", set_=values)
        .returning(JournalEntry)
    )
    await db.commit()
    return JournalOut.model_validate(entry)


@private.delete("/journal/{entry_date}", status_code=204)
async def delete_journal(entry_date: date, db: DbSession, account: Member):
    entry = await db.scalar(
        select(JournalEntry).where(
            JournalEntry.account_id == account.id, JournalEntry.entry_date == entry_date
        )
    )
    if entry is not None:
        await db.delete(entry)
        await db.commit()
