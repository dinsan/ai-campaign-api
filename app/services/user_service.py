from app.models.user import User
from app.repositories.pagination import DEFAULT_LIMIT
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
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
            role=data.role,
        )

    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def get_all_users(self, limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[User]:
        return self.repository.get_all(limit=limit, offset=offset)

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.get_user(user_id)

        existing_user = self.repository.get_by_email(data.email)

        if existing_user and existing_user.id != user_id:
            raise ValueError("Email already registered")

        # Keep the current password unless a new one was supplied.
        hashed_password = (
            hash_password(data.password) if data.password else user.password_hash
        )

        return self.repository.update(
            user_id=user_id,
            email=data.email,
            password_hash=hashed_password,
            role=data.role,
        )

    def delete_user(self, user_id: int) -> None:
        self.repository.delete(user_id)
