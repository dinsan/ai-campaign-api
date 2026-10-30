from dataclasses import dataclass, field

from app.models.category import Category
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository

# Search is for finding things quickly, not for paging through everything, so
# each section is capped independently.
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 100


@dataclass
class SearchResult:
    query: str
    products: list[Product] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)


class SearchService:
    def __init__(
        self,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.product_repository = product_repository
        self.category_repository = category_repository

    def search(
        self,
        owner_id: int,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> SearchResult:
        """Find the owner's products and categories whose name contains `query`.

        Matched products carry their linked category; matched categories carry
        their linked products. Each section returns at most `limit` items.
        """
        query = query.strip()
        if not query:
            raise ValueError("Search query must not be empty")

        return SearchResult(
            query=query,
            products=self.product_repository.search_by_name(owner_id, query, limit=limit),
            categories=self.category_repository.search_by_name(owner_id, query, limit=limit),
        )
