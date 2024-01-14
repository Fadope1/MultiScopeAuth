from typing import Annotated
import requests
import hashlib
import base64
import os

from fastapi import APIRouter, Header, Request, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

client_secret = os.getenv("CLIENT_SECRET")
client_id = os.getenv("CLIENT_ID")
tenant_id = os.getenv("TENANT_ID")
base_url = os.getenv("BASE_URL")
BASE_AUTH_URL = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0"

DEFAULT_SCOPE = "https://graph.microsoft.com/User.Read"
ADDITIONAL_SCOPES = "https://newmultiscopetest.blob.core.windows.net/user_impersonation"
ALL_SCOPES = DEFAULT_SCOPE + " " + ADDITIONAL_SCOPES


@router.get("/silent_login")
async def login(request: Request, scope: str=DEFAULT_SCOPE):
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    request.state.session['code_verifier'] = code_verifier
    request.state.session['scope'] = scope
    if "offline_access" not in scope:
        scope += " offline_access"

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": f"{base_url}/api/v1/auth/oauth/callback",
        "response_mode": "query",
        "scope": scope,
        "prompt": "none",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    login_url = f"{BASE_AUTH_URL}/authorize?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url=login_url)


@router.get("/login")
async def login(request: Request, scope: str=DEFAULT_SCOPE):
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    request.state.session['code_verifier'] = code_verifier
    request.state.session['scope'] = scope
    if "offline_access" not in scope:
        scope += " offline_access"

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": f"{base_url}/api/v1/auth/oauth/callback",
        "response_mode": "query",
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    login_url = f"{BASE_AUTH_URL}/authorize?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url=login_url)


@router.get("/consent")
async def login(request: Request, scope: str=ALL_SCOPES):
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    request.state.session['code_verifier'] = code_verifier
    request.state.session['scope'] = scope
    
    if "offline_access" not in scope:
        scope += " offline_access"

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": f"{base_url}/api/v1/auth/oauth/callback",
        "response_mode": "query",
        "scope": scope,
        "code_challenge": code_challenge,
        'prompt': 'consent',
        "code_challenge_method": "S256"
    }
    login_url = f"{BASE_AUTH_URL}/authorize?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url=login_url)


@router.get("/callback")
async def callback(
        request: Request,
        code: str | None=None,
        session_state: str | None=None,
        error: str=None,
        error_subcode: str=None,
        error_description: str=None
    ) -> RedirectResponse:
    if code is None:
        if error == "login_required":
            return RedirectResponse(url=f"{base_url}/api/v1/auth/oauth/login")
        elif error == "consent_required":
            return RedirectResponse(url=f"{base_url}/api/v1/auth/oauth/consent")
        else:
            raise HTTPException(500, f"{error}|{error_description}")
    
    code_verifier: str = request.state.session.get('code_verifier')
    scope: str = request.state.session['scope'].split(" ")[0]

    data = await get_token_by_code(scope, code, code_verifier)
    token = data['access_token']
    refresh_token = data['refresh_token']
    token_scopes = data['scope']

    request.state.session[scope] = token
    request.state.session['refresh_token'] = refresh_token

    missing_scopes = {scope for scope in ALL_SCOPES.split(" ") if scope not in token_scopes}
    for scope in missing_scopes:
        try:
            data = await get_token_by_refresh_token(scope, refresh_token)
            token = data["access_token"]
            request.state.session[scope] = token
        except Exception as e:
            print(e)
        
    request.state.session["scope"] = None

    return RedirectResponse(url=base_url)


if __debug__ is True and base_url.startswith("http://localhost"):
    @router.get("/session_key")
    async def get_token_from_session(request: Request, key):
        return request.state.session.get(key)


    @router.get("/session_keys")
    async def get_token_from_session(request: Request):
        return request.state.session


async def get_token_by_code(
        scope,
        code,
        code_verifier
    ) -> dict:
    """Acquire the token using refresh_token"""
    url = f"{BASE_AUTH_URL}/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
        "code": code,
        "redirect_uri": f"{base_url}/api/v1/auth/oauth/callback",
        "code_verifier": code_verifier
    }
    response = requests.post(url, data=payload)
    
    response.raise_for_status()
    data = response.json()

    return data


async def get_token_by_refresh_token(
        scope,
        refresh_token
    ) -> dict:
    """Acquire the token using refresh_token"""
    url = f"{BASE_AUTH_URL}/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "scope": scope
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    data = response.json()

    return data


@router.get("/acquire_token_silent")
async def aquire_token_silent(
        request: Request,
        scope: str,
        refresh_token: Annotated[str, Header(alias="X-Refresh-Token")]=None
    ) -> dict:
    """Acquire the token silent using refresh_token"""
    refresh_token = request.state.session.get("refresh_token", refresh_token)
    
    data = await get_token_by_refresh_token(scope, refresh_token)
    token = data["access_token"]
    request.state.session[scope] = token

    return data


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Logout the user."""
    del request.state.session
    logout_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout?post_logout_redirect_uri={base_url}"
    response = RedirectResponse(url=logout_url)
    
    return response
