from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.authorization import Permission, has_permissions
from app.core.config import settings
from app.database.dependencies import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )

        user_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    repository = UserRepository(db)
    user = repository.get_by_id(user_id)

    if user is None:
        raise credentials_error

    return user

def require_permissions(*permissions: Permission) -> Callable[..., User]:
    """Build a dependency that only lets through users whose role grants
    every listed permission.

    Usage::

        @router.delete("/{product_id}")
        def delete_product(
            current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
        ): ...

    Authentication failures are still reported as 401 by ``get_current_user``;
    an authenticated user lacking the permission gets 403.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_permissions(current_user.role, *permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency
