from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from database.db_config import get_db, SessionLocal
from database.models import Product, AnalysisResult
from services.analysis_service import analysis_service
from utils.api_key import require_internal_api_key
from utils.rate_limit import rate_limit
from utils.logging import get_logger
import re
from urllib.parse import urlparse
import os
import requests
import time

router = APIRouter()
"""
Resumen del módulo:
- Router de análisis que orquesta scraping y análisis de sentimiento.
- Patrón: tareas en segundo plano + inyección de dependencias (DB, rate limit, API Key).
- Métricas y logging JSON integrados para observabilidad.
"""
logger = get_logger("routes.analysis")

class AnalysisRequest(BaseModel):
    product_url: str
    platform: Optional[str] = "mercadolibre"

class AnalysisResponse(BaseModel):
    id: int
    product_id: int
    product_name: str  # Added product name to response
    product_price: Optional[float] = None
    product_image_url: Optional[str] = None
    product_rating: Optional[float] = None
    avg_sentiment: float
    sentiment_label: str
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    keywords: List[str]
    price_data: Optional[Dict] = None
    analyzed_at: datetime
    
    class Config:
        from_attributes = True

async def run_analysis_task(product_id: int):
    """Background task to run analysis with a fresh DB session"""
    db = SessionLocal()
    started_at = time.time()
    try:
        result = await analysis_service.analyze_product_complete(product_id, db)
        # Optional callback to Java orchestrator
        callback_url = os.getenv("JAVA_CALLBACK_URL")
        if callback_url:
            try:
                headers = {"Content-Type": "application/json"}
                api_key = os.getenv("INTERNAL_API_KEY")
                if api_key:
                    headers["X-API-Key"] = api_key
                requests.post(callback_url, json=result, headers=headers, timeout=10)
                logger.info({"event": "analysis_callback_sent", "product_id": product_id, "analysis_id": result.get("analysis_id")})
            except Exception as e:
                logger.error({"event": "analysis_callback_error", "product_id": product_id, "error": str(e)})
    except Exception as e:
        logger.error({"event": "analysis_task_error", "product_id": product_id, "error": str(e)})
    finally:
        try:
            db.close()
        except Exception:
            pass

# Helpers de nombre mostrable
def _derive_name_from_url(url: str | None) -> str:
    """Deriva un nombre legible desde una URL de Mercado Libre.

    Reglas:
    - Si la ruta es "/<slug>/p/<ITEM_ID>", usa el segmento `<slug>`.
    - Limpia frases comunes al final del slug (p.ej. "distribuidor-autorizado").
    - Si no coincide, intenta capturar un slug posterior a un ID en la ruta.
    - Fallback final: último segmento de la ruta.
    """
    if not url:
        return "Unknown Product"
    try:
        path = (urlparse(url).path or "").strip("/")
        segments = [s for s in path.split("/") if s]
        slug = None
        if segments:
            # Caso típico: /<slug>/p/<ITEM_ID>
            if "p" in segments:
                idx = segments.index("p")
                if idx > 0:
                    slug = segments[idx - 1]
            # Si no, intenta regex tras un ID
            if not slug:
                m = re.search(r"/[A-Z]{3}-\d{6,}-([\w-]+)", url, re.IGNORECASE)
                if m:
                    slug = m.group(1)
            # Fallback: primer segmento
            if not slug:
                slug = segments[0]

        if not slug:
            return "Unknown Product"

        # Limpieza de frases comunes al final
        cleanup_phrases = [
            "distribuidor-autorizado",
            "tienda-oficial",
            "envio-gratis",
            "nuevo",
            "original",
            "importado",
        ]
        for phrase in cleanup_phrases:
            if slug.endswith("-" + phrase):
                slug = slug[: -len("-" + phrase)]
                break

        pretty = slug.replace("-", " ").strip()
        return pretty.title() if pretty else "Unknown Product"
    except Exception:
        return "Unknown Product"

def _display_name(p: Product | None) -> str:
    """Nombre robusto para el frontend: evita 'Analyzing...'/'Unknown'."""
    invalid = {None, "", "Unknown", "Unknown Product", "Undefined", "Analyzing..."}
    if p and (p.name not in invalid):
        return p.name
    return _derive_name_from_url(p.url if p else None)

