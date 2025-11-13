from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database.db_config import get_db
from database.models import Review, Product
from utils.api_key import require_internal_api_key
from utils.rate_limit import rate_limit

router = APIRouter()
"""
Resumen del módulo:
- Router de reseñas: lectura y creación (simple y bulk).
- Patrón: FastAPI + Pydantic + SQLAlchemy, rate limit y API Key opcional.
- Idempotencia y validaciones básicas por existencia de producto.
"""

class ReviewCreate(BaseModel):
    product_id: int
    user_name: Optional[str] = "Anonymous"
    rating: float
    text: str
    review_date: Optional[datetime] = None
    platform: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_name: str
    rating: float
    text: str
    review_date: Optional[datetime]
    platform: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReviewsListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int

@router.get("/{product_id}", response_model=ReviewsListResponse)
async def get_reviews(product_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Obtiene todas las reseñas de un producto específico.
    """
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Obtener reseñas
    reviews = db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()
    total = db.query(Review).filter(Review.product_id == product_id).count()
    
    return {
        "reviews": reviews,
        "total": total
    }

@router.post("/", response_model=ReviewResponse)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db), _: None = Depends(require_internal_api_key)):
    """
    Agrega una nueva reseña a la base de datos.
    """
    # Check if product exists
    product = db.query(Product).filter(Product.id == review.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_review = Review(
        product_id=review.product_id,
        user_name=review.user_name,
        rating=review.rating,
        text=review.text,
        review_date=review.review_date or datetime.utcnow(),
        platform=review.platform or product.platform
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.post("/bulk")
async def create_reviews_bulk(reviews: List[ReviewCreate], db: Session = Depends(get_db), __: None = Depends(rate_limit), _: None = Depends(require_internal_api_key)):
    """
    Agrega múltiples reseñas de una vez (útil para scraping).
    """
    db_reviews = []
    for review in reviews:
        db_review = Review(
            product_id=review.product_id,
            user_name=review.user_name,
            rating=review.rating,
            text=review.text,
            review_date=review.review_date or datetime.utcnow(),
            platform=review.platform
        )
        db_reviews.append(db_review)
    
    db.add_all(db_reviews)
    db.commit()
    return {"message": f"Added {len(db_reviews)} reviews successfully"}
