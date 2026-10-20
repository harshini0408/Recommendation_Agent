"""Application factory permits isolated, reproducible tests without real API calls."""

import logging
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings
from app.db import get_session_factory
from app.agent.llm_client import GroqExtractor
from app.agent.demo import DemoExtractor
from app.api import products, conversations, health
from app.errors import AppError

logger = logging.getLogger("electronics")


def create_app(settings=None, session_factory=None, extractor=None):
    settings = settings or get_settings()
    app = FastAPI(
        title="ClearChoice Electronics Assistant",
        version="1.0.0",
        description="Local assessment demo. Synthetic catalogue. No production authentication. All paths under /api/v1.",
    )
    app.state.settings = settings
    app.state.session_factory = session_factory or get_session_factory()
    app.state.extractor = extractor or (
        GroqExtractor(settings) if settings.llm_mode == "live" else DemoExtractor()
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    def error_body(request, code, message, retryable=False):
        return {
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "request_id": getattr(request.state, "request_id", None),
            }
        }

    @app.exception_handler(AppError)
    async def app_error(request, exc):
        return JSONResponse(error_body(request, exc.code, exc.message, exc.retryable), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [".".join(str(x) for x in e["loc"]) for e in exc.errors()]
        return JSONResponse(
            error_body(request, "validation_error", "Invalid input: " + ", ".join(fields)), status_code=422
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        logger.error("database_error request_id=%s", getattr(request.state, "request_id", None))
        return JSONResponse(
            error_body(
                request,
                "database_error",
                "Database operation failed. Check connectivity and migrations.",
                True,
            ),
            status_code=503,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.error(
            "unexpected_error type=%s request_id=%s",
            type(exc).__name__,
            getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            error_body(
                request, "internal_error", "Unexpected server error. Check the server log request ID.", True
            ),
            status_code=500,
        )

    app.include_router(products.router)
    app.include_router(conversations.router)
    app.include_router(health.router)
    return app


app = create_app()
