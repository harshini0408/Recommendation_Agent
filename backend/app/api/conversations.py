from uuid import UUID
from fastapi import APIRouter, Request, Query
from sqlalchemy import select, func
from app.models.entities import Conversation, Message
from app.schemas.requirements import Requirements
from app.schemas.conversations import (
    ConversationOut,
    ConversationSummary,
    MessageOut,
    MessageIn,
    TurnResponse,
    TitleOut,
    SummaryRequest,
)
from app.agent.orchestrator import process_turn
from app.agent.title import generate_title, is_meaningful
from app.errors import AppError

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])


def read_conversation(session, cid):
    c = session.get(Conversation, cid)
    if not c:
        raise AppError(404, "not_found", "Conversation not found.")
    msgs = session.scalars(
        select(Message).where(Message.conversation_id == cid).order_by(Message.sequence)
    ).all()
    return ConversationOut(
        id=c.id,
        requirements=Requirements.model_validate(c.requirements),
        state_version=c.state_version,
        title=c.title,
        title_status=c.title_status,
        created_at=c.created_at,
        updated_at=c.updated_at,
        messages=[MessageOut.model_validate(m) for m in msgs],
        latest_response=msgs[-1].response if msgs else None,
    )


@router.post("", status_code=201, response_model=ConversationOut)
def create(request: Request):
    with request.app.state.session_factory.begin() as session:
        c = Conversation(requirements=Requirements().model_dump())
        session.add(c)
        session.flush()
        return read_conversation(session, c.id)


@router.get("")
def list_conversations(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)
):
    with request.app.state.session_factory() as session:
        rows = session.scalars(
            select(Conversation)
            .order_by(Conversation.updated_at.desc(), Conversation.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return {
            "items": [
                {"id": c.id, "updated_at": c.updated_at, "state_version": c.state_version} for c in rows
            ],
            "total": session.scalar(select(func.count()).select_from(Conversation)),
            "page": page,
            "page_size": page_size,
        }


@router.post("/summaries", response_model=list[ConversationSummary])
def batch_summaries(body: SummaryRequest, request: Request):
    """Return lightweight summaries for browser-known conversation IDs.

    Only returns conversations that actually exist; silently drops unknown/invalid IDs.
    Used by the sidebar to display recent chats without exposing the entire database.
    Sorted by most recent activity.
    """
    if not body.ids:
        return []
    # Validate and deduplicate
    valid_ids = list(dict.fromkeys(i for i in body.ids if i and len(i) == 36))[:100]
    if not valid_ids:
        return []
    with request.app.state.session_factory() as session:
        rows = session.scalars(
            select(Conversation)
            .where(Conversation.id.in_(valid_ids))
            .order_by(Conversation.updated_at.desc())
        ).all()
        return [
            ConversationSummary(
                id=c.id,
                title=c.title,
                title_status=c.title_status,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in rows
        ]


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: UUID, request: Request):
    with request.app.state.session_factory() as session:
        return read_conversation(session, str(conversation_id))


@router.post("/{conversation_id}/messages", response_model=TurnResponse)
def send(conversation_id: UUID, body: MessageIn, request: Request):
    return process_turn(
        request.app.state.session_factory, request.app.state.extractor, str(conversation_id), body
    )


@router.post("/{conversation_id}/title", response_model=TitleOut)
def generate_conversation_title(conversation_id: UUID, request: Request):
    """Idempotent title generation.

    - Returns immediately if a final title already exists (generated or fallback).
    - Reads the first meaningful user message, generates a title with Groq.
    - Falls back to a truncated first-message if generation fails.
    - Never holds a DB transaction open during the external model call.
    - Protected against concurrent finalisation: only writes if still pending.
    """
    cid = str(conversation_id)
    settings = request.app.state.settings

    # --- Phase 1: read without a transaction ---
    with request.app.state.session_factory() as session:
        c = session.get(Conversation, cid)
        if not c:
            raise AppError(404, "not_found", "Conversation not found.")
        # Already finalised — return immediately, no model call.
        if c.title_status in ("generated", "fallback") and c.title:
            return TitleOut(id=cid, title=c.title, title_status=c.title_status)

        # Find the first meaningful user message
        first_user = session.scalar(
            select(Message)
            .where(Message.conversation_id == cid, Message.role == "user")
            .order_by(Message.sequence)
        )

    if not first_user or not is_meaningful(first_user.content):
        # No meaningful query yet; stay pending
        return TitleOut(id=cid, title=None, title_status="pending")

    # --- Phase 2: call Groq outside any transaction ---
    new_title, new_status = generate_title(settings, first_user.content)

    # --- Phase 3: write only if still pending (optimistic guard) ---
    with request.app.state.session_factory.begin() as session:
        c = session.get(Conversation, cid)
        if not c:
            raise AppError(404, "not_found", "Conversation not found.")
        if c.title_status not in ("generated", "fallback"):
            # Still pending — safe to write. Do NOT bump state_version or updated_at.
            c.title = new_title
            c.title_status = new_status

    return TitleOut(id=cid, title=new_title, title_status=new_status)
