import unittest

from fastapi.testclient import TestClient

from app.api import API_PREFIX, VERSIONS
from app.api import v1
from app.main import app


class ApiVersioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.paths = cls.client.get("/openapi.json").json()["paths"]

    def test_v1_is_the_only_served_version(self):
        self.assertEqual(VERSIONS, ["v1"])
        self.assertEqual(v1.VERSION, "v1")
        self.assertEqual(API_PREFIX, "/api")

    def test_all_endpoints_except_health_are_versioned(self):
        unversioned = [path for path in self.paths if not path.startswith("/api/v1/")]

        self.assertEqual(unversioned, ["/health"])

    def test_v1_exposes_every_feature(self):
        expected = {
            "/api/v1/auth/login",
            "/api/v1/users",
            "/api/v1/users/{user_id}",
            "/api/v1/products",
            "/api/v1/products/{product_id}",
            "/api/v1/categories",
            "/api/v1/categories/{category_id}",
            "/api/v1/search",
        }

        self.assertTrue(expected.issubset(self.paths), expected - set(self.paths))

    def test_legacy_unversioned_paths_are_not_served(self):
        for path in ["/products", "/categories", "/search", "/users", "/auth/login"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_versioned_protected_endpoint_requires_authentication(self):
        response = self.client.get("/api/v1/products")

        self.assertEqual(response.status_code, 401)

    def test_health_check_advertises_available_versions(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["api_versions"], ["v1"])


if __name__ == "__main__":
    unittest.main()
