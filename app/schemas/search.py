from pydantic import BaseModel, ConfigDict


class SearchCategorySummary(BaseModel):
    """Category details embedded in a matched product."""

    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class SearchProductSummary(BaseModel):
    """Product details embedded in a matched category."""

    id: int
    name: str
    description: str | None
    website: str | None

    model_config = ConfigDict(from_attributes=True)


class SearchProductResult(BaseModel):
    id: int
    name: str
    description: str | None
    website: str | None
    category: SearchCategorySummary | None

    model_config = ConfigDict(from_attributes=True)


class SearchCategoryResult(BaseModel):
    id: int
    name: str
    description: str | None
    products: list[SearchProductSummary]

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    query: str
    products: list[SearchProductResult]
    categories: list[SearchCategoryResult]

    model_config = ConfigDict(from_attributes=True)
