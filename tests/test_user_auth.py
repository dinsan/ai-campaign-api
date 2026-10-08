import unittest
from unittest.mock import MagicMock, patch

from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class UserServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.service = UserService(self.repository)

    def test_create_user_success(self):
        self.repository.get_by_email.return_value = None
        created_user = User(id=1, email="test@example.com", password_hash="hashed-password")
        self.repository.create.return_value = created_user

        with patch("app.services.user_service.hash_password", return_value="hashed-password"):
            result = self.service.create_user(
                UserCreate(email="test@example.com", password="secret123")
            )

        self.repository.get_by_email.assert_called_once_with("test@example.com")
        self.repository.create.assert_called_once_with(
            email="test@example.com",
            password_hash="hashed-password",
        )
        self.assertEqual(result, created_user)

    def test_create_user_fails_for_duplicate_email(self):
        self.repository.get_by_email.return_value = User(
            id=2,
            email="test@example.com",
            password_hash="existing-hash",
        )

        with self.assertRaisesRegex(ValueError, "Email already registered"):
            self.service.create_user(
                UserCreate(email="test@example.com", password="secret123")
            )

        self.repository.create.assert_not_called()

    def test_get_user_returns_existing_user(self):
        user = User(id=3, email="user@example.com", password_hash="hash")
        self.repository.get_by_id.return_value = user

        result = self.service.get_user(3)

        self.assertEqual(result, user)
        self.repository.get_by_id.assert_called_once_with(3)

    def test_get_user_raises_when_not_found(self):
        self.repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "User not found"):
            self.service.get_user(99)

    def test_update_user_success(self):
        existing_user = User(id=5, email="same@example.com", password_hash="old-hash")
        updated_user = User(id=5, email="new@example.com", password_hash="hashed-password")
        self.repository.get_by_email.return_value = existing_user
        self.repository.update.return_value = updated_user

        with patch("app.services.user_service.hash_password", return_value="hashed-password"):
            result = self.service.update_user(
                5,
                UserCreate(email="new@example.com", password="newsecret"),
            )

        self.assertEqual(result, updated_user)
        self.repository.update.assert_called_once_with(
            user_id=5,
            email="new@example.com",
            password_hash="hashed-password",
        )

    def test_update_user_fails_for_duplicate_email_on_other_account(self):
        other_user = User(id=9, email="taken@example.com", password_hash="hash")
        self.repository.get_by_email.return_value = other_user

        with self.assertRaisesRegex(ValueError, "Email already registered"):
            self.service.update_user(
                5,
                UserCreate(email="taken@example.com", password="secret123"),
            )

        self.repository.update.assert_not_called()

    def test_delete_user_calls_repository(self):
        self.service.delete_user(7)
        self.repository.delete.assert_called_once_with(7)


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.service = AuthService(self.repository)

    def test_login_success(self):
        user = User(id=11, email="login@example.com", password_hash="hashed-password")
        self.repository.get_by_email.return_value = user

        with patch("app.services.auth_service.verify_password", return_value=True), patch(
            "app.services.auth_service.create_access_token",
            return_value="test-token",
        ):
            result = self.service.login(
                LoginRequest(email="login@example.com", password="secret123")
            )

        self.assertEqual(result, "test-token")
        self.repository.get_by_email.assert_called_once_with("login@example.com")

    def test_login_fails_for_unknown_email(self):
        self.repository.get_by_email.return_value = None

        with self.assertRaisesRegex(ValueError, "Invalid email or password"):
            self.service.login(
                LoginRequest(email="missing@example.com", password="secret123")
            )

    def test_login_fails_for_wrong_password(self):
        user = User(id=12, email="login@example.com", password_hash="hashed-password")
        self.repository.get_by_email.return_value = user

        with patch("app.services.auth_service.verify_password", return_value=False):
            with self.assertRaisesRegex(ValueError, "Invalid email or password"):
                self.service.login(
                    LoginRequest(email="login@example.com", password="wrongpassword")
                )


if __name__ == "__main__":
    unittest.main()
