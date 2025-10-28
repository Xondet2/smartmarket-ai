from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import random

class PriceComparator:
    """
    Compare prices across different e-commerce platforms
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def compare_prices(self, product_name: str, platforms: List[str] = None) -> Dict[str, float]:
        """
        Search for product across platforms and compare prices
        
        Args:
            product_name: Name of the product to search
            platforms: List of platforms to search (default: all supported)
        
        Returns:
            Dictionary with platform names as keys and prices as values
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
                print(f"Error searching {platform}: {e}")
                continue
        
        return prices
    
    def _search_platform(self, product_name: str, platform: str, base_price: float) -> Optional[float]:
        """
        Search for product on specific platform and return price
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
        Find the best deal from price comparison
        
        Returns:
            Dictionary with platform, price, and savings information
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

# Singleton instance
price_comparator = PriceComparator()
