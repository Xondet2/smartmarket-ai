# SmartMarket AI - Backend

Backend API built with FastAPI for product analysis with lightweight sentiment analysis.

## Features

- RESTful API for product management
- Mercado Libre official API focus (no multi-platform scraping)
- Lightweight sentiment analysis of reviews (lexicon-based, no heavy ML)
- SQLite database (local) with PostgreSQL migration support

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Nota: el proyecto usa `EmailStr` de Pydantic para validar correos, por eso en `requirements.txt` se incluye `pydantic[email]` (que instala `email-validator`). Si instalas manualmente, usa:

\`\`\`bash
pip install "pydantic[email]>=2.12.0,<3.0.0"
\`\`\`

## Running the server

\`\`\`bash
uvicorn main:app --reload
\`\`\`

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

\`\`\`
backend/
├── main.py                 # FastAPI application entry point
├── routes/                 # API endpoints
│   ├── products.py
│   ├── reviews.py
│   └── analysis.py
├── services/              # Business logic
│   ├── scraper.py              # Mercado Libre API-only
│   ├── sentiment_analyzer.py   # Lightweight, lexicon-based sentiment
│   └── price_comparator.py     # (legacy, not used)
├── database/              # Database models and config (coming soon)
│   ├── models.py
│   └── db_config.py
└── requirements.txt       # Python dependencies (slim for fast deploy)
