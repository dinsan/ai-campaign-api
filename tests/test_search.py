import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.search import contains_pattern
from app.schemas.search import SearchResponse
from app.services.search_service import SearchResult, SearchService


class ContainsPatternTests(unittest.TestCase):
    def test_wraps_query_in_wildcards(self):
        self.assertEqual(contains_pattern("bike"), "%bike%")

    def test_escapes_like_wildcards_in_query(self):
        self.assertEqual(contains_pattern("50%_off"), "%50\\%\\_off%")

    def test_escapes_backslash_in_query(self):
        self.assertEqual(contains_pattern("a\\b"), "%a\\\\b%")


class SearchRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.owner = User(email="owner@example.com", password_hash="hash")
        self.other_owner = User(email="other@example.com", password_hash="hash")
        self.db.add_all([self.owner, self.other_owner])
        self.db.flush()

        self.transport = Category(owner_id=self.owner.id, name="Transport")
        self.food = Category(owner_id=self.owner.id, name="Food")
        self.other_transport = Category(owner_id=self.other_owner.id, name="Transport")
        self.db.add_all([self.transport, self.food, self.other_transport])
        self.db.flush()

        self.bike = Product(
            owner_id=self.owner.id,
            name="Electric Bike",
            category_id=self.transport.id,
        )
        self.scooter = Product(
            owner_id=self.owner.id,
            name="Scooter",
            category_id=self.transport.id,
        )
        self.uncategorised = Product(owner_id=self.owner.id, name="Bike helmet")
        self.other_bike = Product(owner_id=self.other_owner.id, name="Bike")
        self.db.add_all([self.bike, self.scooter, self.uncategorised, self.other_bike])
        self.db.commit()

        self.product_repository = ProductRepository(self.db)
        self.category_repository = CategoryRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_product_search_is_case_insensitive_partial_match(self):
        products = self.product_repository.search_by_name(self.owner.id, "bIkE")

        self.assertEqual(
            [product.name for product in products],
            ["Bike helmet", "Electric Bike"],
        )

    def test_product_search_returns_only_owned_products(self):
        products = self.product_repository.search_by_name(self.other_owner.id, "bike")

        self.assertEqual([product.id for product in products], [self.other_bike.id])

    def test_product_search_includes_linked_category(self):
        products = self.product_repository.search_by_name(self.owner.id, "electric")

        self.assertEqual(products[0].category.name, "Transport")

    def test_product_search_treats_wildcards_literally(self):
        self.db.add(Product(owner_id=self.owner.id, name="100% cotton"))
        self.db.commit()

        self.assertEqual(len(self.product_repository.search_by_name(self.owner.id, "%")), 1)
        self.assertEqual(len(self.product_repository.search_by_name(self.owner.id, "_")), 0)

    def test_product_search_respects_limit(self):
        products = self.product_repository.search_by_name(self.owner.id, "bike", limit=1)

        self.assertEqual([product.name for product in products], ["Bike helmet"])

    def test_product_search_returns_empty_list_when_nothing_matches(self):
        self.assertEqual(self.product_repository.search_by_name(self.owner.id, "car"), [])

    def test_category_search_is_case_insensitive_partial_match(self):
        categories = self.category_repository.search_by_name(self.owner.id, "TRANS")

        self.assertEqual([category.id for category in categories], [self.transport.id])

    def test_category_search_returns_only_owned_categories(self):
        categories = self.category_repository.search_by_name(self.other_owner.id, "transport")

        self.assertEqual([category.id for category in categories], [self.other_transport.id])

    def test_category_search_includes_linked_products(self):
        categories = self.category_repository.search_by_name(self.owner.id, "transport")

        self.assertEqual(
            sorted(product.name for product in categories[0].products),
            ["Electric Bike", "Scooter"],
        )

    def test_category_search_returns_empty_list_when_nothing_matches(self):
        self.assertEqual(self.category_repository.search_by_name(self.owner.id, "toys"), [])


class SearchServiceTests(unittest.TestCase):
    def setUp(self):
        self.product_repository = MagicMock()
        self.category_repository = MagicMock()
        self.service = SearchService(self.product_repository, self.category_repository)

    def test_search_combines_products_and_categories_for_owner(self):
        products = [Product(id=1, owner_id=7, name="Bike")]
        categories = [Category(id=2, owner_id=7, name="Bikes")]
        self.product_repository.search_by_name.return_value = products
        self.category_repository.search_by_name.return_value = categories

        result = self.service.search(7, "bike", limit=5)

        self.assertEqual(result, SearchResult(query="bike", products=products, categories=categories))
        self.product_repository.search_by_name.assert_called_once_with(7, "bike", limit=5)
        self.category_repository.search_by_name.assert_called_once_with(7, "bike", limit=5)

    def test_search_trims_surrounding_whitespace(self):
        result = self.service.search(7, "  bike  ")

        self.assertEqual(result.query, "bike")
        self.product_repository.search_by_name.assert_called_once_with(7, "bike", limit=20)
        self.category_repository.search_by_name.assert_called_once_with(7, "bike", limit=20)

    def test_search_rejects_blank_query(self):
        with self.assertRaisesRegex(ValueError, "Search query must not be empty"):
            self.service.search(7, "   ")

        self.product_repository.search_by_name.assert_not_called()
        self.category_repository.search_by_name.assert_not_called()


class SearchResponseTests(unittest.TestCase):
    def test_response_embeds_linked_category_and_products(self):
        category = Category(id=2, owner_id=7, name="Transport", description="Wheels")
        product = Product(id=1, owner_id=7, name="Bike", category=category)
        category.products = [product]
        result = SearchResult(query="bike", products=[product], categories=[category])

        response = SearchResponse.model_validate(result).model_dump()

        self.assertEqual(
            response,
            {
                "query": "bike",
                "products": [
                    {
                        "id": 1,
                        "name": "Bike",
                        "description": None,
                        "website": None,
                        "category": {"id": 2, "name": "Transport", "description": "Wheels"},
                    }
                ],
                "categories": [
                    {
                        "id": 2,
                        "name": "Transport",
                        "description": "Wheels",
                        "products": [
                            {"id": 1, "name": "Bike", "description": None, "website": None}
                        ],
                    }
                ],
            },
        )

    def test_response_allows_product_without_category(self):
        product = Product(id=1, owner_id=7, name="Bike")
        result = SearchResult(query="bike", products=[product])

        response = SearchResponse.model_validate(result).model_dump()

        self.assertIsNone(response["products"][0]["category"])
        self.assertEqual(response["categories"], [])


if __name__ == "__main__":
    unittest.main()
