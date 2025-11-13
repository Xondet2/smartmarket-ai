"""
Resumen del módulo:
- Dependencia de API Key interna opcional para proteger endpoints sensibles.
- Patrón: lectura de `INTERNAL_API_KEY` desde entorno y validación via header.
"""
import os
from fastapi import Header, HTTPException


def require_internal_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    """
    Verificación opcional de API Key interna.
    - Si la variable `INTERNAL_API_KEY` está definida, se requiere vía header `X-API-Key`
      o `Authorization: ApiKey <key>`.
    - Si no está definida, se permite la solicitud (no-op).
    """
    required_key = os.getenv("INTERNAL_API_KEY")
    if not required_key:
        return  # no-op if not configured

    provided: str | None = None
    if x_api_key:
        provided = x_api_key.strip()
    elif authorization and authorization.lower().startswith("apikey "):
        provided = authorization.split(" ", 1)[1].strip()

    if not provided or provided != required_key:
        raise HTTPException(status_code=403, detail={
            "message": "Invalid or missing internal API key",
            "error": "forbidden",
        })