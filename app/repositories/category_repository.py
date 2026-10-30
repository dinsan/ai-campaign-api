from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.repositories.pagination import DEFAULT_LIMIT
from app.repositories.search import LIKE_ESCAPE, contains_pattern


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_owner(
        self,
        owner_id: int,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[Category]:
        statement = (
            select(Category)
            .where(Category.owner_id == owner_id)
            .order_by(Category.id)
            .limit(limit)
            .offset(offset)
        )
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

    def search_by_name(
        self,
        owner_id: int,
        query: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Category]:
        """Case-insensitive partial match on name, with linked products preloaded."""
        statement = (
            select(Category)
            .where(
                Category.owner_id == owner_id,
                Category.name.ilike(contains_pattern(query), escape=LIKE_ESCAPE),
            )
            .options(selectinload(Category.products))
            .order_by(Category.name, Category.id)
            .limit(limit)
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
        self._commit_or_raise_duplicate()
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
        self._commit_or_raise_duplicate()
        self.db.refresh(category)
        return category

    def delete(self, category_id: int, owner_id: int) -> None:
        category = self.get_by_id(category_id, owner_id)
        if category is None:
            raise ValueError("Category not found")

        self.db.delete(category)
        self.db.commit()

    def _commit_or_raise_duplicate(self) -> None:
        """Commit, turning a unique-constraint violation into a domain error.

        The service checks for duplicates first, but two concurrent requests
        can both pass that check; the database constraint is the final word.
        """
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Category name already exists") from exc
