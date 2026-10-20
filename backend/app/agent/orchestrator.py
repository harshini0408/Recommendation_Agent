"""One turn: snapshot -> model -> deterministic decision -> atomic versioned save."""

from uuid import uuid4
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.models.entities import Conversation, Message, RecommendationRun, now
from app.schemas.requirements import Requirements
from app.schemas.conversations import TurnResponse
from app.agent.state import merge_state
from app.agent.clarification import clarification
from app.agent.tools import search_products, rank_products, get_product
from app.errors import AppError


def prior_request(session, cid, client_id, content):
    msg = session.scalar(
        select(Message).where(Message.conversation_id == cid, Message.client_message_id == client_id)
    )
    if msg:
        if msg.content != content:
            raise AppError(
                409, "idempotency_conflict", "This request ID was already used for different text."
            )
        return msg.response
    return None


def process_turn(factory, extractor, cid, incoming):
    client_id = str(incoming.client_message_id)
    with factory() as session:
        existing = prior_request(session, cid, client_id, incoming.content)
        if existing:
            return existing
        conversation = session.get(Conversation, cid)
        if not conversation:
            raise AppError(404, "not_found", "Conversation not found.")
        old = Requirements.model_validate(conversation.requirements)
        version = conversation.state_version
        recent = list(
            reversed(
                session.scalars(
                    select(Message)
                    .where(Message.conversation_id == cid)
                    .order_by(Message.sequence.desc())
                    .limit(6)
                ).all()
            )
        )
        history = [{"role": m.role, "content": m.content[:4000]} for m in recent]
        run = session.scalar(
            select(RecommendationRun)
            .where(RecommendationRun.conversation_id == cid)
            .order_by(RecommendationRun.created_at.desc())
            .limit(1)
        )
        previous = [r["product"] for r in run.products] if run else []
    # No open database session/transaction during the network call.
    extraction = extractor.extract(incoming.content, old, history, previous)
    user_id = str(uuid4())
    state, changed = merge_state(old, extraction, incoming.content, user_id)
    response_type = "informational"
    cards = []
    eligible = []
    diagnostic = None
    question = clarification(state)
    searched = False
    with factory() as session:
        if extraction.intent == "out_of_scope" and not extraction.changes:
            message = "I can help compare laptops in this synthetic catalogue. Tell me your use case and budget in INR."
        elif extraction.intent in ("details", "compare") and not extraction.changes and previous:
            ids = extraction.product_ids or [p["id"] for p in previous]
            allowed = {p["id"] for p in previous}
            eligible = [p for pid in ids[:2] if pid in allowed and (p := get_product(session, pid))]
            cards = rank_products(eligible, state)
            message = "Here are the recorded specifications and trade-offs for those products. Unknown specifications are marked; battery figures are synthetic estimates."
        elif question:
            response_type = "clarification"
            message = question
        else:
            searched = True
            eligible = search_products(session, state)
            cards = rank_products(eligible, state)
            if cards:
                response_type = "recommendations"
                message = f"I found {len(eligible)} catalogue product(s) meeting your mandatory constraints. "
                message += (
                    "Here are the two highest-ranked matches."
                    if len(cards) == 2
                    else "Only one product matches, so I am showing one."
                )
                if state.pending_budget:
                    state.pending_budget = None
            else:
                response_type = "no_match"
                message = "No product in this catalogue meets all your mandatory constraints. I have kept your requirements unchanged."
                if state.budget_max_inr is not None:
                    relaxed = state.model_copy(update={"budget_max_inr": None})
                    alternatives = search_products(session, relaxed)
                    if alternatives:
                        cheapest = min(alternatives, key=lambda p: (p.price_inr, p.id))
                        state.pending_budget = cheapest.price_inr
                        diagnostic = {
                            "field": "budget_max_inr",
                            "current": state.budget_max_inr,
                            "proposed": cheapest.price_inr,
                            "product_id": cheapest.id,
                            "status": "requires_confirmation",
                        }
                        message += f" The lowest price meeting all other constraints is INR {cheapest.price_inr:,}. Would you like to raise the budget to that amount?"
                if diagnostic is None:
                    state.pending_budget = None
                    message += " Which requirement would you like to reconsider? Changing budget alone may not resolve the mismatch."
        evidence = {
            "changed_fields": changed,
            "eligible_count": len(eligible),
            "searched": searched,
            "hard_filters": {
                k: v
                for k, v in state.model_dump().items()
                if k
                in [
                    "category",
                    "budget_max_inr",
                    "min_ram_gb",
                    "min_storage_gb",
                    "require_dedicated_gpu",
                    "max_weight_kg",
                    "min_battery_hours",
                    "required_features",
                ]
                and v is not None
            },
            "budget_proposal": diagnostic,
            "ranking": "Deterministic workload 50%, preferences 30%, affordability 20%; unused factors omitted.",
        }
    reply = TurnResponse(
        conversation_id=cid,
        response_type=response_type,
        assistant_message=message,
        requirements=state,
        state_version=version + 1,
        recommendations=cards,
        evidence=evidence,
        mode=extractor.mode,
    ).model_dump(mode="json")
    try:
        with factory.begin() as session:
            existing = prior_request(session, cid, client_id, incoming.content)
            if existing:
                return existing
            changed_count = session.execute(
                update(Conversation)
                .where(Conversation.id == cid, Conversation.state_version == version)
                .values(requirements=state.model_dump(), state_version=version + 1, updated_at=now())
            ).rowcount
            if changed_count != 1:
                raise AppError(
                    409,
                    "state_conflict",
                    "This conversation changed during processing. Refresh and retry.",
                    True,
                )
            session.add(
                Message(
                    id=user_id,
                    conversation_id=cid,
                    role="user",
                    content=incoming.content,
                    sequence=version * 2 + 1,
                    client_message_id=client_id,
                    response=reply,
                )
            )
            session.add(
                Message(
                    conversation_id=cid,
                    role="assistant",
                    content=message,
                    sequence=version * 2 + 2,
                    response=reply,
                )
            )
            session.flush()
            if searched:
                session.add(
                    RecommendationRun(
                        conversation_id=cid,
                        source_message_id=user_id,
                        requirement_snapshot=state.model_dump(),
                        products=cards,
                        evidence=evidence,
                        eligible_count=len(eligible),
                    )
                )
    except (IntegrityError, AppError) as exc:
        if isinstance(exc, AppError) and exc.code != "state_conflict":
            raise
        with factory() as session:
            existing = prior_request(session, cid, client_id, incoming.content)
            if existing:
                return existing
        raise AppError(409, "state_conflict", "Another turn completed first. Refresh and retry.", True)
    return reply
