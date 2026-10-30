import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService


class ProductRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.owner = User(email="owner@example.com", password_hash="hash")
        self.other_owner = User(email="other@example.com", password_hash="hash")
        self.db.add_all([self.owner, self.other_owner])
        self.db.flush()
        self.product = Product(owner_id=self.owner.id, name="Bike")
        self.db.add(self.product)
        self.db.commit()
        self.repository = ProductRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_list_products_returns_only_owned_products(self):
        products = self.repository.get_all_by_owner(self.owner.id)

        self.assertEqual([product.id for product in products], [self.product.id])

    def test_get_product_hides_products_owned_by_another_user(self):
        product = self.repository.get_by_id(self.product.id, self.other_owner.id)

        self.assertIsNone(product)

    def test_create_product_stores_category_link(self):
        category = Category(owner_id=self.owner.id, name="Transport")
        self.db.add(category)
        self.db.commit()

        product = self.repository.create(
            owner_id=self.owner.id,
            name="Scooter",
            description=None,
            website=None,
            category_id=category.id,
        )

        self.assertEqual(product.category_id, category.id)
        self.assertEqual(product.category, category)


class ProductServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.category_repository = MagicMock()
        self.service = ProductService(self.repository, self.category_repository)

    def test_list_products_scopes_to_owner(self):
        products = [Product(id=1, owner_id=7, name="Bike")]
        self.repository.get_all_by_owner.return_value = products

        result = self.service.list_products(7)

        self.assertEqual(result, products)
        self.repository.get_all_by_owner.assert_called_once_with(7)

    def test_get_product_scopes_to_owner(self):
        product = Product(id=1, owner_id=7, name="Bike")
        self.repository.get_by_id.return_value = product

        result = self.service.get_product(1, 7)

        self.assertEqual(result, product)
        self.repository.get_by_id.assert_called_once_with(1, 7)

    def test_get_product_raises_when_not_found_for_owner(self):
        self.repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "Product not found"):
            self.service.get_product(1, 7)

    def test_create_product_persists_optional_fields(self):
        data = ProductCreate(
            name="Bike",
            description="Electric bike subscription",
            website="https://example.com",
            category_id=3,
        )
        product = Product(id=1, owner_id=7, name="Bike", category_id=3)
        self.category_repository.get_by_id.return_value = Category(
            id=3,
            owner_id=7,
            name="Transport",
        )
        self.repository.create.return_value = product

        result = self.service.create_product(7, data)

        self.assertEqual(result, product)
        self.category_repository.get_by_id.assert_called_once_with(3, 7)
        self.repository.create.assert_called_once_with(
            owner_id=7,
            name="Bike",
            description="Electric bike subscription",
            website="https://example.com/",
            category_id=3,
        )

    def test_create_product_without_category_skips_category_lookup(self):
        data = ProductCreate(name="Bike")

        self.service.create_product(7, data)

        self.category_repository.get_by_id.assert_not_called()
        self.repository.create.assert_called_once_with(
            owner_id=7,
            name="Bike",
            description=None,
            website=None,
            category_id=None,
        )

    def test_create_product_rejects_category_not_owned_by_user(self):
        data = ProductCreate(name="Bike", category_id=3)
        self.category_repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "Category not found"):
            self.service.create_product(7, data)

        self.category_repository.get_by_id.assert_called_once_with(3, 7)
        self.repository.create.assert_not_called()

    def test_update_product_scopes_to_owner(self):
        data = ProductCreate(name="Updated bike")

        self.service.update_product(1, 7, data)

        self.repository.update.assert_called_once_with(
            product_id=1,
            owner_id=7,
            name="Updated bike",
            description=None,
            website=None,
            category_id=None,
        )

    def test_update_product_links_owned_category(self):
        data = ProductCreate(name="Updated bike", category_id=3)
        self.category_repository.get_by_id.return_value = Category(
            id=3,
            owner_id=7,
            name="Transport",
        )

        self.service.update_product(1, 7, data)

        self.category_repository.get_by_id.assert_called_once_with(3, 7)
        self.repository.update.assert_called_once_with(
            product_id=1,
            owner_id=7,
            name="Updated bike",
            description=None,
            website=None,
            category_id=3,
        )

    def test_update_product_rejects_category_not_owned_by_user(self):
        data = ProductCreate(name="Updated bike", category_id=3)
        self.category_repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "Category not found"):
            self.service.update_product(1, 7, data)

        self.repository.update.assert_not_called()

    def test_delete_product_scopes_to_owner(self):
        self.service.delete_product(1, 7)
        self.repository.delete.assert_called_once_with(1, 7)


if __name__ == "__main__":
    unittest.main()