@router.post("/analyze", dependencies=[Depends(require_internal_api_key), Depends(rate_limit)])
async def analyze_product(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start product analysis process:
    1. Create or get product
    2. Scrape reviews (background task)
    3. Perform sentiment analysis (background task)
    4. Store results
    """
    # Check if product exists
    product = db.query(Product).filter(Product.url == request.product_url).first()
    
    if not product:
        # Create new product
        product = Product(
            name="Analyzing...",
            platform=request.platform,
            url=request.product_url
        )
        db.add(product)
        db.commit()
        db.refresh(product)
    
    # Add background task for analysis
    background_tasks.add_task(run_analysis_task, product.id)
    
    resp = {
        "status": "processing",
        "message": "Analysis started",
        "product_id": product.id,
        "product_url": request.product_url,
        "platform": request.platform
    }
    logger.info({"event": "analysis_started", "product_id": product.id, "platform": request.platform})
    return resp

@router.get("/{product_id}", response_model=AnalysisResponse)
async def get_analysis(product_id: int, db: Session = Depends(get_db)):
    """
    Get the latest analysis results for a specific product
    """
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.product_id == product_id
    ).order_by(AnalysisResult.analyzed_at.desc()).first()
    
    product = db.query(Product).filter(Product.id == product_id).first()

    # Helpers moved to module scope: _display_name

    if not analysis:
        # No analysis yet: return processing status instead of 404
        return {
            "id": 0,
            "product_id": product_id,
            "product_name": _display_name(product),
            "product_price": (product.price if product and hasattr(product, 'price') else None),
            "product_image_url": (product.image_url if product and hasattr(product, 'image_url') else None),
            "product_rating": (product.rating if product and hasattr(product, 'rating') else None),
            "avg_sentiment": 0.0,
            "sentiment_label": "processing",
            "total_reviews": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "keywords": [],
            "price_data": None,
            "analyzed_at": datetime.utcnow()
        }

    return {
        "id": analysis.id,
        "product_id": analysis.product_id,
        "product_name": _display_name(product),
        "product_price": (product.price if product and hasattr(product, 'price') else None),
        "product_image_url": (product.image_url if product and hasattr(product, 'image_url') else None),
        "product_rating": (product.rating if product and hasattr(product, 'rating') else None),
        "avg_sentiment": analysis.avg_sentiment,
        "sentiment_label": analysis.sentiment_label,
        "total_reviews": analysis.total_reviews,
        "positive_count": analysis.positive_count,
        "negative_count": analysis.negative_count,
        "neutral_count": analysis.neutral_count,
        "keywords": analysis.keywords,
        "price_data": analysis.price_data,
        "analyzed_at": analysis.analyzed_at
    }

@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    List all analysis results
    """
    analyses = db.query(AnalysisResult).join(Product).order_by(
        AnalysisResult.analyzed_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for analysis in analyses:
        product = db.query(Product).filter(Product.id == analysis.product_id).first()
        result.append({
            "id": analysis.id,
            "product_id": analysis.product_id,
            "product_name": _display_name(product),
            "product_price": (product.price if product and hasattr(product, 'price') else None),
            "product_image_url": (product.image_url if product and hasattr(product, 'image_url') else None),
            "product_rating": (product.rating if product and hasattr(product, 'rating') else None),
            "avg_sentiment": analysis.avg_sentiment,
            "sentiment_label": analysis.sentiment_label,
            "total_reviews": analysis.total_reviews,
            "positive_count": analysis.positive_count,
            "negative_count": analysis.negative_count,
            "neutral_count": analysis.neutral_count,
            "keywords": analysis.keywords,
            "price_data": analysis.price_data,
            "analyzed_at": analysis.analyzed_at
        })
    
    return result

@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific analysis
    """
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    
    return {"status": "success", "message": "Analysis deleted"}

@router.delete("/")
async def clear_all_analyses(db: Session = Depends(get_db)):
    """
    Clear all analysis history
    """
    db.query(AnalysisResult).delete()
    db.commit()
    
    return {"status": "success", "message": "All analyses cleared"}
