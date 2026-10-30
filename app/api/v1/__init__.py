"""Version 1 of the public API.

Every route module in this package is mounted under ``/api/v1``. To introduce
breaking changes later, add a sibling ``v2`` package with its own aggregate
router and mount it next to this one in ``app.main``; v1 keeps working for
existing clients.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.products import router as products_router
from app.api.v1.search import router as search_router
from app.api.v1.users import router as users_router

VERSION = "v1"

router = APIRouter(prefix=f"/{VERSION}")

router.include_router(users_router)
router.include_router(auth_router)
router.include_router(products_router)
router.include_router(categories_router)
router.include_router(search_router)
