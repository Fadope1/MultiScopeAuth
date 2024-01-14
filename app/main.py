from dotenv import load_dotenv
load_dotenv("../.env")

import uuid

from fastapi import FastAPI, Request

app = FastAPI(
    title="Test multi scope api",
    debug=__debug__,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

session_store = {}


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Add basic user session to request"""
    # TODO: Add timed user_session
    # TODO: Add enrypted user_session
    # TODO: Add correct storage -> redis?
    session_id = request.cookies.get("session_id", None)
    if session_id not in session_store:
        session_id = str(uuid.uuid4())
        session_store[session_id] = {}

    request.state.session = session_store[session_id]

    response = await call_next(request)

    response.set_cookie(key="session_id", value=session_id)
    return response


from api.main import router as api_router
from frontend.main import router as frontend_router

app.include_router(api_router, prefix="/api")
app.include_router(frontend_router)
