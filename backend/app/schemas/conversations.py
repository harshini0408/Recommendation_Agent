from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.products import ProductOut
from app.schemas.requirements import Requirements


class MessageIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=4000)
    client_message_id: UUID


class Recommendation(BaseModel):
    product: ProductOut
    score: float
    score_components: dict[str, float]
    reasons: list[str]
    trade_offs: list[str]
    unknowns: list[str]


class TurnResponse(BaseModel):
    conversation_id: str
    response_type: Literal["clarification", "recommendations", "no_match", "informational"]
    assistant_message: str
    requirements: Requirements
    state_version: int
    recommendations: list[Recommendation]
    evidence: dict
    mode: Literal["live", "demo", "test"]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    content: str
    sequence: int
    created_at: datetime
    response: TurnResponse | None


class ConversationOut(BaseModel):
    id: str
    requirements: Requirements
    state_version: int
    title: str | None = None
    title_status: str = "pending"
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]
    latest_response: TurnResponse | None


class ConversationSummary(BaseModel):
    """Lightweight summary returned by the sidebar listing endpoint."""
    id: str
    title: str | None = None
    title_status: str = "pending"
    created_at: datetime
    updated_at: datetime


class TitleOut(BaseModel):
    id: str
    title: str | None
    title_status: str


class SummaryRequest(BaseModel):
    """Batch lookup of conversation summaries by browser-known IDs."""
    model_config = ConfigDict(extra="forbid")
    ids: list[str] = Field(max_length=100)
