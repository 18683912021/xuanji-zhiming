import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated
from uuid import UUID, uuid4

from anyio import CancelScope
from fastapi import APIRouter, Depends, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy import select, update

from app.accounts.auth import Member
from app.agent.models import Conversation, Turn
from app.agent.prompts import PROMPT_VERSION, ROLES
from app.agent.schemas import (
    ConversationInput,
    ConversationOut,
    ConversationUpdate,
    Reply,
    TurnInput,
    TurnOut,
)
from app.agent.workflow import TurnContext, ask_for_input, run_model
from app.core.db import DbSession, utc_now
from app.core.errors import ApiError
from app.readings.models import Reading
from app.readings.router import owned_reading

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI 对话"])


async def owned_conversation(db: DbSession, account: Member, conversation_id: UUID, *, lock=False):
    query = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.account_id == account.id
    )
    if lock:
        query = query.with_for_update()
    conversation = await db.scalar(query)
    if conversation is None:
        raise ApiError(404, "conversation_not_found", "对话不存在。")
    return conversation


@router.get("/roles")
async def roles(request: Request) -> list[dict]:
    ready = request.app.state.agent is not None
    return [
        {
            "id": role,
            "name": spec["name"],
            "scope": spec["scope"],
            "reading_kinds": spec["reading_kinds"],
            "model_available": ready,
        }
        for role, spec in ROLES.items()
    ]


@router.post("/conversations", status_code=201)
async def create_conversation(
    payload: ConversationInput, db: DbSession, account: Member
) -> ConversationOut:
    role = ROLES[payload.role]
    if payload.reading_id is not None:
        reading = await owned_reading(db, account, payload.reading_id)
        if reading.kind not in role["reading_kinds"]:
            raise ApiError(422, "unsupported_reading", "此角色无法解读该类体验。")
    conversation = Conversation(
        account_id=account.id,
        role=payload.role,
        title=payload.title or role["name"],
        reading_id=payload.reading_id,
    )
    db.add(conversation)
    await db.commit()
    return ConversationOut.model_validate(conversation)


@router.get("/conversations")
async def list_conversations(
    db: DbSession,
    account: Member,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[ConversationOut]:
    rows = await db.scalars(
        select(Conversation)
        .where(Conversation.account_id == account.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [ConversationOut.model_validate(row) for row in rows]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID, db: DbSession, account: Member):
    conversation = await owned_conversation(db, account, conversation_id, lock=True)
    if await db.scalar(
        select(Turn.id).where(
            Turn.conversation_id == conversation.id,
            Turn.status == "running",
            Turn.lease_until > utc_now(),
        )
    ):
        raise ApiError(409, "turn_running", "请先停止正在生成的消息。")
    await db.delete(conversation)
    await db.commit()


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID, db: DbSession, account: Member
) -> ConversationOut:
    return ConversationOut.model_validate(await owned_conversation(db, account, conversation_id))


@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: UUID, payload: ConversationUpdate, db: DbSession, account: Member
) -> ConversationOut:
    item = await owned_conversation(db, account, conversation_id, lock=True)
    if payload.title is not None:
        item.title = payload.title
    if "reading_id" in payload.model_fields_set:
        if payload.reading_id is not None:
            reading = await owned_reading(db, account, payload.reading_id)
            if reading.kind not in ROLES[item.role]["reading_kinds"]:
                raise ApiError(422, "unsupported_reading", "此角色无法解读该类体验。")
        item.reading_id = payload.reading_id
    item.updated_at = utc_now()
    await db.commit()
    return ConversationOut.model_validate(item)


def turn_out(turn: Turn) -> TurnOut:
    result = TurnOut.model_validate(turn)
    if turn.status == "running" and turn.lease_until <= utc_now():
        return result.model_copy(update={"status": "stopped", "error_code": "interrupted"})
    return result


