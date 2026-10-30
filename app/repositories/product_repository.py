from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.repositories.pagination import DEFAULT_LIMIT
from app.repositories.search import LIKE_ESCAPE, contains_pattern


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_owner(
        self,
        owner_id: int,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[Product]:
        statement = (
            select(Product)
            .where(Product.owner_id == owner_id)
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))

    def get_by_id(self, product_id: int, owner_id: int) -> Product | None:
        statement = select(Product).where(
            Product.id == product_id,
            Product.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def search_by_name(
        self,
        owner_id: int,
        query: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Product]:
        """Case-insensitive partial match on name, with the category preloaded."""
        statement = (
            select(Product)
            .where(
                Product.owner_id == owner_id,
                Product.name.ilike(contains_pattern(query), escape=LIKE_ESCAPE),
            )
            .options(joinedload(Product.category))
            .order_by(Product.name, Product.id)
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def create(
        self,
        owner_id: int,
        name: str,
        description: str | None,
        website: str | None,
        category_id: int | None,
    ) -> Product:
        product = Product(
            owner_id=owner_id,
            name=name,
            description=description,
            website=website,
            category_id=category_id,
        )
        self.db.add(product)
        self._commit_or_raise_missing_category()
        self.db.refresh(product)
        return product

    def update(
        self,
        product_id: int,
        owner_id: int,
        name: str,
        description: str | None,
        website: str | None,
        category_id: int | None,
    ) -> Product:
        product = self.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")

        product.name = name
        product.description = description
        product.website = website
        product.category_id = category_id
        self._commit_or_raise_missing_category()
        self.db.refresh(product)
        return product

    def delete(self, product_id: int, owner_id: int) -> None:
        product = self.get_by_id(product_id, owner_id)
        if product is None:
            raise ValueError("Product not found")

        self.db.delete(product)
        self.db.commit()

    def _commit_or_raise_missing_category(self) -> None:
        """Commit, turning a foreign-key violation into a domain error.

        The service verifies the category exists first, but it may be deleted
        by a concurrent request before this commit lands.
        """
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Category not found") from exc
