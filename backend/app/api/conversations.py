from uuid import UUID
from fastapi import APIRouter, Request, Query
from sqlalchemy import select, func
from app.models.entities import Conversation, Message
from app.schemas.requirements import Requirements
from app.schemas.conversations import ConversationOut, MessageOut, MessageIn, TurnResponse
from app.agent.orchestrator import process_turn
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


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: UUID, request: Request):
    with request.app.state.session_factory() as session:
        return read_conversation(session, str(conversation_id))


@router.post("/{conversation_id}/messages", response_model=TurnResponse)
def send(conversation_id: UUID, body: MessageIn, request: Request):
    return process_turn(
        request.app.state.session_factory, request.app.state.extractor, str(conversation_id), body
    )
