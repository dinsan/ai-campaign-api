from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.authorization import Permission
from app.core.dependencies import require_permissions
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.search import SearchResponse
from app.services.search_service import (
    DEFAULT_SEARCH_LIMIT,
    MAX_SEARCH_LIMIT,
    SearchService,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(
        min_length=1,
        max_length=255,
        description="Text to look for in product and category names",
    ),
    limit: int = Query(
        DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=MAX_SEARCH_LIMIT,
        description="Maximum number of products and of categories to return",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions(Permission.PRODUCTS_READ, Permission.CATEGORIES_READ)
    ),
):
    service = SearchService(ProductRepository(db), CategoryRepository(db))
    try:
        return service.search(current_user.id, q, limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
