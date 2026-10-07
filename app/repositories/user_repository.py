from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self) -> list[User]:
        return self.db.query(User).all()

    def create(self, email: str, password_hash: str) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update(self, user_id: int, email: str, password_hash: str) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        user.email = email
        user.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user)

        return user

    def delete(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        self.db.delete(user)
        self.db.commit()
