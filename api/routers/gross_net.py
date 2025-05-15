# api/routers/gross_net.py

import logging
import pandas as pd
import io
from typing import Any, list  # Added List for type annotations
import math  # Added to handle NaN values

from fastapi import APIRouter, Body, HTTPException, status, UploadFile, File

from core.calculator import calculate_gross_to_net
from core.models import (
    GrossNetInput,
    GrossNetResult,
    SavedCalculationDB,
)  # Using existing models
from core.exceptions import (
    CoreCalculationError,
    InvalidRegionError,
    InvalidInputDataError,
    NegativeGrossIncomeError,
    NegativeDependentsError,
    MissingConfigurationError,
)
import numpy as np  # ensure numpy is imported
import json


# Add a helper function to recursively replace NaN values with None.
def replace_nan_in_data(data):
    if isinstance(data, dict):
        return {k: replace_nan_in_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_nan_in_data(item) for item in data]
    elif isinstance(data, float) and np.isnan(data):
        return None
    else:
        return data


# Existing dummy function for saving a single calculation
def create_saved_calculation(calculation: GrossNetInput) -> dict:
    # Dummy implementation; replace with actual DB logic.
    saved = calculation.dict()
    saved["id"] = 1  # In a real implementation, the DB would assign an ID.
    return saved


logger = logging.getLogger(__name__)
router = APIRouter()


def clean_nan(results):
    return [
        {
            k: (None if (isinstance(v, float) and np.isnan(v)) else v)
            for k, v in row.items()
        }
        for row in results
    ]


API_EXPECTED_COLUMNS = {
    "gross": "GrossIncome",
    "dependents": "Dependents",
    "region": "Region",
}


