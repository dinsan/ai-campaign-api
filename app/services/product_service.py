from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def list_products(self, owner_id: int) -> list[Product]:
        return self.repository.get_all_by_owner(owner_id)

    def get_product(self, product_id: int, owner_id: int) -> Product:
        product = self.repository.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")
        return product

    def create_product(self, owner_id: int, data: ProductCreate) -> Product:
        return self.repository.create(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            website=str(data.website) if data.website else None,
            category=data.category,
        )

    def update_product(
        self,
        product_id: int,
        owner_id: int,
        data: ProductCreate,
    ) -> Product:
        return self.repository.update(
            product_id=product_id,
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            website=str(data.website) if data.website else None,
            category=data.category,
        )

    def delete_product(self, product_id: int, owner_id: int) -> None:
        self.repository.delete(product_id, owner_id)
