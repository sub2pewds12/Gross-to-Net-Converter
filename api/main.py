from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from .routers import gross_net

DESCRIPTION = f"""
API for calculating Vietnamese Net Income from Gross Income based on regulations
applicable around **April 2025**. 🇻🇳 (Generated on: Thursday, April 17, 2025)

Provides endpoints for:
* **Gross-to-Net Calculation**: `/calculate/gross-to-net` (POST)

Uses data like Personal/Dependent Allowances, Regional Minimum Wages,
Insurance Rates/Caps, and Progressive PIT brackets.
"""

app = FastAPI(
    title="Vietnam Gross Net Calculator API",
    description=DESCRIPTION,
    version="0.1.0",
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
)

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

app.include_router(gross_net.router, prefix="/calculate")


@app.get("/", tags=["Root"], summary="API Welcome Message")
async def read_root():
    """
    Root endpoint providing a welcome message and links to the API documentation.
    Useful for checking if the API is reachable.
    """
    return {
        "message": "Welcome to the VN Gross Net Calculator API!",
        "documentation": app.docs_url,
        "alternative_documentation": app.redoc_url,
    }


@app.get(
    "/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Health Check"
)
async def health_check():
    """Basic health check endpoint to verify API service status. Returns status 'ok'."""
    return {"status": "healthy"}
