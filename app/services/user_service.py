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

    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def get_all_users(self) -> list[User]:
        return self.repository.get_all()

    def update_user(self, user_id: int, data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(data.email)

        if existing_user and existing_user.id != user_id:
            raise ValueError("Email already registered")

        hashed_password = hash_password(data.password)

        return self.repository.update(
            user_id=user_id,
            email=data.email,
            password_hash=hashed_password,
        )

    def delete_user(self, user_id: int) -> None:
        self.repository.delete(user_id)
