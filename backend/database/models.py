"""
Resumen del módulo:
- Modelos SQLAlchemy: `User`, `Product`, `Review`, `AnalysisResult`.
- Relaciones:
  - `Product` 1:N `Review` y 1:N `AnalysisResult`.
  - `User` 1:N `AnalysisResult`.
- Patrón: timestamps `created_at`/`updated_at`, idempotencia por URL en `Product`.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db_config import Base
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    analyses = relationship("AnalysisResult", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    image_url = Column(Text)
    price = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="product", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_name = Column(String(255))
    rating = Column(Float, nullable=False)
    text = Column(Text)
    review_date = Column(DateTime)
    platform = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    product = relationship("Product", back_populates="reviews")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    avg_sentiment = Column(Float, nullable=False)
    sentiment_label = Column(String(20))
    total_reviews = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    keywords = Column(JSON)
    price_data = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    product = relationship("Product", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
