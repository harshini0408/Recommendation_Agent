"""Idempotent upsert of the 40 bundled synthetic IDs; no deletes."""

import json
from app.config import BACKEND_DIR
from app.db import get_session_factory
from app.models.entities import Product
from app.schemas.products import ProductOut


def load_seed():
    raw = json.loads((BACKEND_DIR / "data/products.json").read_text(encoding="utf-8"))
    rows = [ProductOut.model_validate(row).model_dump() for row in raw]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate seed IDs")
    if not all(r["is_synthetic"] for r in rows):
        raise ValueError("Seeds must be labelled synthetic")
    return rows


def seed(factory):
    rows = load_seed()
    with factory.begin() as session:
        for row in rows:
            p = session.get(Product, row["id"])
            if p:
                if not p.is_synthetic:
                    raise ValueError("Seed ID collides with a non-synthetic record; stopped.")
                for key, value in row.items():
                    setattr(p, key, value)
            else:
                session.add(Product(**row))
    return len(rows)


if __name__ == "__main__":
    from sqlalchemy.exc import SQLAlchemyError

    try:
        print(f"Upserted {seed(get_session_factory())} synthetic catalogue records.")
    except SQLAlchemyError:
        raise SystemExit(
            "Seed failed: verify DB credentials and run alembic upgrade head first. No secrets displayed."
        )
