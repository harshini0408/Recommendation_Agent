"""Create only dedicated databases/role. Never changes an existing password or owner."""

import argparse
import re
import sys
import psycopg
from psycopg import sql
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import BACKEND_DIR, get_settings


class AdminSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env.bootstrap", extra="ignore")
    pg_admin_host: str = "localhost"
    pg_admin_port: int = 5432
    pg_admin_database: str = "postgres"
    pg_admin_user: str = "postgres"
    pg_admin_password: SecretStr = SecretStr("")


def provision(with_test=False):
    s = get_settings()
    a = AdminSettings()
    names = [s.db_name] + ([s.test_db_name] if with_test else [])
    if with_test:
        s.database_url(test=True)
    for name in [s.db_user, *names]:
        if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", name):
            raise ValueError(
                "Use lowercase project database/role names with letters, digits and underscores (3-63 chars)."
            )
    if s.db_name in ("postgres", "template0", "template1") or s.db_user == a.pg_admin_user:
        raise ValueError("Choose dedicated project database and application role names.")
    if (a.pg_admin_host, a.pg_admin_port) != (s.db_host, s.db_port):
        raise ValueError("Bootstrap host/port must match runtime host/port.")
    password = s.db_password.get_secret_value()
    if password in ("", "CHANGE_ME", "<SET_LOCALLY>"):
        raise ValueError("Set DB_PASSWORD in backend/.env before provisioning.")
    with psycopg.connect(
        host=a.pg_admin_host,
        port=a.pg_admin_port,
        dbname=a.pg_admin_database,
        user=a.pg_admin_user,
        password=a.pg_admin_password.get_secret_value(),
        connect_timeout=5,
        autocommit=True,
    ) as conn:
        role = conn.execute(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolcanlogin FROM pg_roles WHERE rolname=%s",
            (s.db_user,),
        ).fetchone()
        if role:
            if any(role[:3]) or not role[3]:
                raise ValueError(
                    "Existing application role has incompatible privileges; choose a new dedicated role."
                )
        else:
            conn.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE").format(
                    sql.Identifier(s.db_user), sql.Literal(password)
                )
            )
        for name in names:
            owner = conn.execute(
                "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=%s", (name,)
            ).fetchone()
            if owner and owner[0] != s.db_user:
                raise ValueError(
                    "Existing database has another owner. Choose a new project database; no ownership was changed."
                )
            if not owner:
                conn.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(name), sql.Identifier(s.db_user)
                    )
                )
    for name in names:
        with psycopg.connect(
            host=s.db_host, port=s.db_port, dbname=name, user=s.db_user, password=password, connect_timeout=5
        ) as conn:
            conn.execute("SELECT 1")
    print(
        "Project role/database provisioning and application login verified. No existing password was changed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-test", action="store_true")
    args = parser.parse_args()
    try:
        provision(args.with_test)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
    except psycopg.Error as exc:
        print(
            "PostgreSQL setup failed ("
            + type(exc).__name__
            + "). Check server, credentials and privileges; secrets suppressed."
        )
        sys.exit(1)
