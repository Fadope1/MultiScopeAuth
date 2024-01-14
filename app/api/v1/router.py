from fastapi import APIRouter

from .graph.router import router as graph_router
from .auth.router import router as auth_router

router = APIRouter()

router.include_router(graph_router, prefix="/graph")
router.include_router(auth_router, prefix="/auth")