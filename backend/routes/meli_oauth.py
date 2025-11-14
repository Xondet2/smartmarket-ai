"""
Resumen del módulo:
- OAuth con Mercado Libre usando PKCE: generación de URL, callback y canje de tokens.
- Patrón: almacenamiento efímero `state -> verifier` y validación de expiración.
"""
from fastapi import APIRouter, HTTPException
import os
import secrets
import urllib.parse
import requests
import hashlib
import base64
import time

router = APIRouter()

# Configuración de entorno
MELI_CLIENT_ID = os.getenv("MELI_CLIENT_ID")
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET")
MELI_REDIRECT_URI = os.getenv("MELI_REDIRECT_URI")

# Permite sobrescribir para diferentes sitios (AR/MX/BR) si es necesario
AUTH_BASE = os.getenv("MELI_AUTH_BASE", "https://auth.mercadolibre.com/authorization")
TOKEN_URL = os.getenv("MELI_TOKEN_URL", "https://api.mercadolibre.com/oauth/token")

# Almacenamiento efímero PKCE (state -> code_verifier)
PKCE_STORE: dict[str, dict] = {}
PKCE_TTL_SECONDS = int(os.getenv("MELI_PKCE_TTL", "600"))  # 10 minutes default

def _generate_code_verifier(length: int = 64) -> str:
    """Genera un code_verifier PKCE (RFC 7636, 43-128 caracteres)."""
    verifier = secrets.token_urlsafe(length)
    # Garantiza longitud máxima de 128
    return verifier[:128]

def _code_challenge_s256(verifier: str) -> str:
    """Crea un code_challenge S256 desde el verifier (base64url sin padding)."""
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
    """Devuelve la URL de autorización OAuth de Mercado Libre para iniciar el flujo de login."""
    if not (MELI_CLIENT_ID and MELI_REDIRECT_URI):
        raise HTTPException(status_code=500, detail="MELI_CLIENT_ID and MELI_REDIRECT_URI must be set")

    state = secrets.token_urlsafe(16)
    # PKCE: crea code_verifier y challenge S256, guarda el verifier por state.
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
    """Gestiona el callback OAuth: canjea el código por tokens de acceso/refresh."""
    if not (MELI_CLIENT_ID and MELI_CLIENT_SECRET and MELI_REDIRECT_URI):
        raise HTTPException(status_code=500, detail="MELI_CLIENT_ID, MELI_CLIENT_SECRET and MELI_REDIRECT_URI must be set")

    if not state:
        raise HTTPException(status_code=400, detail="state is required")

    # Recupera el verifier PKCE para este state (y lo extrae para evitar reutilización).
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
    # persistir tokens vinculados al usuario/sesión actual si es necesario.
    return {"status": "ok", "token": token}


@router.post("/meli/refresh")
def meli_refresh(refresh_token: str | None = None):
    """Refresca el `access_token` de Mercado Libre usando un `refresh_token`.

    - Si no se proporciona `refresh_token`, intenta usar `MERCADO_LIBRE_REFRESH_TOKEN` del entorno.
    - Devuelve el JSON de tokens de ML. Además, actualiza variables de entorno del proceso
      (`MERCADO_LIBRE_ACCESS_TOKEN` y `MERCADO_LIBRE_REFRESH_TOKEN`) si están presentes en la respuesta.
    """
    if not (MELI_CLIENT_ID and MELI_CLIENT_SECRET):
        raise HTTPException(status_code=500, detail="MELI_CLIENT_ID and MELI_CLIENT_SECRET must be set")

    rt = refresh_token or os.getenv("MERCADO_LIBRE_REFRESH_TOKEN")
    if not rt:
        raise HTTPException(status_code=400, detail="refresh_token is required (or set MERCADO_LIBRE_REFRESH_TOKEN)")

    data = {
        "grant_type": "refresh_token",
        "client_id": MELI_CLIENT_ID,
        "client_secret": MELI_CLIENT_SECRET,
        "refresh_token": rt,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Refresh request failed: {e}")

    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = {"error": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=err)

    token = resp.json()
    # Actualiza variables de entorno del proceso para facilitar uso inmediato en servicios
    access_token = token.get("access_token")
    if access_token:
        os.environ["MERCADO_LIBRE_ACCESS_TOKEN"] = access_token
    new_refresh = token.get("refresh_token")
    if new_refresh:
        os.environ["MERCADO_LIBRE_REFRESH_TOKEN"] = new_refresh

    return {"status": "ok", "token": token}