from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.authorization import Role

PASSWORD_MIN_LENGTH = 8
# Bounds the work done by the password hash on untrusted input.
PASSWORD_MAX_LENGTH = 128


def normalize_email(email: str) -> str:
    """Emails are compared case-insensitively, so store them in one form."""
    return email.strip().lower()


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: Role = Role.VIEWER

    @field_validator("email", mode="after")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class UserUpdate(BaseModel):
    """Full replacement of a user's profile.

    The password is optional so an administrator can change an email or role
    without having to know or reset the user's password.
    """

    email: EmailStr
    password: str | None = Field(
        default=None,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    role: Role

    @field_validator("email", mode="after")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
