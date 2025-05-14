# api/routers/saved_calculations_router.py

import logging
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
import pandas as pd
import io

# Import core components
# Changed how CRUD functions are imported:
from core.crud_saved_calculations import (
    create_saved_calculation,
    get_all_saved_calculations,
    get_saved_calculation,
    update_saved_calculation,
    delete_saved_calculation,
    count_saved_calculations,
)
from core import models  # models can still be imported like this
from core import database  # database can still be imported like this
from core.models import (  # Pydantic schemas are fine to import like this
    SavedCalculationCreate,
    SavedCalculationUpdate,
    SavedCalculationResponse,
    SavedCalculationListResponse,
)
from core.exceptions import (  # Custom exceptions
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
router = APIRouter(prefix="/saved-calculations", tags=["Saved Calculations"])

API_EXPECTED_COLUMNS = {  # Assuming this was from your previous version for Excel upload
    "gross": "GrossIncome",
    "dependents": "Dependents",
    "region": "Region",
}


# --- CRUD Endpoints for Saved Calculations ---


@router.post(
    "/",
    response_model=models.SavedCalculationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Saved Calculation",
)
async def create_new_saved_calculation_endpoint(  # Renamed to avoid conflict if you import the function
    calculation_data: models.SavedCalculationCreate,
    db: Session = Depends(database.get_db),
):
    logger.info(
        f"Received request to create saved calculation: {calculation_data.model_dump_json(exclude_none=True)}"
    )
    try:
        # Use the directly imported function
        created_calculation = create_saved_calculation(
            db=db, calculation=calculation_data
        )
        logger.info(
            f"Successfully created saved calculation with ID: {created_calculation.id}"
        )
        return created_calculation
    except Exception as e:
        logger.error(f"Error creating saved calculation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create the saved calculation record.",
        ) from e


@router.get(
    "/",
    response_model=models.SavedCalculationListResponse,
    summary="List All Saved Calculations",
)
async def read_all_saved_calculations_endpoint(  # Renamed
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(
        100, ge=0, le=1000, description="Maximum number of records to return"
    ),
    db: Session = Depends(database.get_db),
):
    logger.info(
        f"Received request to list saved calculations with skip={skip}, limit={limit}"
    )
    try:
        calculations = get_all_saved_calculations(db, skip=skip, limit=limit)
        total_count = count_saved_calculations(db)
        logger.info(
            f"Retrieved {len(calculations)} saved calculations. Total count: {total_count}"
        )
        return SavedCalculationListResponse(
            items=calculations, total=total_count, skip=skip, limit=limit
        )
    except Exception as e:
        logger.error(f"Error retrieving saved calculations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve saved calculations.",
        ) from e


@router.get(
    "/{calculation_id}",
    response_model=models.SavedCalculationResponse,
    summary="Get a Specific Saved Calculation by ID",
)
async def read_specific_saved_calculation_endpoint(  # Renamed
    calculation_id: int, db: Session = Depends(database.get_db)
):
    logger.info(f"Received request to get saved calculation with ID: {calculation_id}")
    db_calculation = get_saved_calculation(db, calculation_id=calculation_id)
    if db_calculation is None:
        logger.warning(f"Saved calculation with ID {calculation_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved calculation with ID {calculation_id} not found",
        )
    logger.info(f"Retrieved saved calculation with ID: {calculation_id}")
    return db_calculation


@router.put(
    "/{calculation_id}",
    response_model=models.SavedCalculationResponse,
    summary="Update a Saved Calculation",
)
async def update_existing_saved_calculation_endpoint(  # Renamed
    calculation_id: int,
    calculation_update_data: models.SavedCalculationUpdate,
    db: Session = Depends(database.get_db),
):
    logger.info(
        f"Received request to update saved calculation ID {calculation_id} with data: {calculation_update_data.model_dump_json(exclude_none=True)}"
    )
    updated_calculation = update_saved_calculation(
        db=db, calculation_id=calculation_id, calculation_update=calculation_update_data
    )
    if updated_calculation is None:
        logger.warning(
            f"Saved calculation with ID {calculation_id} not found for update."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved calculation with ID {calculation_id} not found",
        )
    logger.info(f"Successfully updated saved calculation with ID: {calculation_id}")
    return updated_calculation


@router.delete(
    "/{calculation_id}",
    response_model=models.SavedCalculationResponse,
    summary="Delete a Saved Calculation",
)
async def delete_existing_saved_calculation_endpoint(  # Renamed
    calculation_id: int, db: Session = Depends(database.get_db)
):
    logger.info(
        f"Received request to delete saved calculation with ID: {calculation_id}"
    )
    deleted_calculation = delete_saved_calculation(db, calculation_id=calculation_id)
    if deleted_calculation is None:
        logger.warning(
            f"Saved calculation with ID {calculation_id} not found for deletion."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved calculation with ID {calculation_id} not found",
        )
    logger.info(f"Successfully deleted saved calculation with ID: {calculation_id}")
    return deleted_calculation


# Keep your existing api_calculate_gross_to_net_single and api_calculate_batch_excel endpoints here
# ... (ensure their imports are also correct if they use core components)
