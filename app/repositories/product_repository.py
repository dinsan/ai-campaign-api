from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_owner(self, owner_id: int) -> list[Product]:
        statement = select(Product).where(Product.owner_id == owner_id)
        return list(self.db.scalars(statement))

    def get_by_id(self, product_id: int, owner_id: int) -> Product | None:
        statement = select(Product).where(
            Product.id == product_id,
            Product.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def create(
        self,
        owner_id: int,
        name: str,
        description: str | None,
        website: str | None,
        category: str | None,
    ) -> Product:
        product = Product(
            owner_id=owner_id,
            name=name,
            description=description,
            website=website,
            category=category,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(
        self,
        product_id: int,
        owner_id: int,
        name: str,
        description: str | None,
        website: str | None,
        category: str | None,
    ) -> Product:
        product = self.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")

        product.name = name
        product.description = description
        product.website = website
        product.category = category
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product_id: int, owner_id: int) -> None:
        product = self.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")

        self.db.delete(product)
        self.db.commit()
