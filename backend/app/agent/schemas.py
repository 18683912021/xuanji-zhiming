from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

type Role = Literal["astrologer", "tarot", "diviner", "dream", "report"]
type Task = Literal["general", "reading"]


class ConversationInput(BaseModel):
    role: Role
    title: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=96)] | None
    ) = None
    reading_id: UUID | None = None


class ConversationOut(ConversationInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    title: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=96)] | None
    ) = None
    reading_id: UUID | None = None


class TurnInput(BaseModel):
    client_message_id: UUID
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1500)]
    task: Task = "general"
    retry: bool = False


class Citation(BaseModel):
    id: str
    title: str
    source: str
    version: str


class Answer(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]
    source_ids: list[str] = Field(max_length=6)
    follow_up: Annotated[str, StringConstraints(strip_whitespace=True, max_length=240)] | None = (
        None
    )


class Reply(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    follow_up: str | None = None
    needs_input: bool = False


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_message_id: UUID
    question: str
    task: Task
    status: Literal["running", "complete", "failed", "stopped"]
    reply: Reply | None
    error_code: str | None
    created_at: datetime
    updated_at: datetime
