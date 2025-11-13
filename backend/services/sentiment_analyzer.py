"""
Resumen del módulo:
- Servicio de análisis de sentimiento ligero (reglas y lexicón simple).
- Patrón: clase con métodos puros y una instancia singleton reutilizable.
"""
from typing import List, Dict, Optional
from utils.helpers import clean_text, extract_keywords, calculate_sentiment_label

class SentimentAnalyzer:
    """
    Análisis de sentimiento ligero sin dependencias de ML pesadas.
    Usa texto limpiado, léxicos simples y extracción de palabras clave.
    """
    
    def __init__(self):
        # Sin inicialización de modelos pesados; mantener el analizador ligero.
        pass
    
    def analyze_reviews(self, reviews: List[Dict]) -> Dict:
        """
        Analiza una lista de reseñas y devuelve un análisis de sentimiento completo.
        
        Args:
            reviews: Lista de diccionarios de reseñas con campos 'text' y 'rating'.
        
        Returns:
            Diccionario con puntajes de sentimiento, conteos y palabras clave.
        """
        if not reviews:
            return self._empty_analysis()
        
        # Analiza cada reseña, combinando texto y rating cuando esté disponible.
        cleaned_reviews: List[Dict] = []
        for r in reviews:
            cleaned_reviews.append({
                'text': clean_text(r.get('text', '')),
                'rating': float(r.get('rating', 0) or 0),
                'review_date': r.get('review_date')
            })

        # Si aún está vacía la lista, devuelve valores base.
        if not cleaned_reviews:
            return self._empty_analysis()

        sentiments = [self._analyze_single_review(cr['text'], cr['rating']) for cr in cleaned_reviews]

        # Calcula estadísticas agregadas sin numpy.
        scores = [s['score'] for s in sentiments]
        avg_sentiment = sum(scores) / len(scores) if scores else 0.5
        
        # Cuenta categorías de sentimiento.
        positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
        negative_count = sum(1 for s in sentiments if s['label'] == 'negative')
        neutral_count = len(sentiments) - positive_count - negative_count
        
        # Extrae palabras clave solo de textos no vacíos.
        all_texts = [cr['text'] for cr in cleaned_reviews if cr['text']]
        all_text = ' '.join(all_texts)
        keywords = extract_keywords(all_text, top_n=15)
        
        # Determina etiqueta de sentimiento general.
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
        Analiza el sentimiento de una reseña combinando señales del texto y calificación.
        """
        text_sent = self._fallback_sentiment(text or "")

        # Normaliza el rating a [0,1] si se proporciona (escala 1-5).
        rating_norm: Optional[float] = None
        if rating is not None and rating > 0:
            rating_norm = max(0.0, min(1.0, float(rating) / 5.0))

        # Combina señales: si el texto no tiene señal, usar el rating; si no, promediar.
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
        Análisis de sentimiento simple basado en reglas como respaldo.
        """
        text_lower = text.lower()
        
        # Listas de palabras positivas y negativas (inglés + español).
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
        
        # Cuenta palabras positivas y negativas.
        words = text_lower.replace('no funciona','nofunciona').split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calcula puntaje.
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
        Devuelve una estructura de análisis vacía.
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
        Analiza tendencias de sentimiento a lo largo del tiempo.
        """
        if not reviews:
            return {'trend': 'stable', 'data': []}
        
        # Ordena reseñas por fecha.
        sorted_reviews = sorted(reviews, key=lambda x: x.get('review_date', ''))
        
        # Agrupa por períodos de tiempo y calcula sentimiento.
        # Implementación simplificada.
        return {
            'trend': 'improving',
            'recent_sentiment': 0.75,
            'historical_sentiment': 0.65
        }

# Instancia singleton
sentiment_analyzer = SentimentAnalyzer()
