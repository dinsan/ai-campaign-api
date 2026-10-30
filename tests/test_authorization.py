import unittest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.authorization import (
    Permission,
    Role,
    has_permissions,
    permissions_for,
)
from app.core.dependencies import get_current_user, require_permissions
from app.database.base import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


class PermissionMatrixTests(unittest.TestCase):
    def test_viewer_can_only_read(self):
        self.assertEqual(
            permissions_for(Role.VIEWER),
            {Permission.PRODUCTS_READ, Permission.CATEGORIES_READ},
        )

    def test_editor_can_read_and_write_products_and_categories(self):
        self.assertEqual(
            permissions_for(Role.EDITOR),
            {
                Permission.PRODUCTS_READ,
                Permission.PRODUCTS_WRITE,
                Permission.CATEGORIES_READ,
                Permission.CATEGORIES_WRITE,
            },
        )

    def test_admin_has_every_permission(self):
        self.assertEqual(permissions_for(Role.ADMIN), set(Permission))

    def test_roles_are_cumulative(self):
        self.assertTrue(permissions_for(Role.VIEWER) < permissions_for(Role.EDITOR))
        self.assertTrue(permissions_for(Role.EDITOR) < permissions_for(Role.ADMIN))

    def test_has_permissions_requires_all_listed_permissions(self):
        self.assertTrue(has_permissions(Role.EDITOR, Permission.PRODUCTS_READ, Permission.PRODUCTS_WRITE))
        self.assertFalse(has_permissions(Role.VIEWER, Permission.PRODUCTS_READ, Permission.PRODUCTS_WRITE))

    def test_has_permissions_accepts_role_value_strings(self):
        self.assertTrue(has_permissions("editor", Permission.PRODUCTS_WRITE))


class RequirePermissionsDependencyTests(unittest.TestCase):
    def test_returns_user_when_role_is_sufficient(self):
        editor = User(id=1, email="editor@example.com", password_hash="hash", role=Role.EDITOR)
        dependency = require_permissions(Permission.PRODUCTS_WRITE)

        self.assertIs(dependency(current_user=editor), editor)

    def test_rejects_user_with_insufficient_role(self):
        viewer = User(id=1, email="viewer@example.com", password_hash="hash", role=Role.VIEWER)
        dependency = require_permissions(Permission.PRODUCTS_WRITE)

        with self.assertRaises(HTTPException) as context:
            dependency(current_user=viewer)

        self.assertEqual(context.exception.status_code, 403)


