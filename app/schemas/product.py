from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    website: HttpUrl | None = None
    category_id: int | None = None


class ProductResponse(BaseModel):
    id: int
    owner_id: int
    category_id: int | None
    name: str
    description: str | None
    website: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
