# api/main.py

import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, status

# from fastapi.middleware.cors import CORSMiddleware # Keep commented if not used
from contextlib import asynccontextmanager

# Import routers
from .routers import gross_net
from .routers import saved_calculations_router  # <-- IMPORT NEW ROUTER

# Import database utilities from core
from core import database  # For create_db_and_tables

# Load environment variables from .env file
load_dotenv()

# --- Basic Logging Configuration ---
LOG_LEVEL_FROM_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL_FROM_ENV,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to: {LOG_LEVEL_FROM_ENV}")

# --- Application Metadata & Environment ---
API_ENVIRONMENT = os.getenv("API_ENV", "development")
logger.info(f"FastAPI application starting in '{API_ENVIRONMENT}' environment.")

DESCRIPTION = f"""
API for calculating Vietnamese Net Income from Gross Income and managing saved calculations.
Regulations applicable around **April 2025**. 🇻🇳

Running in environment: **{API_ENVIRONMENT}**

Provides endpoints for:
* **Gross-to-Net Calculation (Single)**: `/calculate/gross-to-net` (POST)
* **Gross-to-Net Calculation (Batch Excel)**: `/calculate/batch-excel-upload` (POST)
* **Saved Calculations CRUD**: under `/saved-calculations`
"""


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Code to run on startup
    logger.info("FastAPI application startup initiated via lifespan event...")
    try:
        # Create database tables if they don't exist
        # This is suitable for development. For production, consider using migrations (e.g., Alembic).
        database.create_db_and_tables()
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error during database table creation: {e}", exc_info=True)
        # Depending on severity, you might want to prevent app startup if DB init fails
    logger.info("FastAPI application startup complete.")
    yield
    # Code to run on shutdown
    logger.info("FastAPI application shutting down via lifespan event.")


# --- Initialize FastAPI app ---
app = FastAPI(
    title="Vietnam Gross Net Calculator API",
    description=DESCRIPTION,
    version="0.3.0",  # Version bump for CRUD
    contact={
        "name": "Your Name / Project Team",
        "url": "http://yourexample.com/contact",
        "email": "your.email@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Calculations",
            "description": "Endpoints related to income calculations.",
        },
        {
            "name": "Saved Calculations",
            "description": "Endpoints for managing saved calculation records.",
        },
        {"name": "Health", "description": "Endpoints for checking API status."},
        {"name": "Root", "description": "Basic API information."},
    ],
    lifespan=lifespan,
)

# --- Optional: Configure CORS ---
# ... (CORS middleware code remains commented out unless needed) ...
logger.info("CORS middleware configuration is currently commented out.")

# --- Include API Routers ---
app.include_router(gross_net.router, prefix="/calculate", tags=["Calculations"])
app.include_router(
    saved_calculations_router.router
)  # Prefix is defined in the router itself
logger.info("Included gross_net and saved_calculations routers.")


# --- Root Endpoint ---
@app.get("/", tags=["Root"], summary="API Welcome Message")
async def read_root():
    logger.info("Root endpoint '/' accessed.")
    return {
        "message": "Welcome to the VN Gross Net Calculator API!",
        "documentation": app.docs_url,
        "alternative_documentation": app.redoc_url,
    }


# --- Health Check Endpoint ---
@app.get(
    "/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Health Check"
)
async def health_check():
    logger.info("Health check endpoint '/health' accessed, returning status: ok.")
    return {"status": "healthy"}
