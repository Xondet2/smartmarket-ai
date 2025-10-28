from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database.db_config import get_db
from database.models import Review, Product

router = APIRouter()

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
    Get all reviews for a specific product
    """
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get reviews
    reviews = db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()
    total = db.query(Review).filter(Review.product_id == product_id).count()
    
    return {
        "reviews": reviews,
        "total": total
    }

@router.post("/", response_model=ReviewResponse)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    """
    Add a new review to the database
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
async def create_reviews_bulk(reviews: List[ReviewCreate], db: Session = Depends(get_db)):
    """
    Add multiple reviews at once (useful for scraping)
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
