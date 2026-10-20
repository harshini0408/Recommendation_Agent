"""Print non-secret readiness checks; no API request and no writes."""

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings
from app.db import get_session_factory
from app.models.entities import Product

s = get_settings()
print("LLM mode:", s.llm_mode)
print("Groq key configured:", bool(s.groq_api_key.get_secret_value()))
try:
    with get_session_factory()() as session:
        print("Database ready. Catalogue rows:", session.scalar(select(func.count()).select_from(Product)))
except SQLAlchemyError:
    raise SystemExit("Database check failed. Verify server/configuration and apply migrations.")