class RouteAuthorizationTests(unittest.TestCase):
    """Exercise the real routes with users of each role."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        with cls.SessionLocal() as db:
            cls.users = {
                role: User(email=f"{role.value}@example.com", password_hash="hash", role=role)
                for role in Role
            }
            db.add_all(cls.users.values())
            db.flush()
            cls.user_ids = {role: user.id for role, user in cls.users.items()}
            db.commit()

        cls.active_role = Role.VIEWER

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_get_current_user():
            with cls.SessionLocal() as db:
                return db.get(User, cls.user_ids[cls.active_role])

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        # Every test starts with a fresh product/category owned by each user.
        with self.SessionLocal() as db:
            db.query(Product).delete()
            db.query(Category).delete()
            self.category_ids = {}
            self.product_ids = {}
            for role, user_id in self.user_ids.items():
                category = Category(owner_id=user_id, name="Transport")
                db.add(category)
                db.flush()
                product = Product(owner_id=user_id, name="Bike", category_id=category.id)
                db.add(product)
                db.flush()
                self.category_ids[role] = category.id
                self.product_ids[role] = product.id
            db.commit()

    def as_role(self, role: Role):
        type(self).active_role = role

    # --- reading: every role -------------------------------------------------

    def test_every_role_can_read_products_and_categories(self):
        for role in Role:
            with self.subTest(role=role):
                self.as_role(role)
                self.assertEqual(self.client.get("/api/v1/products").status_code, 200)
                self.assertEqual(
                    self.client.get(f"/api/v1/products/{self.product_ids[role]}").status_code,
                    200,
                )
                self.assertEqual(self.client.get("/api/v1/categories").status_code, 200)
                self.assertEqual(
                    self.client.get(f"/api/v1/categories/{self.category_ids[role]}").status_code,
                    200,
                )
                self.assertEqual(
                    self.client.get("/api/v1/search", params={"q": "bike"}).status_code,
                    200,
                )

    # --- writing: editor and admin only -------------------------------------

    def test_viewer_cannot_create_update_or_delete(self):
        self.as_role(Role.VIEWER)
        product_id = self.product_ids[Role.VIEWER]
        category_id = self.category_ids[Role.VIEWER]

        attempts = [
            ("POST", "/api/v1/products", {"name": "Scooter"}),
            ("PUT", f"/api/v1/products/{product_id}", {"name": "Scooter"}),
            ("DELETE", f"/api/v1/products/{product_id}", None),
            ("POST", "/api/v1/categories", {"name": "Food"}),
            ("PUT", f"/api/v1/categories/{category_id}", {"name": "Food"}),
            ("DELETE", f"/api/v1/categories/{category_id}", None),
        ]
        for method, url, body in attempts:
            with self.subTest(method=method, url=url):
                response = self.client.request(method, url, json=body)
                self.assertEqual(response.status_code, 403)
                self.assertIn("permission", response.json()["detail"].lower())

        # Nothing was changed behind the scenes.
        self.assertEqual(self.client.get(f"/api/v1/products/{product_id}").json()["name"], "Bike")
        self.assertEqual(self.client.get(f"/api/v1/categories/{category_id}").status_code, 200)

    def test_editor_and_admin_can_create_update_and_delete(self):
        for role in (Role.EDITOR, Role.ADMIN):
            with self.subTest(role=role):
                self.as_role(role)
                product_id = self.product_ids[role]
                category_id = self.category_ids[role]

                self.assertEqual(
                    self.client.post("/api/v1/products", json={"name": "Scooter"}).status_code,
                    201,
                )
                self.assertEqual(
                    self.client.put(f"/api/v1/products/{product_id}", json={"name": "Scooter"}).status_code,
                    200,
                )
                self.assertEqual(self.client.delete(f"/api/v1/products/{product_id}").status_code, 204)
                self.assertEqual(
                    self.client.post("/api/v1/categories", json={"name": "Food"}).status_code,
                    201,
                )
                self.assertEqual(
                    self.client.put(f"/api/v1/categories/{category_id}", json={"name": "Mobility"}).status_code,
                    200,
                )
                self.assertEqual(self.client.delete(f"/api/v1/categories/{category_id}").status_code, 204)

    # --- user management: admin only ----------------------------------------

    def test_only_admin_can_manage_users(self):
        viewer_id = self.user_ids[Role.VIEWER]

        for role in (Role.VIEWER, Role.EDITOR):
            with self.subTest(role=role):
                self.as_role(role)
                self.assertEqual(self.client.get("/api/v1/users").status_code, 403)
                self.assertEqual(self.client.get(f"/api/v1/users/{viewer_id}").status_code, 403)
                self.assertEqual(
                    self.client.post(
                        "/api/v1/users",
                        json={"email": "new@example.com", "password": "secret123", "role": "admin"},
                    ).status_code,
                    403,
                )

        self.as_role(Role.ADMIN)
        self.assertEqual(self.client.get("/api/v1/users").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/users/{viewer_id}").json()["role"], "viewer")

    def test_admin_can_promote_a_user_and_it_takes_effect_immediately(self):
        self.as_role(Role.ADMIN)
        viewer_id = self.user_ids[Role.VIEWER]

        response = self.client.put(
            f"/api/v1/users/{viewer_id}",
            json={"email": "viewer@example.com", "password": "secret123", "role": "editor"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "editor")

        self.as_role(Role.VIEWER)  # same account, role now read from the database
        self.assertEqual(self.client.post("/api/v1/products", json={"name": "Scooter"}).status_code, 201)

        # Restore so other tests keep a real viewer.
        self.as_role(Role.ADMIN)
        self.client.put(
            f"/api/v1/users/{viewer_id}",
            json={"email": "viewer@example.com", "password": "secret123", "role": "viewer"},
        )

    def test_role_is_validated(self):
        self.as_role(Role.ADMIN)

        response = self.client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "password": "secret123", "role": "superuser"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
