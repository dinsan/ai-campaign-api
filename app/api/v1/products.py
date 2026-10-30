from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.authorization import Permission
from app.core.dependencies import require_permissions
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def _build_service(db: Session) -> ProductService:
    return ProductService(ProductRepository(db), CategoryRepository(db))


def _status_code_for(exc: ValueError) -> int:
    # A missing category is a problem with the request body, not the URL,
    # so it is reported as a bad request rather than a missing resource.
    if "category" in str(exc).lower():
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_404_NOT_FOUND


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
):
    service = _build_service(db)
    try:
        return service.create_product(current_user.id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=_status_code_for(exc),
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ProductResponse])
def list_products(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PRODUCTS_READ)),
):
    service = _build_service(db)
    return service.list_products(current_user.id, limit=limit, offset=offset)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PRODUCTS_READ)),
):
    service = _build_service(db)
    try:
        return service.get_product(product_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
):
    service = _build_service(db)
    try:
        return service.update_product(product_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=_status_code_for(exc),
            detail=str(exc),
        ) from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
):
    service = _build_service(db)
    try:
        service.delete_product(product_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
