"""
Resumen del módulo:
- Configuración de SQLAlchemy: engine, SessionLocal y Base.
- Patrón: adaptación de URL para PostgreSQL (Heroku/Railway) y SQLite dev.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartmarket.db")

# Ajuste para URLs de PostgreSQL en Heroku/Railway (usan postgres:// en vez de postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crea el engine con configuración apropiada para SQLite o PostgreSQL
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Crea la clase SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crea la clase Base para modelos
Base = declarative_base()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicializa la base de datos
def init_db():
    """Crea todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)
