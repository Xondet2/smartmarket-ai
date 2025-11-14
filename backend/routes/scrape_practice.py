from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from services.sentiment_analyzer import sentiment_analyzer

router = APIRouter()

class ReviewItem(BaseModel):
    source: str
    item_type: str
    item_name: str
    rating: Optional[float] = None
    text: str

class SentimentSummary(BaseModel):
    stars: float
    sentiment_label: str
    avg_sentiment: float
    total_reviews: int
    keywords: List[str]
    opinion_summary: str
    positive_count: int
    neutral_count: int
    negative_count: int

def _slugify(name: str, space_replacement: str = "_") -> str:
    return (name or "").strip().lower().replace(" ", space_replacement)

def _opinion_summary(analysis: Dict, stars: float) -> str:
    label = str(analysis.get("sentiment_label", "neutral"))
    total = int(analysis.get("total_reviews", 0))
    dist = analysis.get("sentiment_distribution", {}) or {}
    pos = dist.get("positive")
    neu = dist.get("neutral")
    neg = dist.get("negative")
    # Frase base por etiqueta
    base = {
        "positive": "En general la percepción es positiva.",
        "negative": "La percepción general es negativa.",
        "neutral": "La percepción es mixta o neutral.",
    }.get(label, "La percepción es mixta o neutral.")

    # Construir partes opcionales
    parts: List[str] = [base]
    parts.append(f"Promedio {round(stars, 1)}★ con {total} reseñas.")
    if isinstance(pos, (int, float)) and isinstance(neu, (int, float)) and isinstance(neg, (int, float)):
        parts.append(f"Distribución: {pos}% positivas, {neu}% neutrales, {neg}% negativas.")
    kws: List[str] = list(analysis.get("keywords", []))
    if kws:
        tops = ", ".join(kws[:6])
        parts.append(f"Temas destacados: {tops}.")
    return " ".join(parts)

def _to_summary(analysis: Dict) -> SentimentSummary:
    avg = float(analysis.get("avg_sentiment", 0.5))
    label = str(analysis.get("sentiment_label", "neutral"))
    total = int(analysis.get("total_reviews", 0))
    keywords: List[str] = list(analysis.get("keywords", []))
    # Mapear a estrellas 1-5, sin forzar mínimo de 1 si el sentimiento es bajo
    stars = round(max(0.0, min(5.0, avg * 5.0)), 1)
    pos = int(analysis.get("positive_count", 0))
    neu = int(analysis.get("neutral_count", 0))
    neg = int(analysis.get("negative_count", 0))
    return SentimentSummary(
        stars=stars,
        sentiment_label=label,
        avg_sentiment=round(avg, 3),
        total_reviews=total,
        keywords=keywords,
        opinion_summary=_opinion_summary(analysis, stars),
        positive_count=pos,
        neutral_count=neu,
        negative_count=neg,
    )

def _http_get(url: str) -> requests.Response:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    return requests.get(url, headers=headers, timeout=20)

def _extract_texts(soup: BeautifulSoup, selectors: List[str]) -> List[str]:
    texts: List[str] = []
    for sel in selectors:
        for node in soup.select(sel):
            txt = node.get_text(strip=True)
            if txt:
                texts.append(txt)
    # De-duplicate preserving order
    seen = set()
    result: List[str] = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result

