"""All SQL is constructed from application-owned, typed filters."""

from sqlalchemy import select, func
from app.models.entities import Product
from app.schemas.products import ProductOut
from app.schemas.requirements import Requirements


def filtered_query(r: Requirements):
    q = select(Product).where(Product.category == r.category)
    if r.budget_max_inr is not None:
        q = q.where(Product.price_inr <= r.budget_max_inr)
    if r.min_ram_gb is not None:
        q = q.where(Product.ram_gb >= r.min_ram_gb)
    if r.min_storage_gb is not None:
        q = q.where(Product.storage_gb >= r.min_storage_gb)
    if r.require_dedicated_gpu is not None:
        q = q.where(Product.dedicated_gpu == r.require_dedicated_gpu)
    if r.max_weight_kg is not None:
        q = q.where(Product.weight_kg <= r.max_weight_kg)
    if r.min_battery_hours is not None:
        q = q.where(Product.battery_hours >= r.min_battery_hours)
    return q


def search_products(session, r: Requirements):
    products = session.scalars(filtered_query(r).order_by(Product.price_inr, Product.id)).all()
    # Feature membership is portable across Postgres and isolated unit tests.
    required = {f.casefold() for f in r.required_features}
    return [p for p in products if required <= {f.casefold() for f in p.feature_tags}]


def product_dict(p):
    return ProductOut.model_validate(p).model_dump()


def list_products(session, r, page=1, page_size=20, sort="price_asc"):
    q = filtered_query(r)
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    orders = {
        "price_asc": Product.price_inr.asc(),
        "price_desc": Product.price_inr.desc(),
        "name": Product.name.asc(),
    }
    rows = session.scalars(
        q.order_by(orders[sort], Product.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [product_dict(p) for p in rows], "total": total, "page": page, "page_size": page_size}
