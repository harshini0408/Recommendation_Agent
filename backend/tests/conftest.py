import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.entities import Base
from app.main import create_app
from app.config import Settings
from app.agent.demo import DemoExtractor
from scripts.seed import seed


@pytest.fixture
def factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_fks(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    seed(factory)
    yield factory
    engine.dispose()


@pytest.fixture
def client(factory):
    settings = Settings(_env_file=None, llm_mode="demo", groq_api_key="")
    with TestClient(create_app(settings, factory, DemoExtractor())) as c:
        yield c
