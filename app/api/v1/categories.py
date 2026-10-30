from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.authorization import Permission
from app.core.dependencies import require_permissions
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.category_service import CategoryService


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def _status_code_for(exc: ValueError) -> int:
    if "already exists" in str(exc).lower():
        return status.HTTP_409_CONFLICT
    return status.HTTP_404_NOT_FOUND


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.CATEGORIES_WRITE)),
):
    service = CategoryService(CategoryRepository(db))
    try:
        return service.create_category(current_user.id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.CATEGORIES_READ)),
):
    service = CategoryService(CategoryRepository(db))
    return service.list_categories(current_user.id, limit=limit, offset=offset)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.CATEGORIES_READ)),
):
    service = CategoryService(CategoryRepository(db))
    try:
        return service.get_category(category_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.CATEGORIES_WRITE)),
):
    service = CategoryService(CategoryRepository(db))
    try:
        return service.update_category(category_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=_status_code_for(exc),
            detail=str(exc),
        ) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.CATEGORIES_WRITE)),
):
    service = CategoryService(CategoryRepository(db))
    try:
        service.delete_category(category_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
