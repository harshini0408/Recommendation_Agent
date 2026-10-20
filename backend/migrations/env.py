from alembic import context
from sqlalchemy import create_engine, pool
from app.config import get_settings
from app.models.entities import Base

config = context.config
target_metadata = Base.metadata
url = get_settings().database_url()
if context.is_offline_mode():
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connectable = create_engine(url, poolclass=pool.NullPool, connect_args={"connect_timeout": 5})
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
