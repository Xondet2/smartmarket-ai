import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import re
import time
import random
import os
from urllib.parse import urlparse, parse_qs
from utils.metrics import SCRAPE_REQUESTS, SCRAPE_DURATION, API_ERRORS
from utils.logging import get_logger
"""
NOTA: Este módulo ha sido simplificado para centrarse en la API oficial
de Mercado Libre. El scraping de otras plataformas (Amazon/eBay/AliExpress)
se ha comentado como referencia histórica y no se ejecuta.

Si más adelante se necesita compatibilidad multi-plataforma, se pueden
recuperar las secciones comentadas y añadir parsers específicos.
"""

class ProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.access_token = os.getenv('MERCADO_LIBRE_ACCESS_TOKEN')
        self.site_id = os.getenv('MERCADO_LIBRE_SITE_ID', 'MLA')
        # Modo estricto: usar solo la API oficial; no complementar con HTML
        self.strict_api = str(os.getenv('MELI_STRICT_API', 'false')).lower() in {"1", "true", "yes"}
        self.logger = get_logger("services.scraper")
        # Configuración OAuth ML para refresco
        self.meli_token_url = os.getenv("MELI_TOKEN_URL", "https://api.mercadolibre.com/oauth/token")
        self.meli_client_id = os.getenv("MELI_CLIENT_ID")
        self.meli_client_secret = os.getenv("MELI_CLIENT_SECRET")

    # ----------------------------
    # Helpers internos
    # ----------------------------
    def _request_get(self, url: str, headers: Optional[Dict] = None, timeout: int = 15, retries: int = 2) -> requests.Response:
        """GET con headers, timeout y reintentos simples con backoff.

        Si la respuesta es 401 desde la API de ML y hay `refresh_token`, intenta
        refrescar el access_token y reintenta una vez inmediatamente.
        """
        hdrs = {**self.headers, **(headers or {})}
        last_exc = None
        for attempt in range(retries + 1):
            try:
                SCRAPE_REQUESTS.inc()
                resp = requests.get(url, headers=hdrs, timeout=timeout)
                # Intento de refresco en 401 únicamente para dominio ML
                if resp.status_code == 401 and "api.mercadolibre.com" in url:
                    self.logger.warning({"event": "ml_unauthorized", "url": url})
                    if self._refresh_access_token_if_possible():
                        # Actualiza Authorization y reintenta de inmediato
                        if "Authorization" in hdrs:
                            hdrs["Authorization"] = f"Bearer {self.access_token}"
                        resp = requests.get(url, headers=hdrs, timeout=timeout)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                last_exc = e
                # Backoff con jitter
                sleep_s = 0.5 * (attempt + 1) + random.uniform(0, 0.5)
                time.sleep(sleep_s)
        # Si falla después de reintentos, relanza última excepción
        raise last_exc

    def _refresh_access_token_if_possible(self) -> bool:
        """Refresca el access_token de ML si hay configuración y refresh_token en entorno."""
        refresh_token = os.getenv("MERCADO_LIBRE_REFRESH_TOKEN")
        if not (self.meli_client_id and self.meli_client_secret and refresh_token):
            self.logger.error({
                "event": "ml_refresh_missing_config",
                "has_client_id": bool(self.meli_client_id),
                "has_client_secret": bool(self.meli_client_secret),
                "has_refresh_token": bool(refresh_token),
            })
            return False
        data = {
            "grant_type": "refresh_token",
            "client_id": self.meli_client_id,
            "client_secret": self.meli_client_secret,
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            resp = requests.post(self.meli_token_url, data=data, headers=headers, timeout=15)
        except requests.RequestException as e:
            self.logger.error({"event": "ml_refresh_failed", "error": str(e)})
            return False
        if resp.status_code >= 400:
            # Log detallado de error
            try:
                err = resp.json()
            except Exception:
                err = {"error": resp.text}
            self.logger.error({"event": "ml_refresh_http_error", "status": resp.status_code, "detail": err})
            return False
        token = resp.json()
        new_access = token.get("access_token")
        if new_access:
            self.access_token = new_access
            os.environ["MERCADO_LIBRE_ACCESS_TOKEN"] = new_access
        new_refresh = token.get("refresh_token")
        if new_refresh:
            os.environ["MERCADO_LIBRE_REFRESH_TOKEN"] = new_refresh
        self.logger.info({"event": "ml_token_refreshed"})
        return True

    def _normalize_image_url(self, url: Optional[str]) -> Optional[str]:
        """Normaliza URLs de imagen a https, manejando esquemas relativos."""
        if not url:
            return None
        u = str(url).strip()
        if u.startswith('//'):
            u = 'https:' + u
        if u.startswith('http://'):
            u = 'https://' + u[len('http://'):]
        return u

    def _extract_meli_item_id(self, url: str) -> Optional[str]:
        """Extrae el ID de Mercado Libre (e.g., MLA123456789, MCO2676566586).

        - Prefiere `wid` en query o fragmento (URLs agregadas `/p/...#...&wid=...`).
        - Si no existe, intenta capturar IDs en la ruta (`/p/MLA123456789`).
        - Finalmente, usa un regex general sobre toda la URL.
        """
        try:
            parsed = urlparse(url)
            # 1) Query params
            q = parse_qs(parsed.query)
            wid_q = (q.get('wid') or q.get('item_id') or [])
            if wid_q:
                return (wid_q[0] or '').upper() or None

            # 2) Fragment (algunas URLs de ML ponen wid en el hash)
            frag_q = parse_qs(parsed.fragment)
            wid_f = (frag_q.get('wid') or frag_q.get('item_id') or [])
            if wid_f:
                return (wid_f[0] or '').upper() or None

            # 3) Ruta con /p/<ID>
            m_path = re.search(r"/p/([A-Z]{3}-?\d{6,})", parsed.path, re.IGNORECASE)
            if m_path:
                return m_path.group(1).upper()

            # 4) Regex general
            m = re.search(r'([A-Z]{3}-?\d{6,})', url)
            return m.group(1).upper() if m else None
        except Exception:
            return None

    def _parse_date_iso(self, s: str) -> datetime:
        """Convierte fechas ISO con offsets tipo -0400 a -04:00 para compatibilidad."""
        if not s:
            return datetime.utcnow()
        # Reemplazar Z por +00:00
        s2 = s.replace('Z', '+00:00')
        # Normalizar offset final -0400 -> -04:00
        s2 = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', s2)
        try:
            return datetime.fromisoformat(s2)
        except Exception:
            return datetime.utcnow()
    
    def detect_platform(self, url: str) -> str:
        """Detecta la plataforma; actualmente solo se soporta Mercado Libre."""
        url = url.lower()
        if "mercadolibre" in url:
            return "mercadolibre"
        # Comentado: soporte para otras plataformas
        # elif "amazon" in url:
        #     return "amazon"
        # elif "ebay" in url:
        #     return "ebay"
        # elif "aliexpress" in url:
        #     return "aliexpress"
        else:
            return "unknown"

    # BÚSQUEDA POR NOMBRE (comentada): Multi-plataforma
    # def search_product_by_name(self, product_name: str, platforms: List[str] = None) -> List[Dict]:
    #     """Buscar productos por nombre en múltiples plataformas (no usado)."""
    #     # Implementación previa eliminada para centrarnos en Mercado Libre.
    #     # Se puede reintroducir con la API de búsqueda de ML u otras fuentes.
    #     return []

    # Nuevos métodos para API de Mercado Libre (robustos)
    
    def scrape_product_api(self, item_id: str) -> Dict:
        if not self.access_token:
            # Sin token, usar fallback HTML directo por item_id
            return self._scrape_mercadolibre_html(item_id)
        url = f"https://api.mercadolibre.com/items/{item_id}"
        headers = {**self.headers, 'Authorization': f'Bearer {self.access_token}'}
        try:
            t0 = time.time()
            response = self._request_get(url, headers=headers, timeout=15, retries=2)
            data = response.json()
            # Nombre robusto: si falta en la API, intentar HTML fallback
            api_name = data.get('title')
            # Solo complementar con HTML si NO estamos en modo estricto
            if ((not api_name) or (str(api_name).strip().lower() in {"unknown product", "unknown", "undefined"})) and (not self.strict_api):
                try:
                    html_fallback = self._scrape_mercadolibre_html(item_id)
                    api_name = html_fallback.get('name') or api_name
                except Exception:
                    pass

            res = {
                'name': api_name or 'Unknown Product',
                'price': data.get('price', None),
                'platform': 'mercadolibre',
                'url': data.get('permalink', ''),
                'image_url': self._normalize_image_url(
                    (data.get('thumbnail', '') or (data.get('pictures', [{}])[0].get('url', '') if data.get('pictures') else ''))
                ),
                'reviews_count': (data.get('reviews', {}) or {}).get('total', 0),
                'rating': (data.get('reviews', {}) or {}).get('rating_average', None),
            }
            SCRAPE_DURATION.observe(time.time() - t0)
            return res
        except requests.exceptions.RequestException as e:
            API_ERRORS.labels(endpoint="scrape_product_api").inc()
            self.logger.error({"event": "scrape_product_api_error", "item_id": item_id, "error": str(e)})
            return self._scrape_mercadolibre_html(item_id)  # Fallback HTML básico

    def scrape_reviews_api(self, item_id: str, max_reviews: int = 50) -> List[Dict]:
        if not self.access_token:
            # Sin token, intentar scrapear reseñas del HTML del artículo
            return self._scrape_mercadolibre_reviews(item_id, max_reviews)
        url = f"https://api.mercadolibre.com/reviews/item/{item_id}?limit={max_reviews}"
        headers = {**self.headers, 'Authorization': f'Bearer {self.access_token}'}
        try:
            t0 = time.time()
            response = self._request_get(url, headers=headers, timeout=15, retries=2)
            data = response.json()
            reviews = []
            for review in data.get('reviews', []):
                reviews.append({
                    'user_name': review.get('reviewer', {}).get('nickname', 'Anonymous'),
                    'rating': review.get('rate', 3.0),
                    'text': review.get('content', ''),
                    'review_date': self._parse_date_iso(review.get('date_created', datetime.utcnow().isoformat())),
                    'platform': 'mercadolibre'
                })
            time.sleep(random.uniform(1, 2))  # Delay para rate limit
            SCRAPE_DURATION.observe(time.time() - t0)
            return reviews
        except requests.exceptions.RequestException as e:
            API_ERRORS.labels(endpoint="scrape_reviews_api").inc()
            self.logger.error({"event": "scrape_reviews_api_error", "item_id": item_id, "error": str(e)})
            return self._scrape_mercadolibre_reviews(f"https://articulo.mercadolibre.com.ar/{item_id}", max_reviews)

    # ----------------------------
    # Fallback HTML Mercado Libre
    # ----------------------------
    def _scrape_mercadolibre_html(self, item_id: str) -> Dict:
        """Obtiene datos mínimos del HTML del artículo como fallback."""
        # Seleccionar dominio según prefijo de sitio del item_id
        prefix = (item_id[:3] or '').upper()
        tld_map = {
            'MLA': 'com.ar',
            'MLB': 'com.br',
            'MLM': 'com.mx',
            'MLC': 'cl',
            'MCO': 'com.co',
            'MLU': 'com.uy',
            'MLV': 'com.ve',
            'MPE': 'com.pe',
        }
        tld = tld_map.get(prefix, 'com.ar')
        article_url = f"https://articulo.mercadolibre.{tld}/{item_id}"
        try:
            resp = self._request_get(article_url, timeout=15, retries=1)
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            name = None
            image_url = None
            price = None
            # OpenGraph
            og_title = soup.find('meta', property='og:title')
            if og_title:
                name = og_title.get('content')
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = self._normalize_image_url(og_image.get('content'))
            # Twitter Card
            if not image_url:
                tw_img = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', property='twitter:image')
                if tw_img and tw_img.get('content'):
                    image_url = self._normalize_image_url(tw_img.get('content'))
            # JSON-LD Product
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string or '{}')
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        name = name or data.get('name')
                        offers = data.get('offers')
                        if isinstance(offers, dict):
                            price = price or float(offers.get('price', 0)) or None
                            image_url = image_url or (data.get('image') if isinstance(data.get('image'), str) else None)
                except Exception:
                    continue
            # Galería de imágenes en markup de ML (ui-pdp-image/srcset/data-zoom)
            if not image_url:
                def pick_best_from_srcset(srcset: str) -> Optional[str]:
                    try:
                        candidates = []
                        for part in (srcset or '').split(','):
                            part = part.strip()
                            if not part:
                                continue
                            bits = part.split()
                            url = bits[0]
                            descriptor = bits[1] if len(bits) > 1 else ''
                            score = 0
                            if '2x' in descriptor:
                                score = 2000
                            else:
                                m = re.search(r'(\d+)w', descriptor)
                                if m:
                                    score = int(m.group(1))
                            candidates.append((score, url))
                        if candidates:
                            candidates.sort(reverse=True)
                            return candidates[0][1]
                    except Exception:
                        return None
                for img in soup.select('img.ui-pdp-image, img.ui-pdp-gallery__figure__image, img[src*="mlstatic.com"]'):
                    try:
                        zoom = img.get('data-zoom')
                        if zoom:
                            image_url = self._normalize_image_url(zoom)
                            break
                        srcset = img.get('srcset')
                        if srcset:
                            best = pick_best_from_srcset(srcset)
                            if best:
                                image_url = self._normalize_image_url(best)
                                break
                        src = img.get('src')
                        if src:
                            image_url = self._normalize_image_url(src)
                            break
                    except Exception:
                        continue
            return {
                'name': name or 'Unknown Product',
                'price': price,
                'platform': 'mercadolibre',
                'url': article_url,
                'image_url': self._normalize_image_url(image_url)
            }
        except Exception as e:
            API_ERRORS.labels(endpoint="scrape_product_html_fallback").inc()
            self.logger.error({"event": "scrape_product_html_fallback_error", "item_id": item_id, "error": str(e)})
            return {
                'name': 'Unknown Product',
                'price': None,
                'platform': 'mercadolibre',
                'url': article_url,
                'image_url': None
            }

    def _scrape_mercadolibre_html_by_url(self, url: str) -> Dict:
        """Fallback mínimo: obtener título e imagen desde una URL de ML directamente."""
        try:
            resp = self._request_get(url, timeout=15, retries=1)
            soup = BeautifulSoup(resp.text, 'html.parser')
            name = None
            image_url = None
            price = None
            og_title = soup.find('meta', property='og:title')
            if og_title:
                name = og_title.get('content')
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = self._normalize_image_url(og_image.get('content'))
            if not image_url:
                tw_img = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', property='twitter:image')
                if tw_img and tw_img.get('content'):
                    image_url = self._normalize_image_url(tw_img.get('content'))
            # JSON-LD Product si aparece
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string or '{}')
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        name = name or data.get('name')
                        offers = data.get('offers')
                        if isinstance(offers, dict):
                            try:
                                price = float(offers.get('price', 0)) or None
                            except Exception:
                                pass
                        if not image_url:
                            img = data.get('image')
                            if isinstance(img, str):
                                image_url = img
                            elif isinstance(img, list) and img:
                                image_url = img[0]
                        break
                except Exception:
                    continue
            # Galería de imágenes: ui-pdp-image/srcset/data-zoom
            if not image_url:
                def pick_best_from_srcset(srcset: str) -> Optional[str]:
                    try:
                        candidates = []
                        for part in (srcset or '').split(','):
                            part = part.strip()
                            if not part:
                                continue
                            bits = part.split()
                            url = bits[0]
                            descriptor = bits[1] if len(bits) > 1 else ''
                            score = 0
                            if '2x' in descriptor:
                                score = 2000
                            else:
                                m = re.search(r'(\d+)w', descriptor)
                                if m:
                                    score = int(m.group(1))
                            candidates.append((score, url))
                        if candidates:
                            candidates.sort(reverse=True)
                            return candidates[0][1]
                    except Exception:
                        return None
                for img in soup.select('img.ui-pdp-image, img.ui-pdp-gallery__figure__image, img[src*="mlstatic.com"]'):
                    try:
                        zoom = img.get('data-zoom')
                        if zoom:
                            image_url = self._normalize_image_url(zoom)
                            break
                        srcset = img.get('srcset')
                        if srcset:
                            best = pick_best_from_srcset(srcset)
                            if best:
                                image_url = self._normalize_image_url(best)
                                break
                        src = img.get('src')
                        if src:
                            image_url = self._normalize_image_url(src)
                            break
                    except Exception:
                        continue
            return {
                'name': name or 'Unknown Product',
                'price': price,
                'platform': 'mercadolibre',
                'url': url,
                'image_url': self._normalize_image_url(image_url)
            }
        except Exception as e:
            API_ERRORS.labels(endpoint="scrape_product_html_by_url_fallback").inc()
            self.logger.error({"event": "scrape_product_html_by_url_error", "url": url, "error": str(e)})
            return {
                'name': 'Unknown Product',
                'price': None,
                'platform': 'mercadolibre',
                'url': url,
                'image_url': None
            }

    def _scrape_mercadolibre_reviews(self, item_id: str, max_reviews: int = 50) -> List[Dict]:
        """Intento de scraping básico de reseñas desde la página del artículo.
        Si no se puede, devuelve lista vacía para no bloquear el análisis."""
        try:
            # Derivar dominio por prefijo del item_id
            prefix = (item_id[:3] or '').upper()
            tld_map = {
                'MLA': 'com.ar',
                'MLB': 'com.br',
                'MLM': 'com.mx',
                'MLC': 'cl',
                'MCO': 'com.co',
                'MLU': 'com.uy',
                'MLV': 'com.ve',
                'MPE': 'com.pe',
            }
            tld = tld_map.get(prefix, 'com.ar')
            article_url = f"https://articulo.mercadolibre.{tld}/{item_id}"
            resp = self._request_get(article_url, timeout=15, retries=1)
            soup = BeautifulSoup(resp.text, 'html.parser')
            reviews: List[Dict] = []
            # Mercado Libre suele renderizar reseñas dinámicamente; intentamos capturar snippets visibles
            for block in soup.select('div.review')[:max_reviews]:
                try:
                    text = (block.get_text() or '').strip()
                    if not text:
                        continue
                    # Rating si está disponible como estrellas
                    rating = None
                    star_el = block.select_one('[aria-label*="estrellas"], [aria-label*="stars"]')
                    if star_el and star_el.get('aria-label'):
                        m = re.search(r"(\d+(?:\.\d+)?)", star_el.get('aria-label'))
                        if m:
                            rating = float(m.group(1))
                    reviews.append({
                        'user_name': 'Anonymous',
                        'rating': rating or 3.0,
                        'text': text,
                        'review_date': datetime.utcnow(),
                        'platform': 'mercadolibre'
                    })
                except Exception:
                    continue
            return reviews
        except Exception as e:
            API_ERRORS.labels(endpoint="scrape_reviews_html_fallback").inc()
            self.logger.error({"event": "scrape_reviews_html_fallback_error", "item_id": item_id, "error": str(e)})
            return []

    # Actualiza scrape_product para usar API si es ML; resto comentado
    def scrape_product(self, url: str) -> Dict:
        platform = self.detect_platform(url)
        if platform == 'mercadolibre':
            item_id = self._extract_meli_item_id(url)
            if item_id:
                return self.scrape_product_api(item_id)
            else:
                # Intentar scraper mínimo por la URL directa
                return self._scrape_mercadolibre_html_by_url(url)
        # Fallback genérico comentado: centrarnos en ML.
        # try:
        #     resp = self._request_get(url, timeout=15, retries=1)
        #     soup = BeautifulSoup(resp.text, 'html.parser')
        #     name = None
        #     image_url = None
        #     price = None
        #     # OG
        #     og_title = soup.find('meta', property='og:title')
        #     if og_title:
        #         name = og_title.get('content')
        #     og_image = soup.find('meta', property='og:image')
        #     if og_image:
        #         image_url = og_image.get('content')
        #     # JSON-LD Product
        #     for script in soup.find_all('script', type='application/ld+json'):
        #         try:
        #             import json
        #             data = json.loads(script.string or '{}')
        #             if isinstance(data, dict) and data.get('@type') == 'Product':
        #                 name = name or data.get('name')
        #                 offers = data.get('offers')
        #                 if isinstance(offers, dict):
        #                     price = price or float(offers.get('price', 0)) or None
        #                 if not image_url and isinstance(data.get('image'), (str, list)):
        #                     image_url = data.get('image')[0] if isinstance(data.get('image'), list) else data.get('image')
        #                 break
        #         except Exception:
        #             continue
        #     parsed = urlparse(url)
        #     return {
        #         'name': name or (parsed.hostname or 'Unknown Product'),
        #         'price': price,
        #         'platform': platform,
        #         'url': url,
        #         'image_url': image_url
        #     }
        # except Exception as e:
        #     print(f"Fallback genérico producto error: {e}")
        #     return {
        #         'name': 'Unknown Product',
        #         'price': None,
        #         'platform': platform,
        #         'url': url,
        #         'image_url': None
        #     }

    def scrape_reviews(self, url: str, max_reviews: int = 50) -> List[Dict]:
        platform = self.detect_platform(url)
        if platform == 'mercadolibre':
            item_id = self._extract_meli_item_id(url)
            if item_id:
                return self.scrape_reviews_api(item_id, max_reviews)
            else:
                self.logger.warning("No se pudo extraer item_id de URL ML para reseñas: %s", url)
                API_ERRORS.labels(endpoint="scraper").inc()
        # Fallback para otras plataformas comentado: nos centramos en ML.
        return []

    # Resto de tu código original (detect_platform, _scrape_amazon_reviews, templates, etc.)

# Instancia singleton
scraper = ProductScraper()