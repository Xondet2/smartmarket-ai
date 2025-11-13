from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.models import Product, Review, AnalysisResult
from services.scraper import scraper
from services.sentiment_analyzer import sentiment_analyzer
from utils.metrics import ANALYSIS_REQUESTS, ANALYSIS_DURATION, API_ERRORS
from utils.logging import get_logger
# Eliminamos comparación de precios para enfocarnos en opiniones
from datetime import datetime

class AnalysisService:
    async def analyze_product_complete(self, product_id: int, db: Session, user_id: Optional[int] = None) -> Dict:
        logger = get_logger("services.analysis_service")
        ANALYSIS_REQUESTS.inc()
        import time
        start_t = time.time()
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            API_ERRORS.labels(endpoint="analysis").inc()
            # Mensaje de error interno en inglés (los mensajes al usuario pueden permanecer localizados).
            raise ValueError(f"Product {product_id} not found")
        
        # Update product info with API/scraping
        product_info = scraper.scrape_product(product.url)
        # Actualizar nombre: preferir nombre válido del scraper, si no derivar del slug de la URL
        scraped_name = product_info.get('name')
        def derive_from_url(url: str) -> str:
            try:
                from urllib.parse import urlparse
                import re
                path = (urlparse(url).path or "").strip("/")
                segments = [s for s in path.split("/") if s]
                slug = None
                if segments:
                    if "p" in segments:
                        idx = segments.index("p")
                        if idx > 0:
                            slug = segments[idx - 1]
                    if not slug:
                        m = re.search(r"/[A-Z]{3}-\d{6,}-([\w-]+)", url, re.IGNORECASE)
                        if m:
                            slug = m.group(1)
                    if not slug:
                        slug = segments[0]
                cleanup_phrases = [
                    "distribuidor-autorizado",
                    "tienda-oficial",
                    "envio-gratis",
                    "nuevo",
                    "original",
                    "importado",
                ]
                if slug:
                    for phrase in cleanup_phrases:
                        if slug.endswith("-" + phrase):
                            slug = slug[: -len("-" + phrase)]
                            break
                    pretty = slug.replace('-', ' ').strip()
                    return pretty.title() if pretty else "Unknown Product"
            except Exception:
                pass
            return "Unknown Product"
        if scraped_name and str(scraped_name).strip().lower() not in {"unknown product", "unknown", "undefined"}:
            product.name = scraped_name
        else:
            product.name = derive_from_url(product.url)
        # Imagen: si no viene, intentar obtener desde la URL directa (OG/JSON-LD)
        image_candidate = product_info.get('image_url')
        if not image_candidate:
            try:
                alt = scraper._scrape_mercadolibre_html_by_url(product.url)
                image_candidate = alt.get('image_url')
            except Exception:
                image_candidate = None
        product.image_url = image_candidate or product.image_url
        # Guardar precio si viene del scraper
        if product_info.get('price') is not None:
            try:
                product.price = float(product_info.get('price'))
            except (TypeError, ValueError):
                pass
        # Guardar rating oficial si viene del scraper
        if product_info.get('rating') is not None:
            try:
                product.rating = float(product_info.get('rating'))
            except (TypeError, ValueError):
                pass
        db.commit()
        
        # Scraping de reseñas con prioridad de API
        scraped_reviews = scraper.scrape_reviews(product.url, max_reviews=50)
        
        # Guardar reseñas
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
        
        # Obtener todas las reseñas para el análisis
        all_reviews = db.query(Review).filter(Review.product_id == product.id).all()
        review_dicts = [
            {'text': r.text, 'rating': r.rating, 'review_date': r.review_date}
            for r in all_reviews
        ]
        
        # Sentiment analysis with IA
        sentiment_results = sentiment_analyzer.analyze_reviews(review_dicts)
        
        # Sin comparación de precios: mantenemos price_data como None
        price_data = None
        
        # Guardar análisis
        analysis = AnalysisResult(
            product_id=product.id,
            user_id=user_id,
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
        dur = time.time() - start_t
        ANALYSIS_DURATION.observe(dur)
        logger.info({"event": "analysis_completed", "product_id": product.id, "analysis_id": analysis.id, "duration_s": round(dur, 3)})
        
        return {
            'product_id': product.id,
            'product_name': product.name,
            'analysis_id': analysis.id,
            'sentiment': sentiment_results,
            # prices eliminado; mantenemos estructura centrada en sentimientos
            'status': 'completed'
        }

# Instancia singleton
analysis_service = AnalysisService()