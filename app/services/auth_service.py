from functools import lru_cache

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    """A throwaway hash used to keep login timing constant.

    Computed once, on first use, so application start-up is not slowed down.
    """
    return hash_password("not-a-real-password")


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def login(self, data: LoginRequest) -> str:
        user = self.repository.get_by_email(data.email)

        if not user:
            # Spend the same time as a real verification so an attacker cannot
            # tell registered emails from unknown ones by measuring latency.
            verify_password(data.password, _dummy_password_hash())
            raise ValueError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password")

        return create_access_token(user.id)
