from fastapi import APIRouter, Request, Response
# from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")  # Ensure you have a 'templates' directory


def check_authorization(request: Request) -> bool:
    return "https://graph.microsoft.com/User.Read" in request.state.session


@router.get("/")
async def home(request: Request, error: str | None=None) -> Response:
    if check_authorization(request) is True:
        return templates.TemplateResponse("home.html", {"request": request})
    else:
        return templates.TemplateResponse("unauthorized.html", {"request": request})