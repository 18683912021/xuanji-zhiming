from collections.abc import Callable
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.accounts.auth import Actor, Member
from app.accounts.models import Account, BirthProfile
from app.core.db import DbSession, utc_now
from app.core.errors import ApiError
from app.readings import rules
from app.readings.astro import VERSION as ASTRO_VERSION
from app.readings.astro import AstroInput, build_astro, moon_phase
from app.readings.bazi import BAZI_VERSION, BirthInput, build_bazi, validate_zone
from app.readings.models import Reading

router = APIRouter(prefix="/readings", tags=["体验记录"])
catalog_router = APIRouter(tags=["星座与历法"])

type Question = Annotated[str, StringConstraints(strip_whitespace=True, max_length=600)]
type RequestKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=72)]
type Sign = Literal[
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]
type ReadingKind = Literal[
    "bazi", "astro", "tarot", "daily", "oracle", "liuyao", "dice", "book", "dream"
]


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: ReadingKind
    request_data: dict
    result: dict
    rules_version: str
    saved: bool
    note: str
    created_at: datetime


class TarotInput(BaseModel):
    spread_id: Literal["single", "timeline", "relationship", "choices", "review"] = "single"
    question: Question = ""
    positions: Annotated[list[Annotated[int, Field(ge=0, le=5)]], Field(max_length=3)] | None = None

    @model_validator(mode="after")
    def validate_positions(self) -> "TarotInput":
        if self.positions is not None and (
            len(set(self.positions)) != len(rules.spreads[self.spread_id]["positions"])
            or len(self.positions) != len(set(self.positions))
        ):
            raise ValueError("请选择对应数量的不同牌背。")
        return self


class OracleInput(BaseModel):
    question: Question = ""
    topic: Literal["general", "relationship", "work", "study", "life"] = "general"


class QuestionInput(BaseModel):
    question: Question = ""


class BookInput(QuestionInput):
    previous_answer: Annotated[str, StringConstraints(max_length=128)] | None = None


