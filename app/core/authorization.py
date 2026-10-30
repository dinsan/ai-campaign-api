"""Role-based authorization.

Authentication (``app.core.dependencies.get_current_user``) answers *who* the
caller is. This module answers *what they may do*: every user has exactly one
role, every role grants a fixed set of permissions, and each API route declares
the permissions it needs.

Roles are cumulative:

    viewer  -> read products and categories (and search them)
    editor  -> viewer + create / update / delete products and categories
    admin   -> editor + manage users and their roles
"""
from enum import Enum


class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class Permission(str, Enum):
    PRODUCTS_READ = "products:read"
    PRODUCTS_WRITE = "products:write"
    CATEGORIES_READ = "categories:read"
    CATEGORIES_WRITE = "categories:write"
    USERS_MANAGE = "users:manage"


_VIEWER_PERMISSIONS = frozenset(
    {
        Permission.PRODUCTS_READ,
        Permission.CATEGORIES_READ,
    }
)

_EDITOR_PERMISSIONS = _VIEWER_PERMISSIONS | frozenset(
    {
        Permission.PRODUCTS_WRITE,
        Permission.CATEGORIES_WRITE,
    }
)

_ADMIN_PERMISSIONS = _EDITOR_PERMISSIONS | frozenset(
    {
        Permission.USERS_MANAGE,
    }
)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: _VIEWER_PERMISSIONS,
    Role.EDITOR: _EDITOR_PERMISSIONS,
    Role.ADMIN: _ADMIN_PERMISSIONS,
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(Role(role), frozenset())


def has_permissions(role: Role, *permissions: Permission) -> bool:
    """True when the role grants every one of the given permissions."""
    return set(permissions).issubset(permissions_for(role))
