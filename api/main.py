# api/main.py

import logging
import os
from dotenv import load_dotenv  # Import python-dotenv
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import gross_net

# Load environment variables from .env file (for local development)
# This should be one of the first things your application does.
load_dotenv()

# --- Basic Logging Configuration ---
# Read LOG_LEVEL from environment, default to INFO
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
API for calculating Vietnamese Net Income from Gross Income based on regulations
applicable around **April 2025**. 🇻🇳

Running in environment: **{API_ENVIRONMENT}**

Provides endpoints for:
* **Gross-to-Net Calculation**: `/calculate/gross-to-net` (POST)

Uses data like Personal/Dependent Allowances, Regional Minimum Wages,
Insurance Rates/Caps, and Progressive PIT brackets.
"""


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    logger.info("FastAPI application startup via lifespan event.")
    yield
    logger.info("FastAPI application shutdown via lifespan event.")


# --- Initialize FastAPI app ---
app = FastAPI(
    title="Vietnam Gross Net Calculator API",
    description=DESCRIPTION,
    version="0.1.4",
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
        {"name": "Health", "description": "Endpoints for checking API status."},
        {"name": "Root", "description": "Basic API information."},
    ],
    lifespan=lifespan,
)

# --- Optional: Configure CORS ---
# origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "") # Example: "http://localhost:8501,https://your-frontend.onrender.com"
# if origins_str:
#     origins = [origin.strip() for origin in origins_str.split(',')]
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=origins,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#     logger.info(f"CORS middleware enabled for origins: {origins}")
# else:
#     logger.info("CORS middleware configuration is currently not set or commented out.")


app.include_router(gross_net.router, prefix="/calculate")
logger.info("Included gross_net router with prefix /calculate.")


@app.get("/", tags=["Root"], summary="API Welcome Message")
async def read_root():
    logger.info("Root endpoint '/' accessed.")
    return {
        "message": "Welcome to the VN Gross Net Calculator API!",
        "documentation": app.docs_url,
        "alternative_documentation": app.redoc_url,
    }


@app.get(
    "/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Health Check"
)
async def health_check():
    logger.info("Health check endpoint '/health' accessed, returning status: ok.")
    return {"status": "healthy"}
