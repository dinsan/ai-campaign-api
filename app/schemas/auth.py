from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import PASSWORD_MAX_LENGTH


class LoginRequest(BaseModel):
    email: EmailStr
    # Only the upper bound is enforced here so that accounts created before a
    # minimum length existed can still sign in.
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
