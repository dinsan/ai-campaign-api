import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.authorization import Role
from app.core.config import JWT_SECRET_MIN_LENGTH, Settings
from app.database.base import Base
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class SettingsHardeningTests(unittest.TestCase):
    def test_short_jwt_secret_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "at least"):
            Settings(database_url="sqlite://", jwt_secret_key="short", _env_file=None)

    def test_jwt_secret_of_minimum_length_is_accepted(self):
        settings = Settings(
            database_url="sqlite://",
            jwt_secret_key="x" * JWT_SECRET_MIN_LENGTH,
            _env_file=None,
        )

        self.assertEqual(len(settings.jwt_secret_key), JWT_SECRET_MIN_LENGTH)


class PasswordPolicyTests(unittest.TestCase):
    def test_create_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="a@example.com", password="short")

    def test_create_rejects_empty_password(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="a@example.com", password="")

    def test_create_rejects_excessively_long_password(self):
        with self.assertRaises(ValidationError):
            UserCreate(email="a@example.com", password="x" * 129)

    def test_login_does_not_enforce_minimum_length(self):
        # Accounts created before the policy may have shorter passwords.
        self.assertEqual(LoginRequest(email="a@example.com", password="abc").password, "abc")

    def test_login_still_caps_length(self):
        with self.assertRaises(ValidationError):
            LoginRequest(email="a@example.com", password="x" * 129)


class EmailNormalizationTests(unittest.TestCase):
    def test_create_lowercases_and_trims_email(self):
        data = UserCreate(email="  Admin@Example.COM ", password="secret123")

        self.assertEqual(data.email, "admin@example.com")

    def test_update_lowercases_email(self):
        data = UserUpdate(email="Admin@Example.COM", role=Role.VIEWER)

        self.assertEqual(data.email, "admin@example.com")


class UserRepositoryHardeningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(User(email="Legacy@Example.com", password_hash="hash"))
        self.db.commit()
        self.repository = UserRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_get_by_email_is_case_insensitive(self):
        for candidate in ["legacy@example.com", "LEGACY@EXAMPLE.COM", " Legacy@Example.com "]:
            with self.subTest(candidate=candidate):
                self.assertIsNotNone(self.repository.get_by_email(candidate))

    def test_duplicate_email_surfaces_as_domain_error(self):
        with self.assertRaisesRegex(ValueError, "Email already registered"):
            self.repository.create(
                email="Legacy@Example.com",
                password_hash="hash",
                role=Role.VIEWER,
            )

        self.assertEqual(len(self.repository.get_all()), 1)

    def test_get_all_is_ordered_and_paginated(self):
        self.db.add_all(
            [User(email=f"user{i}@example.com", password_hash="hash") for i in range(3)]
        )
        self.db.commit()

        page = self.repository.get_all(limit=2, offset=1)

        self.assertEqual([user.email for user in page], ["user0@example.com", "user1@example.com"])


class LoginTimingTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.service = AuthService(self.repository)

    def test_unknown_email_still_runs_a_password_verification(self):
        self.repository.get_by_email.return_value = None

        with patch("app.services.auth_service.verify_password", return_value=False) as verify, patch(
            "app.services.auth_service._dummy_password_hash",
            return_value="dummy-hash",
        ):
            with self.assertRaisesRegex(ValueError, "Invalid email or password"):
                self.service.login(LoginRequest(email="missing@example.com", password="secret123"))

        verify.assert_called_once_with("secret123", "dummy-hash")


class UserUpdateWithoutPasswordTests(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.service = UserService(self.repository)

    def test_update_keeps_existing_password_when_none_supplied(self):
        self.repository.get_by_id.return_value = User(
            id=5, email="user@example.com", password_hash="existing-hash", role=Role.VIEWER
        )
        self.repository.get_by_email.return_value = None

        with patch("app.services.user_service.hash_password") as hash_password:
            self.service.update_user(5, UserUpdate(email="user@example.com", role=Role.EDITOR))

        hash_password.assert_not_called()
        self.repository.update.assert_called_once_with(
            user_id=5,
            email="user@example.com",
            password_hash="existing-hash",
            role=Role.EDITOR,
        )

    def test_update_hashes_new_password_when_supplied(self):
        self.repository.get_by_id.return_value = User(
            id=5, email="user@example.com", password_hash="existing-hash", role=Role.VIEWER
        )
        self.repository.get_by_email.return_value = None

        with patch("app.services.user_service.hash_password", return_value="new-hash"):
            self.service.update_user(
                5, UserUpdate(email="user@example.com", password="newsecret", role=Role.VIEWER)
            )

        self.repository.update.assert_called_once_with(
            user_id=5,
            email="user@example.com",
            password_hash="new-hash",
            role=Role.VIEWER,
        )

    def test_update_raises_when_user_is_missing(self):
        self.repository.get_by_id.return_value = None

        with self.assertRaisesRegex(ValueError, "User not found"):
            self.service.update_user(5, UserUpdate(email="user@example.com", role=Role.VIEWER))


if __name__ == "__main__":
    unittest.main()
