from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from database.db_config import get_db
from database.models import Product, AnalysisResult
from services.analysis_service import analysis_service

router = APIRouter()

class AnalysisRequest(BaseModel):
    product_url: str
    platform: Optional[str] = "amazon"

class AnalysisResponse(BaseModel):
    id: int
    product_id: int
    product_name: str  # Added product name to response
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

async def run_analysis_task(product_id: int, db: Session):
    """Background task to run analysis"""
    try:
        await analysis_service.analyze_product_complete(product_id, db)
    except Exception as e:
        print(f"Error in analysis task: {e}")

@router.post("/analyze")
async def analyze_product(
    request: AnalysisRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
    background_tasks.add_task(run_analysis_task, product.id, db)
    
    return {
        "status": "processing",
        "message": "Analysis started",
        "product_id": product.id,
        "product_url": request.product_url,
        "platform": request.platform
    }

@router.get("/{product_id}", response_model=AnalysisResponse)
async def get_analysis(product_id: int, db: Session = Depends(get_db)):
    """
    Get the latest analysis results for a specific product
    """
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.product_id == product_id
    ).order_by(AnalysisResult.analyzed_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this product")
    
    # Add product name to response
    product = db.query(Product).filter(Product.id == product_id).first()
    analysis_dict = {
        "id": analysis.id,
        "product_id": analysis.product_id,
        "product_name": product.name if product else "Unknown",
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
    
    return analysis_dict

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
            "product_name": product.name if product else "Unknown",
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
