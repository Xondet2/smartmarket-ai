from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import products, reviews, analysis, auth, meli_oauth
from database.db_config import init_db, engine
import os
from dotenv import load_dotenv
from sqlalchemy import inspect

load_dotenv()

app = FastAPI(
    title="SmartMarket AI API",
    description="API for product analysis with AI-powered sentiment analysis",
    version="1.0.0"
)

# Get allowed origins from environment variable or use defaults
# Normalize by trimming spaces and removing empty entries
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

# Optional: allow origins via regex (useful for Vercel previews like https://*.vercel.app)
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", None)

# Debug prints to verify CORS configuration on startup
print("🔐 CORS configured with:")
print(f"   allow_origins: {allowed_origins}")
print(f"   allow_origin_regex: {allowed_origin_regex}")

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
    print("🚀 Starting SmartMarket AI API...")
    init_db()
    print("✅ Database initialized")
    print("📍 Server running at http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(meli_oauth.router, prefix="/api/auth", tags=["meli-auth"])

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
    """Check database connection and tables"""
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