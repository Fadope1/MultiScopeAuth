from fastapi import APIRouter

router = APIRouter()


@router.get("/info")
async def info():
    return {
        "owner": "Fabian"
    }


@router.get("/health")
async def health():
    return {
        "state": "operational"
    }