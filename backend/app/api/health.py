from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["System"])


@router.get("/health")
def health(request: Request):
    try:
        with request.app.state.session_factory() as session:
            session.execute(text("SELECT 1 FROM products LIMIT 1"))
    except SQLAlchemyError:
        raise AppError(
            503, "database_unavailable", "Database unavailable or migrations have not been applied.", True
        )
    return {"status": "ok", "database": "ready"}


@router.get("/meta")
def meta(request: Request):
    settings = request.app.state.settings
    return {
        "name": "ClearChoice",
        "catalogue": "synthetic laptops",
        "mode": request.app.state.extractor.mode,
        "provider": "Groq" if settings.llm_mode == "live" else "limited demo parser",
        "model": settings.groq_model if settings.llm_mode == "live" else None,
        "llm_configured": bool(settings.groq_api_key.get_secret_value()),
        "authentication": "local demo only",
    }
