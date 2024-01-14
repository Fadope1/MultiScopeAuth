from fastapi import APIRouter

from .oauth.router import router as oauth_router

router = APIRouter()

router.include_router(oauth_router, prefix="/oauth")