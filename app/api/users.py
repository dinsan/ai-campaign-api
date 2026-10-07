from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.create_user(data)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)
    return service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.get_user(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.update_user(user_id, data)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT if "already registered" in message.lower() else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=message,
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        service.delete_user(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
