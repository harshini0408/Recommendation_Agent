"""Opt-in integration run on configured *_test DB; never drops databases/tables."""

import os
import subprocess
import sys
from app.config import get_settings, BACKEND_DIR

s = get_settings()
s.database_url(test=True)  # guard against development DB
variables = dict(os.environ, DB_NAME=s.test_db_name, RUN_POSTGRES_TESTS="1", DEV_DB_NAME=s.db_name)
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND_DIR, env=variables, check=True
)
subprocess.run([sys.executable, "-m", "scripts.seed"], cwd=BACKEND_DIR, env=variables, check=True)
raise SystemExit(
    subprocess.call([sys.executable, "-m", "pytest", "-q", "-m", "postgres"], cwd=BACKEND_DIR, env=variables)
)