@router.get("/scrape/{source}", response_model=List[ReviewItem])
async def scrape_reviews(source: str, query: str = Query(..., min_length=2)):
    """
    Scrapea reseñas desde sitios de práctica: Trustpilot, RottenTomatoes, Goodreads.
    Basado en la lógica del archivo `nuevo.txt` y adaptado al proyecto.
    """
    source = source.strip().lower()
    if source not in {"trustpilot", "rottentomatoes", "goodreads"}:
        raise HTTPException(status_code=400, detail="Unsupported source")

    try:
        reviews: List[Dict] = []
        if source == "trustpilot":
            domain = _slugify(query, space_replacement='')
            url = f"https://www.trustpilot.com/review/{domain}"
            html = _http_get(url).text
            soup = BeautifulSoup(html, "html.parser")
            texts = _extract_texts(soup, [
                "section[data-service-review-card-layout]",
                "div.review-card",
                "div.styles_reviewCardInner__E3jJI",
                "p",
            ])
            for text in texts[:50]:
                if len(text) < 20:
                    continue
                reviews.append({
                    "source": "trustpilot",
                    "item_type": "product",
                    "item_name": query,
                    "rating": None,
                    "text": text,
                })
        elif source == "rottentomatoes":
            slug = _slugify(query)
            # Intento 1: endpoint JSON (napi)
            api_url = f"https://www.rottentomatoes.com/napi/movie/{slug}/reviews?type=user&sort=&page=1"
            try:
                resp = _http_get(api_url)
                if resp.status_code == 200:
                    j = resp.json()
                    items = j.get("reviews", [])
                    for it in items[:50]:
                        text = it.get("review") or it.get("quote") or ""
                        text = (text or "").strip()
                        if not text:
                            continue
                        reviews.append({
                            "source": "rottentomatoes",
                            "item_type": "movie",
                            "item_name": query,
                            "rating": None,
                            "text": text,
                        })
            except Exception:
                pass
            # Fallback: parse HTML
            if not reviews:
                url = f"https://www.rottentomatoes.com/m/{slug}/reviews?type=user"
                html = _http_get(url).text
                soup = BeautifulSoup(html, "html.parser")
                texts = _extract_texts(soup, [
                    "[data-qa='review-text']",
                    ".review-text",
                    ".audience-reviews__review",
                ])
                for text in texts[:50]:
                    if len(text) < 10:
                        continue
                    reviews.append({
                        "source": "rottentomatoes",
                        "item_type": "movie",
                        "item_name": query,
                        "rating": None,
                        "text": text,
                    })
        elif source == "goodreads":
            # Goodreads suele tener dos rutas útiles: la página del libro y la de reseñas.
            # Aceptamos slugs con ID (p.ej. "4671.The_Great_Gatsby") o títulos simples.
            raw = (query or "").strip()
            # Mantener mayúsculas/dígitos si el usuario pasó un slug con ID; si no, normalizar título.
            if any(ch.isdigit() for ch in raw) and "." in raw:
                slug = raw  # Parece un slug con ID (p.ej. 4671.The_Great_Gatsby)
            else:
                slug = _slugify(raw, space_replacement='-')

            candidates = [
                f"https://www.goodreads.com/book/show/{slug}/reviews?rating=all&sort=newest&text_only=true",
                f"https://www.goodreads.com/book/show/{slug}?text_only=true",
                f"https://www.goodreads.com/book/show/{slug}",
            ]

            texts: List[str] = []
            for url in candidates:
                try:
                    html = _http_get(url).text
                    soup = BeautifulSoup(html, "html.parser")
                    # Ampliar selectores para nuevas páginas (React) y clásicas
                    sel = [
                        ".reviewText span.readable",
                        "div.reviewText",
                        "div.reviewText span",
                        "section[data-testid='review']",
                        "article[data-testid='review']",
                        "[data-testid='reviewText']",
                        "[data-testid='content']",
                        "div[class*='ReviewText']",
                        "div[class*='ReviewsList__review']",
                        "div.review",
                        "p",
                    ]
                    texts = _extract_texts(soup, sel)
                    # Si encontramos suficientes textos, detenemos el ciclo
                    if len(texts) >= 5:
                        break
                except Exception:
                    continue

            for text in texts[:50]:
                t = (text or "").strip()
                if len(t) < 20:
                    continue
                reviews.append({
                    "source": "goodreads",
                    "item_type": "book",
                    "item_name": query,
                    "rating": None,
                    "text": t,
                })

        if not reviews:
            raise HTTPException(status_code=424, detail="No se encontraron reseñas. Intenta otro término o URL.")

        return [ReviewItem(**rev) for rev in reviews]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error scraping reviews")

class AnalyzeRequest(BaseModel):
    source: str
    query: str

@router.post("/scrape/analyze", response_model=SentimentSummary)
async def analyze_scraped_reviews(req: AnalyzeRequest):
    """
    Ejecuta scraping y devuelve un resumen de sentimiento con estrellas y opinión.
    """
    items = await scrape_reviews(req.source, req.query)
    review_dicts = [{"text": i.text, "rating": i.rating} for i in items]
    analysis = sentiment_analyzer.analyze_reviews(review_dicts)
    return _to_summary(analysis)