from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate


class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    def list_categories(self, owner_id: int) -> list[Category]:
        return self.repository.get_all_by_owner(owner_id)

    def get_category(self, category_id: int, owner_id: int) -> Category:
        category = self.repository.get_by_id(category_id, owner_id)
        if category is None:
            raise ValueError("Category not found")
        return category

    def create_category(self, owner_id: int, data: CategoryCreate) -> Category:
        existing_category = self.repository.get_by_name(data.name, owner_id)
        if existing_category:
            raise ValueError("Category name already exists")

        return self.repository.create(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
        )

    def update_category(
        self,
        category_id: int,
        owner_id: int,
        data: CategoryCreate,
    ) -> Category:
        existing_category = self.repository.get_by_name(data.name, owner_id)
        if existing_category and existing_category.id != category_id:
            raise ValueError("Category name already exists")

        return self.repository.update(
            category_id=category_id,
            owner_id=owner_id,
            name=data.name,
            description=data.description,
        )

    def delete_category(self, category_id: int, owner_id: int) -> None:
        self.repository.delete(category_id, owner_id)
