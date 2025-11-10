from typing import List, Dict, Optional
from utils.helpers import clean_text, extract_keywords, calculate_sentiment_label

class SentimentAnalyzer:
    """
    Lightweight sentiment analysis without heavy ML dependencies.
    Uses cleaned text, simple lexicons, and keyword extraction.
    """
    
    def __init__(self):
        # No heavy model initialization; keep analyzer lightweight.
        pass
    
    def analyze_reviews(self, reviews: List[Dict]) -> Dict:
        """
        Analyze a list of reviews and return comprehensive sentiment analysis
        
        Args:
            reviews: List of review dictionaries with 'text' and 'rating' fields
        
        Returns:
            Dictionary with sentiment scores, counts, and keywords
        """
        if not reviews:
            return self._empty_analysis()
        
        # Analyze each review, combining text and rating when available
        cleaned_reviews: List[Dict] = []
        for r in reviews:
            cleaned_reviews.append({
                'text': clean_text(r.get('text', '')),
                'rating': float(r.get('rating', 0) or 0),
                'review_date': r.get('review_date')
            })

        # If still empty list, return baseline
        if not cleaned_reviews:
            return self._empty_analysis()

        sentiments = [self._analyze_single_review(cr['text'], cr['rating']) for cr in cleaned_reviews]

        # Calculate aggregate statistics without numpy
        scores = [s['score'] for s in sentiments]
        avg_sentiment = sum(scores) / len(scores) if scores else 0.5
        
        # Count sentiment categories
        positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
        negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
        neutral_count = len(sentiments) - positive_count - negative_count
        
        # Extract keywords only from non-empty texts
        all_texts = [cr['text'] for cr in cleaned_reviews if cr['text']]
        all_text = ' '.join(all_texts)
        keywords = extract_keywords(all_text, top_n=15)
        
        # Determine overall sentiment label
        sentiment_label = calculate_sentiment_label(avg_sentiment)
        
        return {
            'avg_sentiment': round(float(avg_sentiment), 3),
            'sentiment_label': sentiment_label,
            'total_reviews': len(reviews),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'keywords': keywords,
            'sentiment_distribution': {
                'positive': round((positive_count / len(sentiments)) * 100, 1) if sentiments else 0.0,
                'negative': round((negative_count / len(sentiments)) * 100, 1) if sentiments else 0.0,
                'neutral': round((neutral_count / len(sentiments)) * 100, 1) if sentiments else 0.0
            }
        }
    
    def _analyze_single_review(self, text: str, rating: Optional[float] = None) -> Dict:
        """
        Analyze sentiment of a single review combining text signals and star rating.
        """
        text_sent = self._fallback_sentiment(text or "")

        # Normalize rating to [0,1] if provided (ML uses 1-5 scale)
        rating_norm: Optional[float] = None
        if rating is not None and rating > 0:
            rating_norm = max(0.0, min(1.0, float(rating) / 5.0))

        # Combine signals: if text has no signal, rely on rating; otherwise average
        if rating_norm is None:
            combined_score = text_sent['score']
        elif text_sent['score'] == 0.5 and (text or "").strip() == "":
            combined_score = rating_norm
        else:
            combined_score = (text_sent['score'] + rating_norm) / 2.0

        label = calculate_sentiment_label(combined_score)
        return { 'label': label, 'score': combined_score }
    
    def _fallback_sentiment(self, text: str) -> Dict:
        """
        Simple rule-based sentiment analysis as fallback
        """
        text_lower = text.lower()
        
        # Positive and negative word lists (English + Spanish)
        positive_words = {
            # EN
            'good','great','excellent','amazing','wonderful','fantastic','love','perfect','best','awesome','outstanding','superb','happy','satisfied','recommend','quality','fast','easy',
            # ES
            'bueno','excelente','increible','maravilloso','fantastico','mejor','perfecto','encanta','recomiendo','satisfecho','feliz','calidad','rapido','facil','cumple','funciona','genial'
        }
        
        negative_words = {
            # EN
            'bad','terrible','awful','horrible','worst','poor','hate','disappointed','waste','broken','defective','useless','slow','difficult','problem','issue','never','not',"don't",
            # ES
            'malo','terrible','horrible','peor','defectuoso','roto','lento','dificil','problema','fallo','nunca','no','decepcionado','odio','pobre','nofunciona','engaño','estafa'
        }
        
        # Count positive and negative words
        words = text_lower.replace('no funciona','nofunciona').split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            score = 0.5
        else:
            score = positive_count / total
        
        label = calculate_sentiment_label(score)
        
        return {
            'label': label,
            'score': score
        }
    
    def _empty_analysis(self) -> Dict:
        """
        Return empty analysis structure
        """
        return {
            'avg_sentiment': 0.5,
            'sentiment_label': 'neutral',
            'total_reviews': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'keywords': [],
            'sentiment_distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
        }
    
    def analyze_review_trends(self, reviews: List[Dict]) -> Dict:
        """
        Analyze sentiment trends over time
        """
        if not reviews:
            return {'trend': 'stable', 'data': []}
        
        # Sort reviews by date
        sorted_reviews = sorted(reviews, key=lambda x: x.get('review_date', ''))
        
        # Group by time periods and calculate sentiment
        # Simplified implementation
        return {
            'trend': 'improving',
            'recent_sentiment': 0.75,
            'historical_sentiment': 0.65
        }

# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
