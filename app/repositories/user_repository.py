from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import Role
from app.models.user import User
from app.repositories.pagination import DEFAULT_LIMIT


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        # Case-insensitive so accounts created before emails were normalised
        # (see ``normalize_email``) can still be found.
        statement = select(User).where(func.lower(User.email) == email.strip().lower())
        return self.db.scalar(statement)

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_all(self, limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[User]:
        statement = select(User).order_by(User.id).limit(limit).offset(offset)
        return list(self.db.scalars(statement))

    def create(self, email: str, password_hash: str, role: Role) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
        )

        self.db.add(user)
        self._commit_or_raise_duplicate()
        self.db.refresh(user)

        return user

    def update(
        self,
        user_id: int,
        email: str,
        password_hash: str,
        role: Role,
    ) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        user.email = email
        user.password_hash = password_hash
        user.role = role
        self._commit_or_raise_duplicate()
        self.db.refresh(user)

        return user

    def delete(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        self.db.delete(user)
        self.db.commit()

    def _commit_or_raise_duplicate(self) -> None:
        """Commit, turning a unique-constraint violation into a domain error.

        The service checks for duplicates first, but two concurrent requests
        can both pass that check; the database constraint is the final word.
        """
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Email already registered") from exc
