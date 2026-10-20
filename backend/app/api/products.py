from typing import Literal
from fastapi import APIRouter, Query, Request
from app.schemas.products import ProductOut, ProductPage
from app.schemas.requirements import Requirements
from app.models.entities import Product
from app.services.catalogue import list_products
from app.errors import AppError

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("", response_model=ProductPage)
def products(
    request: Request,
    category: str = "laptop",
    max_price_inr: int | None = Query(None, gt=0, le=10000000),
    min_ram_gb: int | None = Query(None, gt=0, le=1024),
    min_storage_gb: int | None = Query(None, gt=0, le=100000),
    dedicated_gpu: bool | None = None,
    max_weight_kg: float | None = Query(None, gt=0, le=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: Literal["price_asc", "price_desc", "name"] = "price_asc",
):
    r = Requirements(
        category=category,
        budget_max_inr=max_price_inr,
        min_ram_gb=min_ram_gb,
        min_storage_gb=min_storage_gb,
        require_dedicated_gpu=dedicated_gpu,
        max_weight_kg=max_weight_kg,
    )
    with request.app.state.session_factory() as session:
        return list_products(session, r, page, page_size, sort)


@router.get("/{product_id}", response_model=ProductOut)
def product(product_id: str, request: Request):
    with request.app.state.session_factory() as session:
        p = session.get(Product, product_id)
        if not p:
            raise AppError(404, "not_found", "Product not found.")
        return ProductOut.model_validate(p)
