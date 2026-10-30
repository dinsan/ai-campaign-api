from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.authorization import Permission
from app.core.dependencies import require_permissions
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    # Creating users and changing roles is reserved for administrators.
    dependencies=[Depends(require_permissions(Permission.USERS_MANAGE))],
)

manage_users = require_permissions(Permission.USERS_MANAGE)


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
        ) from exc


@router.get("", response_model=list[UserResponse])
def list_users(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    service = UserService(repository)
    return service.get_all_users(limit=limit, offset=offset)


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
        ) from exc


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(manage_users),
):
    # An administrator demoting themself could leave the system without
    # anyone able to manage users. Another administrator must do it.
    if user_id == current_user.id and data.role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

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
        ) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(manage_users),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    repository = UserRepository(db)
    service = UserService(repository)

    try:
        service.delete_user(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
