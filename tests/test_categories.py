import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate
from app.services.category_service import CategoryService


class CategoryRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.owner = User(email="owner@example.com", password_hash="hash")
        self.other_owner = User(email="other@example.com", password_hash="hash")
        self.db.add_all([self.owner, self.other_owner])
        self.db.flush()
        self.category = Category(owner_id=self.owner.id, name="Transport")
        self.db.add(self.category)
        self.db.commit()
        self.repository = CategoryRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_list_categories_returns_only_owned_categories(self):
        self.db.add(Category(owner_id=self.other_owner.id, name="Food"))
        self.db.commit()

        categories = self.repository.get_all_by_owner(self.owner.id)

        self.assertEqual([category.id for category in categories], [self.category.id])

    def test_get_category_hides_categories_owned_by_another_user(self):
        category = self.repository.get_by_id(self.category.id, self.other_owner.id)

        self.assertIsNone(category)

    def test_get_by_name_scopes_to_owner(self):
        self.assertEqual(
            self.repository.get_by_name("Transport", self.owner.id),
            self.category,
        )
        self.assertIsNone(self.repository.get_by_name("Transport", self.other_owner.id))

    def test_create_persists_category(self):
        category = self.repository.create(
            owner_id=self.owner.id,
            name="Food",
            description="Groceries and meals",
        )

        self.assertIsNotNone(category.id)
        self.assertEqual(category.owner_id, self.owner.id)
        self.assertEqual(category.name, "Food")
        self.assertEqual(category.description, "Groceries and meals")

    def test_same_name_is_allowed_for_different_owners(self):
        category = self.repository.create(
            owner_id=self.other_owner.id,
            name="Transport",
            description=None,
        )

        self.assertIsNotNone(category.id)

    def test_duplicate_name_for_same_owner_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            self.repository.create(
                owner_id=self.owner.id,
                name="Transport",
                description=None,
            )
        self.db.rollback()

    def test_update_changes_owned_category(self):
        category = self.repository.update(
            category_id=self.category.id,
            owner_id=self.owner.id,
            name="Mobility",
            description="Bikes and scooters",
        )

        self.assertEqual(category.name, "Mobility")
        self.assertEqual(category.description, "Bikes and scooters")

    def test_update_rejects_category_owned_by_another_user(self):
        with self.assertRaisesRegex(ValueError, "Category not found"):
            self.repository.update(
                category_id=self.category.id,
                owner_id=self.other_owner.id,
                name="Mobility",
                description=None,
            )

    def test_delete_removes_owned_category(self):
        self.repository.delete(self.category.id, self.owner.id)

        self.assertIsNone(self.repository.get_by_id(self.category.id, self.owner.id))

    def test_delete_rejects_category_owned_by_another_user(self):
        with self.assertRaisesRegex(ValueError, "Category not found"):
            self.repository.delete(self.category.id, self.other_owner.id)

    def test_delete_unlinks_products_without_deleting_them(self):
        product = Product(
            owner_id=self.owner.id,
            name="Bike",
            category_id=self.category.id,
        )
        self.db.add(product)
        self.db.commit()

        self.repository.delete(self.category.id, self.owner.id)
        self.db.refresh(product)

        self.assertIsNone(product.category_id)
        self.assertIsNotNone(self.db.get(Product, product.id))


class CategoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.service = CategoryService(self.repository)

    def test_list_categories_scopes_to_owner(self):
        categories = [Category(id=1, owner_id=7, name="Transport")]
        self.repository.get_all_by_owner.return_value = categories

        result = self.service.list_categories(7)

        self.assertEqual(result, categories)
        self.repository.get_all_by_owner.assert_called_once_with(7)

    def test_get_category_scopes_to_owner(self):
        category = Category(id=1, owner_id=7, name="Transport")
        self.repository.get_by_id.return_value = category

        result = self.service.get_category(1, 7)

        self.assertEqual(result, category)
        self.repository.get_by_id.assert_called_once_with(1, 7)

    def test_get_category_raises_when_not_found_for_owner(self):
        self.repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "Category not found"):
            self.service.get_category(1, 7)

    def test_create_category_persists_optional_fields(self):
        data = CategoryCreate(name="Transport", description="Bikes and scooters")
        category = Category(id=1, owner_id=7, name="Transport")
        self.repository.get_by_name.return_value = None
        self.repository.create.return_value = category

        result = self.service.create_category(7, data)

        self.assertEqual(result, category)
        self.repository.get_by_name.assert_called_once_with("Transport", 7)
        self.repository.create.assert_called_once_with(
            owner_id=7,
            name="Transport",
            description="Bikes and scooters",
        )

    def test_create_category_fails_for_duplicate_name(self):
        self.repository.get_by_name.return_value = Category(
            id=2,
            owner_id=7,
            name="Transport",
        )

        with self.assertRaisesRegex(ValueError, "Category name already exists"):
            self.service.create_category(7, CategoryCreate(name="Transport"))

        self.repository.create.assert_not_called()

    def test_update_category_scopes_to_owner(self):
        data = CategoryCreate(name="Mobility")
        self.repository.get_by_name.return_value = None

        self.service.update_category(1, 7, data)

        self.repository.update.assert_called_once_with(
            category_id=1,
            owner_id=7,
            name="Mobility",
            description=None,
        )

    def test_update_category_allows_keeping_own_name(self):
        self.repository.get_by_name.return_value = Category(
            id=1,
            owner_id=7,
            name="Transport",
        )

        self.service.update_category(1, 7, CategoryCreate(name="Transport"))

        self.repository.update.assert_called_once()

    def test_update_category_fails_for_duplicate_name_on_other_category(self):
        self.repository.get_by_name.return_value = Category(
            id=9,
            owner_id=7,
            name="Transport",
        )

        with self.assertRaisesRegex(ValueError, "Category name already exists"):
            self.service.update_category(1, 7, CategoryCreate(name="Transport"))

        self.repository.update.assert_not_called()

    def test_delete_category_scopes_to_owner(self):
        self.service.delete_category(1, 7)
        self.repository.delete.assert_called_once_with(1, 7)


if __name__ == "__main__":
    unittest.main()
