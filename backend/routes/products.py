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
    platform: Optional[str] = "mercadolibre"
    name: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    platform: str
    url: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/search", response_model=List[dict])
async def search_products(
    product_name: str,
    platforms: Optional[List[str]] = None
):
    """
    Búsqueda de productos por nombre.
    Actualmente no implementado para múltiples plataformas; se recomienda usar URL directa de Mercado Libre.
    """
    if not product_name or not product_name.strip():
        raise HTTPException(status_code=400, detail="Product name is required")
    
    # Deshabilitado: la búsqueda multi-plataforma fue retirada para centrarse en Mercado Libre.
    raise HTTPException(status_code=501, detail="Search by name is not implemented. Use Mercado Libre product URL.")

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
