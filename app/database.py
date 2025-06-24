import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# Default to SQLite for local development, but allow PostgreSQL via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gibster_dev.db")

# For SQLite, add more configuration options
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        pool_pre_ping=True,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 