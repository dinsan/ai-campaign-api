from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def login(self, data: LoginRequest) -> str:
        user = self.repository.get_by_email(data.email)

        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password")

        return create_access_token(user.id)