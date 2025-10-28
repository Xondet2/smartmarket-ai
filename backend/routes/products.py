from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database.db_config import get_db
from database.models import Product
from datetime import datetime
from services.scraper import scraper

router = APIRouter()

class ProductRequest(BaseModel):
    url: str
    platform: Optional[str] = "amazon"
    name: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    platform: str
    url: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/search", response_model=List[dict])
async def search_products(
    product_name: str,
    platforms: Optional[List[str]] = None
):
    """
    Search for products by name across multiple platforms
    Returns comparison results from different stores
    """
    if not product_name or not product_name.strip():
        raise HTTPException(status_code=400, detail="Product name is required")
    
    try:
        results = scraper.search_product_by_name(product_name.strip(), platforms)
        
        if not results:
            raise HTTPException(status_code=404, detail="No products found")
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/", response_model=ProductResponse)
async def create_product(product: ProductRequest, db: Session = Depends(get_db)):
    """
    Create a new product entry for analysis
    """
    # Check if product already exists
    existing = db.query(Product).filter(Product.url == product.url).first()
    if existing:
        return existing
    
    # Create new product
    db_product = Product(
        name=product.name or "Unknown Product",
        platform=product.platform,
        url=product.url
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get product details by ID
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[ProductResponse])
async def list_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    List all analyzed products
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Delete a product and all its associated data
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
