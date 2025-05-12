# api/main.py

import logging
import os # For reading environment variables
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware # Optional
from contextlib import asynccontextmanager # Import for lifespan events

# Corrected import: Use relative import for routers within the same 'api' package
from .routers import gross_net

# --- Basic Logging Configuration ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# --- Application Metadata & Environment Demonstration ---
API_ENVIRONMENT = os.getenv("API_ENV", "development")

DESCRIPTION = f"""
API for calculating Vietnamese Net Income from Gross Income based on regulations
applicable around **April 2025**. 🇻🇳

Running in environment: **{API_ENVIRONMENT}**

Provides endpoints for:
* **Gross-to-Net Calculation**: `/calculate/gross-to-net` (POST)

Uses data like Personal/Dependent Allowances, Regional Minimum Wages,
Insurance Rates/Caps, and Progressive PIT brackets.
"""

logger.info(f"FastAPI application starting in '{API_ENVIRONMENT}' environment.")

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Code to run on startup
    logger.info("FastAPI application startup complete via lifespan event.")
    # You could add database connections or other initializations here
    yield
    # Code to run on shutdown
    logger.info("FastAPI application shutting down via lifespan event.")
    # Clean up resources here if needed

# --- Initialize FastAPI app ---
# Pass the lifespan manager to the FastAPI app
app = FastAPI(
    title="Vietnam Gross Net Calculator API",
    description=DESCRIPTION,
    version="0.1.3", # Increment version due to lifespan change
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
        {"name": "Calculations", "description": "Endpoints related to income calculations."},
        {"name": "Health", "description": "Endpoints for checking API status."},
        {"name": "Root", "description": "Basic API information."},
    ],
    lifespan=lifespan # Register the lifespan context manager
)

# --- Optional: Configure CORS ---
# origins = [
#     "http://localhost",
#     "http://localhost:8501",
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
logger.info("CORS middleware configuration is currently commented out.")

# --- Include API Routers ---
app.include_router(gross_net.router, prefix="/calculate")
logger.info("Included gross_net router with prefix /calculate.")

# --- Root Endpoint ---
@app.get("/", tags=["Root"], summary="API Welcome Message")
async def read_root():
    logger.info("Root endpoint '/' accessed.")
    return {
        "message": "Welcome to the VN Gross Net Calculator API!",
        "documentation": app.docs_url,
        "alternative_documentation": app.redoc_url
        }

# --- Health Check Endpoint (Good Practice) ---
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Health Check")
async def health_check():
    logger.info("Health check endpoint '/health' accessed, returning status: ok.")
    return {"status": "healthy"}

# --- DEPRECATED Application Startup/Shutdown Events (Optional) ---
# @app.on_event("startup")
# async def startup_event():
#     logger.info("FastAPI application startup complete.")
#     # You could add database connections or other initializations here

# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("FastAPI application shutting down.")
#     # Clean up resources here if needed