@router.get("/conversations/{conversation_id}/turns")
async def list_turns(
    conversation_id: UUID,
    db: DbSession,
    account: Member,
    before: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[TurnOut]:
    await owned_conversation(db, account, conversation_id)
    query = select(Turn).where(Turn.conversation_id == conversation_id)
    if before is not None:
        anchor = await db.scalar(query.where(Turn.id == before))
        if anchor is None:
            raise ApiError(404, "turn_not_found", "消息不存在。")
        query = query.where(
            (Turn.created_at < anchor.created_at)
            | ((Turn.created_at == anchor.created_at) & (Turn.id < anchor.id))
        )
    rows = await db.scalars(query.order_by(Turn.created_at.desc(), Turn.id.desc()).limit(limit))
    return [turn_out(row) for row in reversed(rows.all())]


@dataclass
class PreparedTurn:
    output: TurnOut
    attempt_id: UUID
    context: TurnContext | None = None


async def prepare_turn(
    conversation_id: UUID, payload: TurnInput, request: Request, db: DbSession, account: Member
) -> PreparedTurn:
    conversation = await owned_conversation(db, account, conversation_id, lock=True)
    now = utc_now()
    prior = await db.scalar(
        select(Turn).where(
            Turn.conversation_id == conversation.id,
            Turn.client_message_id == payload.client_message_id,
        )
    )
    if prior is not None:
        if prior.question != payload.text or prior.task != payload.task:
            raise ApiError(409, "idempotency_conflict", "该消息编号已用于其他内容。")
        prior_state = turn_out(prior)
        if prior_state.status == "running":
            raise ApiError(409, "turn_running", "此消息正在生成。")
        if prior_state.status == "complete" or not payload.retry:
            return PreparedTurn(prior_state, prior.attempt_id)
    elif payload.retry:
        raise ApiError(404, "turn_not_found", "待重试的消息不存在。")

    active = await db.scalar(
        select(Turn.id).where(
            Turn.conversation_id == conversation.id,
            Turn.status == "running",
            Turn.lease_until > now,
        )
    )
    if active is not None:
        raise ApiError(409, "turn_running", "此对话已有一条消息正在生成。")

    snapshot = None
    if payload.task == "reading" and conversation.reading_id is not None:
        reading = await db.scalar(
            select(Reading).where(
                Reading.id == conversation.reading_id, Reading.account_id == account.id
            )
        )
        if reading is not None and reading.kind in ROLES[conversation.role]["reading_kinds"]:
            snapshot = {
                "kind": reading.kind,
                "result": {
                    key: value
                    for key, value in reading.result.items()
                    if key not in {"utc", "solar_date", "birth_snapshot"}
                },
                "rules_version": reading.rules_version,
            }
            if reading.kind == "dream":
                snapshot["result"]["text"] = reading.request_data["text"]

    history_query = select(Turn).where(
        Turn.conversation_id == conversation.id, Turn.status == "complete"
    )
    if prior is not None:
        history_query = history_query.where(Turn.created_at < prior.created_at)
    recent = await db.scalars(
        history_query.order_by(Turn.created_at.desc(), Turn.id.desc()).limit(6)
    )
    context = TurnContext(
        role=conversation.role,
        task=payload.task,
        question=payload.text,
        history=[
            {"question": row.question[:450], "answer": (row.reply or {}).get("text", "")[:750]}
            for row in reversed(recent.all())
        ],
        reference_id=conversation.reading_id,
        snapshot=snapshot,
    )
    clarification = ask_for_input(context)
    state = request.app.state
    if clarification is None and state.agent is None:
        raise ApiError(503, "model_not_configured", "模型服务尚未配置。")

    if prior is None:
        turn = Turn(
            conversation_id=conversation.id,
            client_message_id=payload.client_message_id,
            question=payload.text,
            task=payload.task,
        )
        db.add(turn)
    else:
        turn = prior
    turn.attempt_id = uuid4()
    turn.status = "complete" if clarification else "running"
    turn.reply = clarification.model_dump(mode="json") if clarification else None
    turn.model = None if clarification else state.settings.ai_model
    turn.prompt_version = PROMPT_VERSION
    turn.error_code = None
    turn.updated_at = conversation.updated_at = now
    turn.lease_until = now + timedelta(seconds=state.settings.ai_timeout_seconds + 15)
    await db.commit()
    return PreparedTurn(turn_out(turn), turn.attempt_id, None if clarification else context)


async def finish_turn(
    request: Request,
    prepared: PreparedTurn,
    status: str,
    *,
    reply: Reply | None = None,
    error_code: str | None = None,
    usage: dict | None = None,
) -> TurnOut:
    now = utc_now()
    async with request.app.state.sessions() as db:
        row = await db.scalar(
            update(Turn)
            .where(
                Turn.id == prepared.output.id,
                Turn.attempt_id == prepared.attempt_id,
                Turn.status == "running",
            )
            .values(
                status=status,
                updated_at=now,
                usage=usage,
                error_code=error_code,
                reply=reply.model_dump(mode="json") if reply else None,
            )
            .returning(Turn)
        )
        await db.commit()
    return turn_out(row) if row is not None else prepared.output


@router.post("/conversations/{conversation_id}/turns", response_class=EventSourceResponse)
async def send(
    request: Request, prepared: Annotated[PreparedTurn, Depends(prepare_turn, scope="function")]
) -> AsyncIterator[ServerSentEvent]:
    if prepared.context is None:
        yield ServerSentEvent(event="result", data=prepared.output)
        return

    finished = False
    try:
        yield ServerSentEvent(event="status", data=prepared.output)
        state = request.app.state
        try:
            async with asyncio.timeout(state.settings.ai_timeout_seconds):
                async with state.ai_slots:
                    reply, usage = await run_model(state, prepared.context)
        except TimeoutError:
            output = await finish_turn(request, prepared, "failed", error_code="model_timeout")
        except Exception as error:
            logger.warning("Agent turn %s failed (%s)", prepared.output.id, type(error).__name__)
            output = await finish_turn(request, prepared, "failed", error_code="model_failed")
        else:
            output = await finish_turn(request, prepared, "complete", reply=reply, usage=usage)
        finished = True
        yield ServerSentEvent(event="result", data=output)
    finally:
        if not finished:
            with CancelScope(shield=True):
                await finish_turn(request, prepared, "stopped", error_code="interrupted")
