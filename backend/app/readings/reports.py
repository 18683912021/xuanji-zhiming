from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.accounts.auth import Member
from app.core.db import DbSession
from app.core.errors import ApiError
from app.readings.models import Reading, ReadingReport
from app.readings.router import RequestKey, owned_reading
from app.readings.shares import TITLES, summary

router = APIRouter(prefix="/reports", tags=["基础报告"])
type Template = Literal["bazi", "astro", "review"]
LABELS = {
    "bazi": ("四柱与五行报告", "八字"),
    "astro": ("本命星盘报告", "占星"),
    "review": ("近期自我观察报告", "通用"),
}


class ReportRequest(BaseModel):
    reading_id: UUID
    template: Template


class Section(BaseModel):
    title: str
    content: str


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reading_id: UUID | None
    template: Template
    title: str
    category: str
    source: dict
    sections: list[Section]
    created_at: datetime


def render_report(template: Template, reading: Reading) -> list[dict]:
    data = reading.result
    if template == "bazi":
        parts = [
            ("命盘概览", "日主 " + (data["day_master"] or "待确定") + "，以当次四柱快照为准。"),
            (
                "四柱结构",
                "\n".join(
                    label
                    + "："
                    + (
                        f"{pillar['ganzhi']} · {pillar['elements']}，藏干 {'、'.join(pillar['hidden_stems'])}"
                        if pillar
                        else "资料不足"
                    )
                    for name, label in zip(
                        ("year", "month", "day", "hour"),
                        ("年柱", "月柱", "日柱", "时柱"),
                        strict=True,
                    )
                    for pillar in [data["pillars"][name]]
                ),
            ),
            (
                "五行统计",
                "、".join(f"{key} {value}" for key, value in data["elements"].items())
                + "。统计只含可确定的四柱。",
            ),
        ]
    elif template == "astro":
        names = {body["id"]: body["name"] for body in data["planets"]}
        parts = [
            ("盘面概览", f"上升点 {data['ascendant']:.2f}°，天顶 {data['midheaven']:.2f}°。"),
            (
                "行星与宫位",
                "\n".join(
                    f"{body['name']} · {body['longitude']:.2f}° · 第 {body['house']} 宫"
                    for body in data["planets"]
                ),
            ),
            (
                "相位",
                "\n".join(
                    f"{names[aspect['first']]} {aspect['name']} {names[aspect['second']]} · 偏差 {aspect['orb']:.2f}°"
                    for aspect in data["aspects"]
                )
                or "所设容许度内无主要相位。",
            ),
        ]
    else:
        parts = [
            ("原始体验", TITLES[reading.kind] + " · " + summary(reading)),
            ("回顾要点", reading.note or "回看当时的问题与原始依据，记下目前已经可以核实的信息。"),
            ("下一步", "选一个自己可以观察或记录的变化，给它一个明确的回看时间。"),
        ]
    return [{"title": title, "content": content} for title, content in parts]


@router.post("")
async def generate(
    payload: ReportRequest, key: RequestKey, db: DbSession, account: Member
) -> ReportOut:
    reading = await owned_reading(db, account, payload.reading_id)
    if payload.template != "review" and payload.template != reading.kind:
        raise ApiError(422, "incompatible_report", "所选资料与报告模板不匹配。")
    title, category = LABELS[payload.template]
    statement = (
        insert(ReadingReport)
        .values(
            account_id=account.id,
            reading_id=reading.id,
            request_key=key,
            template=payload.template,
            title=title,
            category=category,
            sections=render_report(payload.template, reading),
            source={
                "kind": reading.kind,
                "title": TITLES[reading.kind],
                "summary": summary(reading),
                "version": reading.rules_version,
            },
        )
        .on_conflict_do_nothing(constraint="uq_report_request")
        .returning(ReadingReport)
    )
    item = await db.scalar(statement)
    if item is not None:
        await db.commit()
        return ReportOut.model_validate(item)
    item = (
        await db.scalars(
            select(ReadingReport).where(
                ReadingReport.account_id == account.id, ReadingReport.request_key == key
            )
        )
    ).one()
    if item.reading_id != reading.id or item.template != payload.template:
        raise ApiError(409, "idempotency_conflict", "该请求编号已用于不同的报告。")
    return ReportOut.model_validate(item)


@router.get("")
async def list_reports(
    db: DbSession, account: Member, limit: Annotated[int, Query(ge=1, le=100)] = 30
) -> list[ReportOut]:
    values = await db.scalars(
        select(ReadingReport)
        .where(ReadingReport.account_id == account.id)
        .order_by(ReadingReport.created_at.desc(), ReadingReport.id.desc())
        .limit(limit)
    )
    return [ReportOut.model_validate(value) for value in values]


async def own_report(report_id: UUID, db: DbSession, account: Member) -> ReadingReport:
    value = await db.scalar(
        select(ReadingReport).where(
            ReadingReport.account_id == account.id, ReadingReport.id == report_id
        )
    )
    if value is None:
        raise ApiError(404, "report_not_found", "报告不存在。")
    return value


@router.get("/{report_id}")
async def get_report(report_id: UUID, db: DbSession, account: Member) -> ReportOut:
    return ReportOut.model_validate(await own_report(report_id, db, account))


@router.delete("/{report_id}", status_code=204)
async def remove_report(report_id: UUID, db: DbSession, account: Member):
    await db.delete(await own_report(report_id, db, account))
    await db.commit()
