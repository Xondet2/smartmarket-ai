"""
Resumen del módulo:
- Utilidades de texto: limpieza, extracción de palabras clave, etiquetado de sentimiento, formateo de precios.
- Patrón: funciones puras y reutilizables con tipado estático.
"""
from typing import List, Dict
import re
from datetime import datetime
from collections import Counter

def clean_text(text: str) -> str:
    """
    Limpia y normaliza texto para el análisis.
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extrae las palabras clave más comunes del texto.
    Implementación mejorada con mejor filtrado.
    """
    if not text:
        return []
    
    # Convert to lowercase and split
    words = text.lower().split()
    
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'from', 'about', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'also', 'its', 'my', 'your',
        'their', 'our', 'his', 'her', 'them', 'us', 'me', 'him', 'sample', 'placeholder',
        'content', 'text', 'review', 'example', 'mock'
    }
    
    word_freq = Counter()
    for word in words:
        # Remove punctuation
        word = re.sub(r'[^\w]', '', word)
        # Keep words longer than 3 chars and not in stop words
        if len(word) > 3 and word not in stop_words and word.isalpha():
            word_freq[word] += 1
    
    return [word for word, freq in word_freq.most_common(top_n)]

def calculate_sentiment_label(score: float) -> str:
    """
    Convierte un puntaje de sentimiento a una etiqueta.
    """
    if score >= 0.6:
        return 'positive'
    elif score <= 0.4:
        return 'negative'
    else:
        return 'neutral'

def format_price(price: float, currency: str = 'USD') -> str:
    """
    Formatea un precio con símbolo de moneda.
    """
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'MXN': '$',
        'BRL': 'R$'
    }
    
    symbol = symbols.get(currency, '$')
    return f"{symbol}{price:.2f}"
