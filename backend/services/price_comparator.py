"""
Resumen del módulo:
- Servicio de comparación de precios (placeholders/heurístico).
- Patrón: clase con métodos puros y una instancia singleton.
- Buenas prácticas: logging estructurado en errores.
"""
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import random
from utils.logging import get_logger

class PriceComparator:
    """
    Compara precios entre diferentes plataformas de e-commerce.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.logger = get_logger("services.price_comparator")
    
    def compare_prices(self, product_name: str, platforms: List[str] = None) -> Dict[str, float]:
        """
        Busca el producto en varias plataformas y compara precios.
        
        Args:
            product_name: Nombre del producto a buscar.
            platforms: Lista de plataformas a consultar (por defecto: todas soportadas).
        
        Returns:
            Diccionario con nombres de plataformas como claves y precios como valores.
        """
        if platforms is None:
            platforms = ['amazon', 'ebay', 'mercadolibre']
        
        prices = {}
        
        base_price = abs(hash(product_name) % 100) + 20  # Base price between 20-120
        
        for platform in platforms:
            try:
                price = self._search_platform(product_name, platform, base_price)
                if price:
                    prices[platform] = price
            except Exception as e:
                self.logger.error({"event": "price_compare_error", "platform": platform, "error": str(e)})
                continue
        
        return prices
    
    def _search_platform(self, product_name: str, platform: str, base_price: float) -> Optional[float]:
        """
        Busca el producto en una plataforma específica y devuelve un precio.
        """
        variations = {
            'amazon': random.uniform(0.95, 1.05),  # -5% to +5%
            'ebay': random.uniform(0.90, 1.10),    # -10% to +10%
            'mercadolibre': random.uniform(0.92, 1.08),  # -8% to +8%
            'walmart': random.uniform(0.93, 1.07)  # -7% to +7%
        }
        
        variation = variations.get(platform, 1.0)
        price = round(base_price * variation, 2)
        
        return price
    
    def get_best_deal(self, prices: Dict[str, float]) -> Dict:
        """
        Encuentra la mejor oferta a partir de la comparación de precios.
        
        Returns:
            Diccionario con plataforma, precio e información de ahorros.
        """
        if not prices:
            return None
        
        min_platform = min(prices, key=prices.get)
        min_price = prices[min_platform]
        max_price = max(prices.values())
        savings = max_price - min_price
        savings_percent = (savings / max_price) * 100 if max_price > 0 else 0
        
        return {
            'best_platform': min_platform,
            'best_price': min_price,
            'savings': round(savings, 2),
            'savings_percent': round(savings_percent, 2),
            'all_prices': prices
        }

# Instancia singleton
price_comparator = PriceComparator()
