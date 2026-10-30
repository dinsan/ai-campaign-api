from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.pagination import DEFAULT_LIMIT
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(
        self,
        repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.repository = repository
        self.category_repository = category_repository

    def list_products(
        self,
        owner_id: int,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[Product]:
        return self.repository.get_all_by_owner(owner_id, limit=limit, offset=offset)

    def get_product(self, product_id: int, owner_id: int) -> Product:
        product = self.repository.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")
        return product

    def create_product(self, owner_id: int, data: ProductCreate) -> Product:
        self._ensure_category_is_owned(data.category_id, owner_id)

        return self.repository.create(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            website=str(data.website) if data.website else None,
            category_id=data.category_id,
        )

    def update_product(
        self,
        product_id: int,
        owner_id: int,
        data: ProductCreate,
    ) -> Product:
        self._ensure_category_is_owned(data.category_id, owner_id)

        return self.repository.update(
            product_id=product_id,
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            website=str(data.website) if data.website else None,
            category_id=data.category_id,
        )

    def delete_product(self, product_id: int, owner_id: int) -> None:
        self.repository.delete(product_id, owner_id)

    def _ensure_category_is_owned(
        self,
        category_id: int | None,
        owner_id: int,
    ) -> None:
        """A product may only be linked to a category of the same owner."""
        if category_id is None:
            return

        category = self.category_repository.get_by_id(category_id, owner_id)
        if category is None:
            raise ValueError("Category not found")
