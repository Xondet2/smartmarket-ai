from fastapi import APIRouter, HTTPException
import os
import secrets
import urllib.parse
import requests
import hashlib
import base64
import time

router = APIRouter()

# Environment configuration
MELI_CLIENT_ID = os.getenv("MELI_CLIENT_ID")
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET")
MELI_REDIRECT_URI = os.getenv("MELI_REDIRECT_URI")

# Allow overriding for different sites (AR/MX/BR) if needed
AUTH_BASE = os.getenv("MELI_AUTH_BASE", "https://auth.mercadolibre.com/authorization")
TOKEN_URL = os.getenv("MELI_TOKEN_URL", "https://api.mercadolibre.com/oauth/token")

# PKCE ephemeral store (state -> code_verifier)
PKCE_STORE: dict[str, dict] = {}
PKCE_TTL_SECONDS = int(os.getenv("MELI_PKCE_TTL", "600"))  # 10 minutes default

def _generate_code_verifier(length: int = 64) -> str:
    """Generate a PKCE code_verifier (RFC 7636, 43-128 chars)."""
    verifier = secrets.token_urlsafe(length)
    # Ensure max length 128
    return verifier[:128]

def _code_challenge_s256(verifier: str) -> str:
    """Create S256 code_challenge from verifier (base64url without padding)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

def _store_pkce_state(state: str, verifier: str) -> None:
    PKCE_STORE[state] = {"verifier": verifier, "ts": time.time()}

def _pop_pkce_verifier(state: str) -> str | None:
    item = PKCE_STORE.pop(state, None)
    if not item:
        return None
    if time.time() - item["ts"] > PKCE_TTL_SECONDS:
        return None
    return item["verifier"]


@router.get("/meli/login")
def meli_login():
    """Return Mercado Libre OAuth authorization URL to start login flow."""
    if not (MELI_CLIENT_ID and MELI_REDIRECT_URI):
        raise HTTPException(status_code=500, detail="MELI_CLIENT_ID and MELI_REDIRECT_URI must be set")

    state = secrets.token_urlsafe(16)
    # PKCE: create code_verifier and S256 challenge, store verifier by state
    code_verifier = _generate_code_verifier()
    code_challenge = _code_challenge_s256(code_verifier)
    _store_pkce_state(state, code_verifier)

    params = {
        "response_type": "code",
        "client_id": MELI_CLIENT_ID,
        "redirect_uri": MELI_REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTH_BASE}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url, "state": state}


@router.get("/meli/callback")
def meli_callback(code: str, state: str | None = None):
    """Handle OAuth callback: exchange code for access/refresh tokens."""
    if not (MELI_CLIENT_ID and MELI_CLIENT_SECRET and MELI_REDIRECT_URI):
        raise HTTPException(status_code=500, detail="MELI_CLIENT_ID, MELI_CLIENT_SECRET and MELI_REDIRECT_URI must be set")

    if not state:
        raise HTTPException(status_code=400, detail="state is required")

    # Retrieve PKCE verifier for this state (and pop to prevent reuse)
    code_verifier = _pop_pkce_verifier(state)
    if not code_verifier:
        raise HTTPException(status_code=400, detail={"message": "Invalid or expired state (PKCE)", "error": "invalid_request"})

    data = {
        "grant_type": "authorization_code",
        "client_id": MELI_CLIENT_ID,
        "client_secret": MELI_CLIENT_SECRET,
        "code": code,
        "redirect_uri": MELI_REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Token request failed: {e}")

    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = {"error": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=err)

    token = resp.json()
    # TODO: persist tokens tied to the current user/session if needed.
    return {"status": "ok", "token": token}