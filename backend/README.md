# SmartMarket AI - Backend

Backend API built with FastAPI for product analysis with AI-powered sentiment analysis.

## Features

- RESTful API for product management
- Web scraping from e-commerce platforms
- AI-powered sentiment analysis
- Price comparison
- SQLite database (local) with PostgreSQL migration support

## Installation

\`\`\`bash
pip install -r requirements.txt
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
├── services/              # Business logic (coming soon)
│   ├── scraper.py
│   ├── sentiment_analyzer.py
│   └── price_comparator.py
├── database/              # Database models and config (coming soon)
│   ├── models.py
│   └── db_config.py
└── requirements.txt       # Python dependencies