@router.post(
    "/gross-to-net",
    response_model=GrossNetResult,
    summary="Calculate Net Income from Gross Income (Single Record)",
    description=(
        "Calculates Vietnamese Net income, PIT, and insurance contributions "
        "based on a single set of Gross Income, Number of Dependents, and Region "
        "for April 2025 regulations."
    ),
    tags=["Calculations"],
)
async def api_calculate_gross_to_net_single(
    input_data: GrossNetInput = Body(  # noqa: B008
        ...,
        examples={
            "Basic Case (Region 1, 1 Dependent)": {
                "summary": "30M Gross, 1 Dependent, R1",
                "description": "A standard calculation example.",
                "value": {"gross_income": 30000000, "num_dependents": 1, "region": 1},
            },
        },
    ),
):
    logger.info(
        f"Received request for /gross-to-net (single): {input_data.model_dump_json(exclude_none=True)}"
    )
    try:
        result = calculate_gross_to_net(input_data)
        logger.info(
            f"Single calculation successful for input: {input_data.model_dump_json(exclude_none=True)}"
        )
        return result
    except (
        InvalidRegionError,
        NegativeGrossIncomeError,
        NegativeDependentsError,
        InvalidInputDataError,
    ) as e:
        logger.warning(
            f"Input validation error for /gross-to-net (single) "
            f"({type(e).__name__}): {str(e)} - Input: {input_data.model_dump_json(exclude_none=True)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except MissingConfigurationError as e:
        logger.error(
            f"Configuration error during /gross-to-net (single) calculation: {str(e)} - Input: {input_data.model_dump_json(exclude_none=True)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal configuration error: {str(e)}",
        ) from e
    except CoreCalculationError as e:
        logger.error(
            f"Core calculation error for /gross-to-net (single): {str(e)} - Input: {input_data.model_dump_json(exclude_none=True)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error during /gross-to-net (single) calculation: {str(e)} - Input: {input_data.model_dump_json(exclude_none=True)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred while processing the calculation.",
        ) from e


@router.post(
    "/batch-excel-upload",
    summary="Calculate Net Income from Uploaded Excel File (Batch)",
    description=(
        "Upload an Excel file (.xlsx, .xls) with columns for GrossIncome, Dependents, and Region. "
        "The API will process each row and return the calculated results along with original data."
    ),
    response_model=list[dict[str, Any]],  # Changed List to list, Dict to dict
    tags=["Calculations"],
)
async def api_calculate_batch_excel(
    file: UploadFile = File(
        ..., description="Excel file (.xlsx or .xls) for batch processing."
    ),
):
    logger.info(
        f"Received request for /batch-excel-upload. Filename: {file.filename}, Content-Type: {file.content_type}"
    )

    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an .xlsx or .xls file.",
        )

    try:
        contents = await file.read()
        excel_stream = io.BytesIO(contents)
        engine = "openpyxl" if file.filename.endswith(".xlsx") else None
        df_input = pd.read_excel(excel_stream, engine=engine)
        # Replace all NaN values with None across the entire dataframe
        df_input = df_input.replace({np.nan: None})
        logger.info(
            f"Successfully read Excel file. Shape: {df_input.shape}. Columns: {df_input.columns.tolist()}"
        )
    except Exception as e:
        logger.error(
            f"Error reading Excel file '{file.filename}': {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read or parse the Excel file. Ensure it is a valid .xlsx or .xls file. Error: {str(e)}",
        )
    finally:
        await file.close()

    missing_cols = [
        col for col in API_EXPECTED_COLUMNS.values() if col not in df_input.columns
    ]
    if missing_cols:
        msg = f"Missing required columns in Excel file: {', '.join(missing_cols)}. Expected: {list(API_EXPECTED_COLUMNS.values())}"
        logger.warning(f"Batch upload validation error: {msg}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    processed_results = []
    total_rows = len(df_input)
    logger.info(f"Starting batch processing for {total_rows} rows from Excel.")
    for index, row_data in df_input.iterrows():
        original_row_dict = (
            row_data.to_dict()
        )  # Temporary conversion; final cleaning will be applied later.
        calculation_status = "Success"
        error_message = ""
        result_object_dict = None

        try:
            gross = float(row_data[API_EXPECTED_COLUMNS["gross"]])
            deps = int(row_data[API_EXPECTED_COLUMNS["dependents"]])
            reg = int(row_data[API_EXPECTED_COLUMNS["region"]])

            if gross <= 0:
                raise NegativeGrossIncomeError(gross_income=gross)
            if deps < 0:
                raise NegativeDependentsError(num_dependents=deps)
            if reg not in [1, 2, 3, 4]:
                raise InvalidRegionError(region_value=reg)

            input_data = GrossNetInput(
                gross_income=gross, num_dependents=deps, region=reg
            )
            result = calculate_gross_to_net(input_data)
            result_object_dict = result.model_dump(exclude_none=True)

        except (
            InvalidRegionError,
            NegativeGrossIncomeError,
            NegativeDependentsError,
            InvalidInputDataError,
            MissingConfigurationError,
            CoreCalculationError,
        ) as e:
            calculation_status = "Error"
            error_message = f"{type(e).__name__}: {str(e)}"
            logger.warning(
                f"Error processing row {index + 1} from Excel: {error_message}"
            )
        except (TypeError, KeyError, ValueError) as e:
            calculation_status = "Error"
            error_message = f"Data Error in row {index + 1}: {type(e).__name__} - {str(e)}. Check column names and data types."
            logger.warning(
                f"Data error processing row {index + 1} from Excel: {error_message}"
            )
        except Exception as e:
            calculation_status = "Error"
            error_message = f"Unexpected Error in row {index + 1}: {str(e)}"
            logger.exception(f"Unexpected error processing row {index + 1} from Excel.")

        combined_row_result = {
            **original_row_dict,
            "CalculationStatus": calculation_status,
            "ErrorMessage": error_message,
        }
        if result_object_dict:
            combined_row_result.update(result_object_dict)
        processed_results.append(combined_row_result)

    # Apply recursive cleaning to remove any nan values from the final results.
    cleaned_results = [replace_nan_in_data(result) for result in processed_results]
    logger.info(
        f"Batch processing completed. Processed {len(cleaned_results)} rows after cleaning NaN."
    )
    return cleaned_results


@router.post("/save")  # Removed response_model parameter
async def save_calculation(calculation: GrossNetInput):  # Using GrossNetInput as input
    try:
        saved = create_saved_calculation(calculation)
        return saved
    except Exception as e:
        logging.error(f"Error saving calculation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not create the saved calculation record. {e}",
        )


@router.post("/save-batch")
async def save_batch_calculations(calculations: list[GrossNetInput]):
    try:
        saved_list = []
        for calc in calculations:
            saved = create_saved_calculation(calc)
            saved_list.append(saved)
        return {"saved_calculations": saved_list}
    except Exception as e:
        logging.error(f"Error saving batch calculations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not create the saved batch calculation records. {e}",
        )
