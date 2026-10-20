from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings


@lru_cache
def get_session_factory():
    engine = create_engine(
        get_settings().database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 5}
    )
    return sessionmaker(engine, expire_on_commit=False)
