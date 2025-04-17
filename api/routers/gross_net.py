from fastapi import APIRouter, HTTPException, Body, status
from core.calculator import calculate_gross_to_net
from core.models import GrossNetInput, GrossNetResult

router = APIRouter()

@router.post(
    "/gross-to-net",
    response_model=GrossNetResult,
    summary="Calculate Net Income from Gross Income",
    description="Calculates Vietnamese Net income, PIT, and insurance contributions based on Gross Income, Number of Dependents, and Region for April 2025 regulations.",
    tags=["Calculations"]
)
async def api_calculate_gross_to_net(
    input_data: GrossNetInput = Body(
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
             "High Income (Region 1, 2 Dependents)": {
                "summary": "100M Gross, 2 Dependents, R1",
                "description": "Example reaching higher tax brackets.",
                "value": {"gross_income": 100000000, "num_dependents": 2, "region": 1},
            },
            "Lower Region (Region 4, 0 Dependents)": {
                 "summary": "15M Gross, 0 Dependents, R4",
                 "description": "Lower income in Region 4.",
                 "value": {"gross_income": 15000000, "num_dependents": 0, "region": 4},
            }
        },
    )
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
    try:
        result = calculate_gross_to_net(input_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation error: {str(e)}"
            )
    except Exception as e:
        print(f"ERROR: api_calculate_gross_to_net - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the calculation."
            )

# @router.post("/net-to-gross", tags=["Calculations"])
# async def api_calculate_net_to_gross():
#     """ Calculates Gross income based on desired Net income (Not Implemented). """
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Net to Gross calculation not implemented yet.")