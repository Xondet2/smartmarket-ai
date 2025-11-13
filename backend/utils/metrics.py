"""
Resumen del módulo:
- Métricas Prometheus: contadores e histogramas para análisis, scraping y errores.
- Patrón: definir métricas globales reutilizables por servicios y routers.
"""
from prometheus_client import Counter, Histogram


ANALYSIS_REQUESTS = Counter("analysis_requests_total", "Total analysis requests")
ANALYSIS_DURATION = Histogram("analysis_duration_seconds", "Analysis duration in seconds")

SCRAPE_REQUESTS = Counter("scrape_requests_total", "Total scrape requests")
SCRAPE_DURATION = Histogram("scrape_duration_seconds", "Scrape duration in seconds")

API_ERRORS = Counter("api_errors_total", "API errors", ["endpoint"])