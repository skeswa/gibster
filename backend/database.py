import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from logging_config import get_logger

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

logger = get_logger("database")

# Database configuration
# Default to SQLite for local development, but allow PostgreSQL via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/gibster_dev.db")

logger.info(f"Configuring database connection to: {DATABASE_URL.split('://')[0]}://...")

# For SQLite, add more configuration options
if "sqlite" in DATABASE_URL:
    logger.info("Using SQLite database configuration")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 20},
        pool_pre_ping=True,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true",
    )
else:
    # PostgreSQL or other databases
    logger.info("Using PostgreSQL/other database configuration")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true",
    )


# Add database event listeners for logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connections"""
    logger.info("Database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_connection, connection_record):
    """Log database disconnections"""
    logger.debug("Database connection closed")


@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log SQL queries (only for debug level)"""
    context._query_start_time = time.time()
    if logger.isEnabledFor(10):  # DEBUG level
        logger.debug(
            f"SQL Query: {statement[:100]}{'...' if len(statement) > 100 else ''}"
        )


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log query execution time"""
    if hasattr(context, "_query_start_time"):
        total = time.time() - context._query_start_time
        if total > 1.0:  # Log slow queries
            logger.warning(
                f"Slow query detected: {total:.3f}s - {statement[:100]}{'...' if len(statement) > 100 else ''}"
            )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        logger.debug("Database session closed")
        db.close()
