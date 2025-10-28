from typing import Dict
from sqlalchemy.orm import Session
from database.models import Product, Review, AnalysisResult
from services.scraper import scraper
from services.sentiment_analyzer import sentiment_analyzer
from services.price_comparator import price_comparator
from datetime import datetime

class AnalysisService:
    """
    Orchestrates the complete product analysis workflow
    """
    
    async def analyze_product_complete(self, product_id: int, db: Session) -> Dict:
        """
        Complete analysis workflow:
        1. Get or scrape product info
        2. Scrape reviews
        3. Analyze sentiment
        4. Compare prices
        5. Save results
        """
        # Get product from database
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Step 1: Update product info if needed
        if product.name == "Analyzing..." or not product.name:
            product_info = scraper.scrape_product(product.url)
            product.name = product_info.get('name', 'Unknown Product')
            db.commit()
        
        # Step 2: Scrape reviews
        print(f"Scraping reviews for {product.name}...")
        scraped_reviews = scraper.scrape_reviews(product.url, max_reviews=50)
        
        # Save reviews to database
        for review_data in scraped_reviews:
            review = Review(
                product_id=product.id,
                user_name=review_data.get('user_name', 'Anonymous'),
                rating=review_data.get('rating', 3.0),
                text=review_data.get('text', ''),
                review_date=review_data.get('review_date', datetime.utcnow()),
                platform=review_data.get('platform', product.platform)
            )
            db.add(review)
        db.commit()
        
        # Step 3: Get all reviews for analysis
        all_reviews = db.query(Review).filter(Review.product_id == product.id).all()
        review_dicts = [
            {
                'text': r.text,
                'rating': r.rating,
                'date': r.review_date
            }
            for r in all_reviews
        ]
        
        # Step 4: Analyze sentiment
        print(f"Analyzing sentiment for {len(review_dicts)} reviews...")
        sentiment_results = sentiment_analyzer.analyze_reviews(review_dicts)
        
        # Step 5: Compare prices
        print(f"Comparing prices...")
        price_data = price_comparator.compare_prices(product.name)
        
        # Step 6: Save analysis results
        analysis = AnalysisResult(
            product_id=product.id,
            avg_sentiment=sentiment_results['avg_sentiment'],
            sentiment_label=sentiment_results['sentiment_label'],
            total_reviews=sentiment_results['total_reviews'],
            positive_count=sentiment_results['positive_count'],
            negative_count=sentiment_results['negative_count'],
            neutral_count=sentiment_results['neutral_count'],
            keywords=sentiment_results['keywords'],
            price_data=price_data,
            analyzed_at=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        print(f"Analysis complete for {product.name}")
        
        return {
            'product_id': product.id,
            'product_name': product.name,
            'analysis_id': analysis.id,
            'sentiment': sentiment_results,
            'prices': price_data,
            'status': 'completed'
        }

# Singleton instance
analysis_service = AnalysisService()
