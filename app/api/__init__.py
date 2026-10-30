"""HTTP layer. Each sub-package is one version of the API (``v1``, ``v2``...)."""
from fastapi import APIRouter

from app.api import v1

API_PREFIX = "/api"

# Versions currently served, oldest first.
VERSIONS = [v1.VERSION]

router = APIRouter(prefix=API_PREFIX)
router.include_router(v1.router)
