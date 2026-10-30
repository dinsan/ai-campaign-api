from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SearchService(ProductRepository(db), CategoryRepository(db))
    try:
        return service.search(current_user.id, q)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
