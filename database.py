from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ganti dengan URL koneksi PostgreSQL Anda
# Database configuration
import os

# Use environment variable or default to SQLite for development
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ocr_development.db")

# Create engine with appropriate settings
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
