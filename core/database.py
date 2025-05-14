# core/database.py

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Get a logger instance
logger = logging.getLogger(__name__)

# Load environment variables from .env file (especially for local development)
# This allows DATABASE_URL to be set in .env for local runs outside Docker Compose
# or for other configurations.
load_dotenv()

# --- Database URL Configuration ---
# For local development with Docker Compose, this will be overridden by the
# DATABASE_URL environment variable set in docker-compose.yml for the api service.
# For Render deployment, this will be Render's internal PostgreSQL connection string,
# also set as an environment variable.
# The default value here is more of a placeholder or for very basic local testing
# if no environment variable is set.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/appdb"
)

if DATABASE_URL.startswith("postgresql://user:password@localhost"):
    logger.warning(
        f"Using default placeholder DATABASE_URL: {DATABASE_URL}. "
        "Ensure DATABASE_URL environment variable is set correctly for Docker Compose or Render."
    )
else:
    logger.info(
        f"Database URL configured: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'URL configured (details masked)'}"
    )


# Create SQLAlchemy engine
# pool_pre_ping is good for handling stale connections with PostgreSQL.
engine_args = {}
if DATABASE_URL.startswith("postgresql"):
    engine_args["pool_pre_ping"] = True
    # For Render's managed PostgreSQL, SSL might be required.
    # Render typically provides the full connection string with sslmode if needed.
    # Example if you needed to force it (usually not necessary if Render provides full URL):
    # if "onrender.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    #     logger.info("Attempting to add sslmode=require for Render PostgreSQL connection.")
    #     DATABASE_URL += "?sslmode=require" # This might need to be more robust

engine = create_engine(DATABASE_URL, **engine_args)

# Create a SessionLocal class to create database sessions
# autocommit=False and autoflush=False are standard defaults for web applications.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative SQLAlchemy models
# All your DB models (like SavedCalculationDB) will inherit from this.
Base = declarative_base()


# --- Dependency for FastAPI to get DB session ---
def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Ensures the session is always closed after the request, even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Function to create database tables ---
def create_db_and_tables():
    """
    Creates all database tables defined by SQLAlchemy models
    that inherit from Base. This should typically be called once at application startup
    (e.g., in api/main.py's lifespan event).

    For production environments using database migration tools like Alembic,
    this function might not be used directly for table creation after the initial setup.
    Alembic would handle schema changes.
    """
    logger.info(
        f"Attempting to create database tables for engine: {engine.url.render_as_string(hide_password=True)}"
    )
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(
            "Database tables checked/created successfully (if they didn't already exist)."
        )
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}", exc_info=True)
        # In a real application, you might want to raise this or handle it more gracefully
        # to prevent the application from starting if the DB is not accessible/set up.
