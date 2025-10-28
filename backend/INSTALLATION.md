# Backend Installation Guide

## Prerequisites

- Python 3.9 or higher (Python 3.13+ recommended)
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Create Virtual Environment (Recommended)

\`\`\`bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate
\`\`\`

### 2. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

This will install:
- FastAPI and Uvicorn (API framework)
- SQLAlchemy (Database ORM)
- BeautifulSoup4 (Web scraping)
- Transformers and PyTorch (AI sentiment analysis)
- Pandas and NumPy (Data processing)
- And other required packages

### 3. Run the Server

\`\`\`bash
uvicorn main:app --reload
\`\`\`

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### 4. Test the API

Visit http://localhost:8000/health to verify the server is running.

## Database

The application uses SQLite by default, which requires no additional setup. The database file `smartmarket.db` will be created automatically in the backend directory on first run.

## Troubleshooting

### Dependency Version Errors

If you see errors about incompatible versions (e.g., "Could not find a version that satisfies the requirement torch==2.5.0"):

\`\`\`bash
# Upgrade pip first
pip install --upgrade pip

# Install with flexible versions
pip install -r requirements.txt --upgrade
\`\`\`

The requirements.txt uses flexible version constraints to ensure compatibility with your Python version.

### PyTorch Installation Issues

If you encounter issues installing PyTorch, you can install a CPU-only version:

\`\`\`bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
\`\`\`

### Transformers Model Download

On first run, the sentiment analysis model will be downloaded automatically. This may take a few minutes depending on your internet connection.

### Port Already in Use

If port 8000 is already in use, you can specify a different port:

\`\`\`bash
uvicorn main:app --reload --port 8001
\`\`\`

Don't forget to update the frontend's `.env.local` file with the new port.

## Production Deployment

For production deployment:

1. Set `DATABASE_URL` environment variable to PostgreSQL connection string
2. Disable auto-reload: `uvicorn main:app --host 0.0.0.0 --port 8000`
3. Use a production ASGI server like Gunicorn with Uvicorn workers
4. Set up proper CORS origins in `main.py`

## Next Steps

After the backend is running, start the frontend application to use the full SmartMarket AI system.
