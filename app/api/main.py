from fastapi import APIRouter

from .system.router import router as system_router
from .v1.router import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1", tags=["v1"])
router.include_router(system_router, prefix="/system", tags=["system"])