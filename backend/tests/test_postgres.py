"""Opt-in checks after migrations/seed on the dedicated test DB. No deletes."""

import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.agent.demo import DemoExtractor
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.getenv("RUN_POSTGRES_TESTS") != "1",
        reason="Run python -m scripts.run_postgres_tests for PostgreSQL checks",
    ),
]


def test_migrated_postgres_round_trip():
    s = Settings()
    assert s.db_name.endswith("_test") and s.db_name != os.getenv("DEV_DB_NAME")
    engine = create_engine(s.database_url())
    factory = sessionmaker(engine, expire_on_commit=False)
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0001_initial"
        assert len(inspect(conn).get_foreign_keys("recommendation_runs")) == 2
    with TestClient(create_app(s, factory, DemoExtractor())) as client:
        cid = client.post("/api/v1/conversations").json()["id"]
        data = {"content": "Programming under 80000 with 16 GB RAM", "client_message_id": str(uuid4())}
        a = client.post(f"/api/v1/conversations/{cid}/messages", json=data)
        assert a.status_code == 200 and len(a.json()["recommendations"]) == 2
        assert client.post(f"/api/v1/conversations/{cid}/messages", json=data).json() == a.json()
        assert client.get(f"/api/v1/conversations/{cid}").json()["state_version"] == 1
    engine.dispose()
