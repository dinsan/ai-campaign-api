from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.core.security import hash_password


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(data.email)

        if existing_user:
            raise ValueError("Email already registered")

        hashed_password = hash_password(data.password)

        return self.repository.create(
            email=data.email,
            password_hash=hashed_password,
        )