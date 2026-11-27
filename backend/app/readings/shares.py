from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select

from app.accounts.auth import Member
from app.core.db import DbSession, utc_now
from app.core.errors import ApiError
from app.readings.models import Reading, ReadingShare
from app.readings.router import owned_reading

router = APIRouter(prefix="/shares", tags=["分享"])
TITLES = {
    "tarot": "塔罗占卜",
    "daily": "今日塔罗",
    "oracle": "占卜问签",
    "liuyao": "六爻问事",
    "bazi": "八字命盘",
    "astro": "西洋本命盘",
    "dice": "星座骰子",
    "book": "答案之书",
    "dream": "梦境记录",
}


class ShareInput(BaseModel):
    reading_id: UUID


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str
    created_at: datetime
    expires_at: datetime


def summary(reading: Reading) -> str:
    # A public share is built from an allowlist, not the private request/result snapshot.
    if reading.kind in ("tarot", "daily"):
        return "、".join(card["name"] for card in reading.result["cards"])
    if reading.kind == "oracle":
        return reading.result["verse"]
    if reading.kind == "liuyao":
        result = reading.result
        return result["hexagram"] + (
            " → " + result["changed_hexagram"] if result["changed_hexagram"] else " · 静卦"
        )
    return "本次完成了" + TITLES[reading.kind] + "体验。"


@router.post("", status_code=201)
async def publish(payload: ShareInput, db: DbSession, account: Member) -> ShareOut:
    reading = await owned_reading(db, account, payload.reading_id)
    entry = ReadingShare(
        reading_id=reading.id,
        account_id=account.id,
        title=TITLES[reading.kind],
        summary=summary(reading),
        expires_at=utc_now() + timedelta(days=7),
    )
    db.add(entry)
    await db.commit()
    return ShareOut.model_validate(entry)


@router.get("/{share_id}")
async def inspect_share(share_id: UUID, db: DbSession) -> ShareOut:
    entry = await db.scalar(
        select(ReadingShare).where(ReadingShare.id == share_id, ReadingShare.expires_at > utc_now())
    )
    if entry is None:
        raise ApiError(404, "share_not_found", "分享已过期或已撤回。")
    return ShareOut.model_validate(entry)


@router.delete("/{share_id}", status_code=204)
async def revoke(share_id: UUID, db: DbSession, account: Member):
    await db.execute(
        delete(ReadingShare).where(
            ReadingShare.id == share_id, ReadingShare.account_id == account.id
        )
    )
    await db.commit()
