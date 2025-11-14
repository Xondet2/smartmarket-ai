"""
Resumen del módulo:
- Limitador de tasa en memoria por IP+ruta para FastAPI.
- Patrón: dependencia simple con `Request` inyectado automáticamente.
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict
from fastapi import Request, HTTPException


RATE_STATE: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=1000))


def _key_for_request(request: Request) -> str:
    client_ip = getattr(getattr(request, "client", None), "host", None) or "unknown"
    path = request.url.path if request and request.url else "unknown"
    return f"{client_ip}:{path}"


def rate_limit(request: Request, max_per_minute: int = 10) -> None:
    """
    Limitador de tasa en memoria por IP del cliente y ruta.
    No distribuido; adecuado para despliegues de un solo proceso.
    """
    key = _key_for_request(request)
    now = time.time()
    window_seconds = 60.0
    q = RATE_STATE[key]
    # purga entradas antiguas
    while q and (now - q[0]) > window_seconds:
        q.popleft()
    # verifica el límite
    if len(q) >= max_per_minute:
        raise HTTPException(status_code=429, detail={
            "message": "Rate limit exceeded",
            "error": "too_many_requests",
        })
    q.append(now)