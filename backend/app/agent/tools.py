"""Only these application-owned catalogue functions are exposed to orchestration."""

from app.models.entities import Product
from app.services.catalogue import search_products
from app.services.ranking import rank_products


def get_product(session, product_id):
    return session.get(Product, product_id)


__all__ = ["search_products", "rank_products", "get_product"]