class DreamInput(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    mood: Literal["平静", "好奇", "紧张", "欣喜", "困惑"]


class LiuyaoInput(BaseModel):
    question: Question = ""
    lines: Annotated[list[Literal[6, 7, 8, 9]], Field(min_length=6, max_length=6)] | None = None


class BaziInput(BaseModel):
    birth: BirthInput | None = None
    profile_id: UUID | None = None
    late_zi: bool = False

    @model_validator(mode="after")
    def exact_source(self) -> "BaziInput":
        if (self.birth is None) == (self.profile_id is None):
            raise ValueError("请选择出生档案或直接录入一份生辰。")
        return self


class SaveInput(BaseModel):
    saved: bool | None = None
    note: Annotated[str, StringConstraints(max_length=4000)] | None = None


def local_date(timezone: str) -> date:
    try:
        return utc_now().astimezone(validate_zone(timezone)).date()
    except ValueError as error:
        raise ApiError(422, "invalid_timezone", "请输入有效的 IANA 时区。") from error


async def owned_reading(db: DbSession, account: Account, reading_id: UUID) -> Reading:
    item = await db.scalar(
        select(Reading).where(Reading.id == reading_id, Reading.account_id == account.id)
    )
    if item is None:
        raise ApiError(404, "reading_not_found", "体验记录不存在。")
    return item


def check_replay(item: Reading, request_data: dict) -> ReadingOut:
    if item.request_data != request_data:
        raise ApiError(409, "idempotency_conflict", "该请求编号已用于不同的输入。")
    return ReadingOut.model_validate(item)


async def save_reading(
    db: DbSession,
    account: Account,
    kind: ReadingKind,
    key: str,
    request_data: dict,
    version: str,
    calculate: Callable[[], dict],
) -> ReadingOut:
    query = select(Reading).where(
        Reading.account_id == account.id, Reading.kind == kind, Reading.idempotency_key == key
    )
    existing = await db.scalar(query)
    if existing is not None:
        return check_replay(existing, request_data)

    inserted = await db.scalar(
        insert(Reading)
        .values(
            account_id=account.id,
            kind=kind,
            idempotency_key=key,
            request_data=request_data,
            result=calculate(),
            rules_version=version,
        )
        .on_conflict_do_nothing(constraint="uq_reading_request")
        .returning(Reading)
    )
    if inserted is not None:
        await db.commit()
        return ReadingOut.model_validate(inserted)
    return check_replay((await db.scalars(query)).one(), request_data)


@catalog_router.get("/zodiac")
async def signs() -> list[dict]:
    return list(rules.signs.values())


@catalog_router.get("/zodiac/{sign}")
async def sign_detail(sign: Sign) -> dict:
    return rules.zodiac(sign)


@catalog_router.get("/fortune/{sign}")
async def fortune(
    sign: Sign,
    day: date | None = None,
    timezone: Annotated[str, Query(max_length=64)] = "Asia/Shanghai",
) -> dict:
    local_day = local_date(timezone)
    info = rules.zodiac(sign)
    return {
        "date": (day or local_day).isoformat(),
        "sign": sign,
        "summary": info["prompt"],
        "relationship": info["relationship"],
        "content_kind": "base_editorial",
        "content_version": rules.CATALOG_VERSION,
    }


@catalog_router.get("/calendar/day")
async def calendar(
    day: date | None = None,
    timezone: Annotated[str, Query(max_length=64)] = "Asia/Shanghai",
) -> dict:
    local_day = local_date(timezone)
    target = day or local_day
    if not 1901 <= target.year <= 2099:
        raise ApiError(422, "unsupported_date", "历法查询范围为 1901 至 2099 年。")
    return {**rules.calendar_day(target), "moon_phase": moon_phase(target, timezone)}


@catalog_router.get("/tarot/spreads")
async def tarot_spreads() -> list[dict]:
    return list(rules.spreads.values())


@catalog_router.get("/tarot/cards")
async def tarot_cards() -> list[dict]:
    return [
        {"index": index, "name": name, "upright": upright, "reversed": reversed_}
        for index, (name, upright, reversed_) in enumerate(rules.cards)
    ]


@router.post("/tarot")
async def tarot(payload: TarotInput, key: RequestKey, db: DbSession, account: Actor) -> ReadingOut:
    return await save_reading(
        db,
        account,
        "tarot",
        key,
        payload.model_dump(exclude_none=True),
        rules.CATALOG_VERSION,
        lambda: rules.draw_tarot(payload.spread_id, payload.positions),
    )


@router.post("/daily-tarot")
async def daily_tarot(
    db: DbSession, account: Actor, timezone: Annotated[str, Query(max_length=64)] = "Asia/Shanghai"
) -> ReadingOut:
    day = local_date(timezone).isoformat()
    return await save_reading(
        db,
        account,
        "daily",
        day,
        {"date": day},
        rules.CATALOG_VERSION,
        lambda: rules.draw_tarot("single"),
    )


@router.post("/oracle")
async def oracle(
    payload: OracleInput, key: RequestKey, db: DbSession, account: Actor
) -> ReadingOut:
    return await save_reading(
        db, account, "oracle", key, payload.model_dump(), rules.CATALOG_VERSION, rules.draw_oracle
    )


@router.post("/liuyao")
async def liuyao(
    payload: LiuyaoInput, key: RequestKey, db: DbSession, account: Actor
) -> ReadingOut:
    return await save_reading(
        db,
        account,
        "liuyao",
        key,
        payload.model_dump(),
        "liuyao-1",
        lambda: rules.cast_liuyao(payload.lines),
    )


@router.post("/bazi")
async def bazi(payload: BaziInput, key: RequestKey, db: DbSession, account: Actor) -> ReadingOut:
    source = payload.model_dump(mode="json")
    if not payload.late_zi:
        source.pop("late_zi")
    if payload.profile_id is not None:
        query = select(Reading).where(
            Reading.account_id == account.id, Reading.kind == "bazi", Reading.idempotency_key == key
        )
        previous = await db.scalar(query)
        if previous is not None:
            return check_replay(previous, source)

        profile = await db.scalar(
            select(BirthProfile).where(
                BirthProfile.id == payload.profile_id, BirthProfile.account_id == account.id
            )
        )
        if profile is None:
            raise ApiError(404, "profile_not_found", "出生档案不存在。")
        birth = BirthInput.model_validate(profile.birth)
    else:
        assert payload.birth is not None
        birth = payload.birth

    return await save_reading(
        db,
        account,
        "bazi",
        key,
        source,
        BAZI_VERSION,
        lambda: {
            **build_bazi(birth, late_zi=payload.late_zi),
            "birth_snapshot": birth.model_dump(mode="json"),
        },
    )


@router.post("/astro")
async def astro(payload: AstroInput, key: RequestKey, db: DbSession, account: Actor) -> ReadingOut:
    return await save_reading(
        db,
        account,
        "astro",
        key,
        payload.model_dump(mode="json"),
        ASTRO_VERSION,
        lambda: build_astro(payload),
    )


@router.post("/dice")
async def dice(
    payload: QuestionInput, key: RequestKey, db: DbSession, account: Actor
) -> ReadingOut:
    return await save_reading(
        db, account, "dice", key, payload.model_dump(), "dice-1", rules.roll_dice
    )


@router.post("/book")
async def book(payload: BookInput, key: RequestKey, db: DbSession, account: Actor) -> ReadingOut:
    return await save_reading(
        db,
        account,
        "book",
        key,
        payload.model_dump(exclude_none=True),
        "book-2",
        lambda: rules.open_book(payload.previous_answer),
    )


@router.post("/dream")
async def dream(payload: DreamInput, key: RequestKey, db: DbSession, account: Actor) -> ReadingOut:
    return await save_reading(
        db, account, "dream", key, payload.model_dump(), "dream-1", lambda: {"mood": payload.mood}
    )


@router.get("")
async def readings(
    db: DbSession,
    account: Actor,
    kind: ReadingKind | None = None,
    saved: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[ReadingOut]:
    query = select(Reading).where(Reading.account_id == account.id)
    if kind is not None:
        query = query.where(Reading.kind == kind)
    if saved is not None:
        query = query.where(Reading.saved == saved)
    items = await db.scalars(
        query.order_by(Reading.created_at.desc(), Reading.id.desc()).limit(limit).offset(offset)
    )
    return [ReadingOut.model_validate(item) for item in items]


@router.get("/{reading_id}")
async def get_reading(reading_id: UUID, db: DbSession, account: Actor) -> ReadingOut:
    return ReadingOut.model_validate(await owned_reading(db, account, reading_id))


@router.patch("/{reading_id}", include_in_schema=False)
@router.put("/{reading_id}")
async def mark_saved(
    reading_id: UUID, payload: SaveInput, db: DbSession, account: Member
) -> ReadingOut:
    item = await owned_reading(db, account, reading_id)
    if payload.saved is not None:
        item.saved = payload.saved
    if payload.note is not None:
        item.note = payload.note
    await db.commit()
    return ReadingOut.model_validate(item)


@router.delete("/{reading_id}", status_code=204)
async def delete_reading(reading_id: UUID, db: DbSession, account: Actor):
    await db.delete(await owned_reading(db, account, reading_id))
    await db.commit()
