from typing import Annotated
import requests # Upgrade to httpx for performance

from fastapi import APIRouter, Header, Request

router = APIRouter()


async def me(token):
    """Get personal info using graph token"""
    url = "https://graph.microsoft.com/v1.0/me"
    token = token if token.startswith("Bearer") else f"Bearer {token}"
    headers = {
        "Authorization": token
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    return data


@router.get("/me")
async def get_me_from_token(request: Request, graph_token: Annotated[str | None, Header(alias="X-Graph-token")]=None):
    graph_token = request.state.session.get("https://graph.microsoft.com/.default", graph_token)

    return await me(graph_token)
