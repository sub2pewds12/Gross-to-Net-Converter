# api/routers/gross_net.py

import logging
from fastapi import APIRouter, Body, HTTPException, status

# Import core components
from core.calculator import calculate_gross_to_net
from core.models import GrossNetInput, GrossNetResult

# Import custom exceptions from core
from core.exceptions import (
    CoreCalculationError,
    InvalidRegionError,
    InvalidInputDataError,
    NegativeGrossIncomeError,
    NegativeDependentsError,
    MissingConfigurationError,
)

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# Create an API router instance
router = APIRouter()


@router.post(
    "/gross-to-net",
    response_model=GrossNetResult,
    summary="Calculate Net Income from Gross Income",
    description=(
        "Calculates Vietnamese Net income, PIT, and insurance contributions "
        "based on Gross Income, Number of Dependents, and Region for April "
        "2025 regulations."
    ),
    tags=["Calculations"],
)
async def api_calculate_gross_to_net(
    input_data: GrossNetInput = Body(  # noqa: B008 (FastAPI standard practice)
        ...,
        examples={
            "Basic Case (Region 1, 1 Dependent)": {
                "summary": "30M Gross, 1 Dependent, R1",
                "description": "A standard calculation example.",
                "value": {"gross_income": 30000000, "num_dependents": 1, "region": 1},
            },
            "No Dependents (Region 1)": {
                "summary": "20M Gross, 0 Dependents, R1",
                "description": "Lower income, no dependents.",
                "value": {"gross_income": 20000000, "num_dependents": 0, "region": 1},
            },
        },
    ),
):
    """
    Performs the Gross-to-Net income calculation based on provided inputs.

    - **gross_income**: Monthly gross salary in VND (> 0).
    - **num_dependents**: Number of registered dependents (>= 0).
    - **region**: Work location region (1-4).

    Returns a detailed breakdown including Net Income, PIT, insurance amounts,
    taxable income, and pre-tax income. Raises HTTP exceptions for invalid inputs
    or calculation errors.
    """
    logger.info(f"Received request for /gross-to-net: {input_data.model_dump_json()}")

    try:
        result = calculate_gross_to_net(input_data)
        logger.info(f"Calculation successful for input: {input_data.model_dump_json()}")
        return result
    except (
        InvalidRegionError,
        NegativeGrossIncomeError,
        NegativeDependentsError,
        InvalidInputDataError,
    ) as e:
        logger.warning(
            f"Input validation error for /gross-to-net "
            f"({type(e).__name__}): {str(e)} - Input: {input_data.model_dump_json()}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Bad Request
            detail=str(e),
        ) from e
    except MissingConfigurationError as e:
        logger.error(
            f"Configuration error during /gross-to-net calculation: {str(e)} - Input: {input_data.model_dump_json()}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal configuration error: {str(e)}",
        ) from e
    except CoreCalculationError as e:  # Catch other specific core errors
        logger.error(
            f"Core calculation error for /gross-to-net: {str(e)} - Input: {input_data.model_dump_json()}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Or 500 if it's an unexpected core logic flaw
            detail=f"Calculation error: {str(e)}",
        ) from e
    except Exception as e:
        # Catch any other unexpected errors during calculation
        logger.error(
            f"Unexpected error during /gross-to-net calculation: {str(e)} - Input: {input_data.model_dump_json()}",
            exc_info=True,  # Includes stack trace in logs
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred while processing the calculation.",
        ) from e


# --- Placeholder for potential future endpoints ---
# @router.post("/net-to-gross", tags=["Calculations"])
# async def api_calculate_net_to_gross():
#     """ Calculates Gross income based on desired Net income (Not Implemented). """
#     logger.info("Received request for /net-to-gross (Not Implemented)")
#     raise HTTPException(
#         status_code=status.HTTP_501_NOT_IMPLEMENTED,
#         detail="Net to Gross calculation not implemented yet."
#     )
