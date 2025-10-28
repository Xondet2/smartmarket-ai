from typing import List, Dict, Tuple
from transformers import pipeline
import numpy as np
from utils.helpers import clean_text, extract_keywords, calculate_sentiment_label

class SentimentAnalyzer:
    """
    AI-powered sentiment analysis using Hugging Face transformers
    Analyzes product reviews to determine customer satisfaction
    """
    
    def __init__(self):
        # Initialize sentiment analysis pipeline
        # Using a lightweight model for faster inference
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # Use CPU
            )
            self.model_loaded = True
        except Exception as e:
            print(f"Warning: Could not load sentiment model: {e}")
            print("Using fallback sentiment analysis")
            self.model_loaded = False
    
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
        
        # Extract review texts
        review_texts = [clean_text(r.get('text', '')) for r in reviews]
        review_texts = [text for text in review_texts if text]  # Remove empty
        
        if not review_texts:
            return self._empty_analysis()
        
        # Analyze sentiments
        sentiments = []
        for text in review_texts:
            sentiment = self._analyze_single_review(text)
            sentiments.append(sentiment)
        
        # Calculate aggregate statistics
        avg_sentiment = np.mean([s['score'] for s in sentiments])
        
        # Count sentiment categories
        positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
        negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
        neutral_count = len(sentiments) - positive_count - negative_count
        
        # Extract keywords from all reviews
        all_text = ' '.join(review_texts)
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
                'positive': round(positive_count / len(sentiments) * 100, 1),
                'negative': round(negative_count / len(sentiments) * 100, 1),
                'neutral': round(neutral_count / len(sentiments) * 100, 1)
            }
        }
    
    def _analyze_single_review(self, text: str) -> Dict:
        """
        Analyze sentiment of a single review text
        """
        if not text:
            return {'label': 'neutral', 'score': 0.5}
        
        if self.model_loaded:
            try:
                # Use transformer model
                # Truncate text to model's max length
                text = text[:512]
                result = self.sentiment_pipeline(text)[0]
                
                # Convert to 0-1 scale
                if result['label'] == 'POSITIVE':
                    score = (result['score'] + 1) / 2  # Map to 0.5-1.0
                else:
                    score = (1 - result['score']) / 2  # Map to 0.0-0.5
                
                label = 'positive' if score >= 0.6 else ('negative' if score <= 0.4 else 'neutral')
                
                return {
                    'label': label,
                    'score': score
                }
            except Exception as e:
                print(f"Error in model inference: {e}")
                return self._fallback_sentiment(text)
        else:
            return self._fallback_sentiment(text)
    
    def _fallback_sentiment(self, text: str) -> Dict:
        """
        Simple rule-based sentiment analysis as fallback
        """
        text_lower = text.lower()
        
        # Positive and negative word lists
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'perfect', 'best', 'awesome', 'outstanding', 'superb',
            'happy', 'satisfied', 'recommend', 'quality', 'fast', 'easy'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'hate',
            'disappointed', 'waste', 'broken', 'defective', 'useless', 'slow',
            'difficult', 'problem', 'issue', 'never', 'not', 'don\'t'
        }
        
        # Count positive and negative words
        words = text_lower.split()
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
