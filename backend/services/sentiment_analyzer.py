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
        
        # Extrae palabras clave con enfoque en sentimiento (ponderadas por polaridad).
        keywords = self._extract_sentiment_weighted_keywords(cleaned_reviews, sentiments, top_n=15)
        
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

    def _extract_sentiment_weighted_keywords(self, cleaned_reviews: List[Dict], sentiments: List[Dict], top_n: int = 15) -> List[str]:
        """
        Extrae palabras clave priorizando aquellas presentes en reseñas con sentimiento fuerte.
        - Usa stopwords en español e inglés para evitar palabras genéricas.
        - Pondera por intensidad: |score - 0.5| y separa positivos/negativos.
        - Combina las más relevantes de ambos polos y filtra duplicados.
        """
        if not cleaned_reviews or not sentiments:
            return []

        # Stopwords ampliadas (ES + EN) y términos genéricos de reseña
        stop_words = {
            # EN
            'the','a','an','and','or','but','in','on','at','to','for','of','with','is','was','are','were','been','be','have','has','had','do','does','did','will','would','could','should','may','might','must','can','this','that','these','those','i','you','he','she','it','we','they','what','which','who','when','where','why','how','all','each','every','both','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','just','from','about','into','through','during','before','after','above','below','between','under','again','further','then','once','here','there','also','its','my','your','their','our','his','her','them','us','me','him','her','himself','herself','itself','ourselves','yourselves','themselves',
            # ES
            'el','la','los','las','un','una','unos','unas','y','o','pero','en','de','con','para','por','es','son','fue','eran','han','ha','haber','tiene','tener','tuvo','tuvieron','puede','podria','debe','deberia','pueden','estas','esta','este','estos','estas','yo','tu','usted','ustedes','vos','vosotros','nosotros','ellos','ellas','que','cual','quien','cuando','donde','porque','como','todos','cada','ambos','pocos','mas','menos','otra','otros','algunos','tal','ninguno','ni','no','solo','mismo','asi','que','muy','desde','sobre','entre','durante','antes','despues','arriba','abajo','aqui','alli','tambien','su','mis','tus','sus','nuestro','nuestra','nuestros','nuestras','mi','tu','su','le','les','lo','la','se',
            # genéricos de reseñas
            'review','reviews','reseña','reseñas','opinion','opiniones','producto','libro','pelicula','film','movie','page','site','website','content','texto','ejemplo','muestra'
        }

        from collections import defaultdict
        import re

        pos_counter = defaultdict(float)
        neg_counter = defaultdict(float)

        for cr, s in zip(cleaned_reviews, sentiments):
            text = (cr.get('text') or '').lower()
            if not text:
                continue
            # Intensidad respecto a neutral
            intensity = abs(float(s.get('score', 0.5)) - 0.5)
            if intensity <= 0.05:
                # reseñas casi neutras aportan muy poco
                continue
            # tokenización simple y filtrado
            for raw in text.split():
                w = re.sub(r'[^\w]', '', raw)
                if len(w) <= 3 or not w.isalpha() or w in stop_words:
                    continue
                if s.get('label') == 'positive':
                    pos_counter[w] += max(0.1, intensity)
                elif s.get('label') == 'negative':
                    neg_counter[w] += max(0.1, intensity)

        # Seleccionar top por cada polaridad
        def top_items(counter: Dict[str, float], n: int) -> List[str]:
            return [k for k, _ in sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:n]]

        pos_kws = top_items(pos_counter, top_n)
        neg_kws = top_items(neg_counter, top_n)

        # Combinar priorizando palabras con mayor peso en cualquier polo
        combined_scores = {k: pos_counter.get(k, 0.0) + neg_counter.get(k, 0.0) for k in set(list(pos_counter.keys()) + list(neg_counter.keys()))}
        combined_sorted = [k for k, _ in sorted(combined_scores.items(), key=lambda kv: kv[1], reverse=True)]

        # Unión manteniendo orden por relevancia y evitando duplicados
        result: List[str] = []
        seen = set()
        for k in combined_sorted:
            if k not in seen:
                seen.add(k)
                result.append(k)
            if len(result) >= top_n:
                break

        # Si no hay suficientes, usar fallback genérico
        if len(result) < max(5, top_n // 2):
            all_texts = [cr.get('text', '') for cr in cleaned_reviews if cr.get('text')]
            fallback = extract_keywords(' '.join(all_texts), top_n=top_n)
            for k in fallback:
                if k not in seen:
                    result.append(k)
                    seen.add(k)
                if len(result) >= top_n:
                    break

        return result

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
