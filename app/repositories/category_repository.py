from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.repositories.search import LIKE_ESCAPE, contains_pattern


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_owner(self, owner_id: int) -> list[Category]:
        statement = select(Category).where(Category.owner_id == owner_id)
        return list(self.db.scalars(statement))

    def get_by_id(self, category_id: int, owner_id: int) -> Category | None:
        statement = select(Category).where(
            Category.id == category_id,
            Category.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def get_by_name(self, name: str, owner_id: int) -> Category | None:
        statement = select(Category).where(
            Category.name == name,
            Category.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def search_by_name(self, owner_id: int, query: str) -> list[Category]:
        """Case-insensitive partial match on name, with linked products preloaded."""
        statement = (
            select(Category)
            .where(
                Category.owner_id == owner_id,
                Category.name.ilike(contains_pattern(query), escape=LIKE_ESCAPE),
            )
            .options(selectinload(Category.products))
            .order_by(Category.name, Category.id)
        )
        return list(self.db.scalars(statement))

    def create(
        self,
        owner_id: int,
        name: str,
        description: str | None,
    ) -> Category:
        category = Category(
            owner_id=owner_id,
            name=name,
            description=description,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(
        self,
        category_id: int,
        owner_id: int,
        name: str,
        description: str | None,
    ) -> Category:
        category = self.get_by_id(category_id, owner_id)
        if category is None:
            raise ValueError("Category not found")

        category.name = name
        category.description = description
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category_id: int, owner_id: int) -> None:
        category = self.get_by_id(category_id, owner_id)
        if category is None:
            raise ValueError("Category not found")

        self.db.delete(category)
        self.db.commit()
