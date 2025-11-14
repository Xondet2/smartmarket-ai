"""
Resumen del módulo:
- Punto de entrada FastAPI: configura CORS, routers, salud, estado de BD y métricas.
- Patrón: inicialización en `startup`, observabilidad con logging JSON y Prometheus.
"""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from routes import products, reviews, analysis, auth, meli_oauth, scrape_practice
from database.db_config import init_db, engine
import os
from dotenv import load_dotenv
from sqlalchemy import inspect
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from utils.logging import get_logger

load_dotenv()

app = FastAPI(
    title="SmartMarket AI API",
    description="API for product analysis with AI-powered sentiment analysis",
    version="1.0.0"
)
logger = get_logger("main")

# Obtiene los orígenes permitidos desde la variable de entorno o usa valores por defecto.
# Normaliza recortando espacios y eliminando entradas vacías.
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:3001"
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

# Opcional: permitir orígenes vía regex (útil para previews de Vercel como https://*.vercel.app)
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", None)

logger.info({"event": "cors_configured", "allow_origins": allowed_origins, "allow_origin_regex": allowed_origin_regex})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info({"event": "startup", "message": "Starting SmartMarket AI API"})
    init_db()
    logger.info({"event": "db_initialized"})
    logger.info({"event": "server_info", "url": "http://localhost:8000", "docs": "http://localhost:8000/docs"})

# Inclusión de routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(meli_oauth.router, prefix="/api/auth", tags=["meli-auth"])
app.include_router(scrape_practice.router, prefix="/api", tags=["scrape-practice"])

@app.get("/")
def read_root():
    return {
        "message": "SmartMarket AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/db-status")
def db_status():
    """Verifica la conexión a la base de datos y sus tablas."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    return {
        "database_connected": True,
        "tables": tables,
        "user_table_exists": "users" in tables,
        "products_table_exists": "products" in tables,
        "reviews_table_exists": "reviews" in tables,
        "analysis_results_table_exists": "analysis_results" in tables
    }

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)