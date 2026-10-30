from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.authorization import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.VIEWER


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
