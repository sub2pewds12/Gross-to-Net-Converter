# core/crud_saved_calculations.py

import logging
from sqlalchemy.orm import Session
from typing import List, Optional

# Import your SQLAlchemy model and Pydantic schemas
from .models import SavedCalculationDB, SavedCalculationCreate, SavedCalculationUpdate

# Get a logger instance
logger = logging.getLogger(__name__)

def get_saved_calculation(db: Session, calculation_id: int) -> Optional[SavedCalculationDB]:
    """
    Retrieves a single saved calculation by its ID from the database.
    """
    logger.debug(f"Attempting to retrieve saved calculation with id: {calculation_id}")
    calculation = db.query(SavedCalculationDB).filter(SavedCalculationDB.id == calculation_id).first()
    if calculation:
        logger.debug(f"Found saved calculation with id: {calculation_id}")
    else:
        logger.debug(f"No saved calculation found with id: {calculation_id}")
    return calculation

def get_all_saved_calculations(db: Session, skip: int = 0, limit: int = 100) -> List[SavedCalculationDB]:
    """
    Retrieves a list of saved calculations from the database with pagination.
    """
    logger.debug(f"Attempting to retrieve all saved calculations with skip: {skip}, limit: {limit}")
    calculations = db.query(SavedCalculationDB).order_by(SavedCalculationDB.created_at.desc()).offset(skip).limit(limit).all()
    logger.debug(f"Retrieved {len(calculations)} saved calculations.")
    return calculations

def create_saved_calculation(db: Session, calculation: SavedCalculationCreate) -> SavedCalculationDB:
    """
    Creates a new saved calculation record in the database.
    The input 'calculation' is a Pydantic model (SavedCalculationCreate).
    """
    logger.info(f"Attempting to create new saved calculation: {calculation.model_dump_json(exclude_none=True)}")
    # Create an instance of the SQLAlchemy model from the Pydantic model
    db_calculation = SavedCalculationDB(
        calculation_name=calculation.calculation_name,
        gross_income=calculation.gross_income,
        num_dependents=calculation.num_dependents,
        region=calculation.region,
        net_income=calculation.net_income,
        personal_income_tax=calculation.personal_income_tax,
        total_insurance_contribution=calculation.total_insurance_contribution
        # created_at and updated_at will use server_default from the model
    )
    try:
        db.add(db_calculation)
        db.commit()
        db.refresh(db_calculation) # Refresh to get ID and default values like created_at
        logger.info(f"Successfully created saved calculation with ID: {db_calculation.id}")
        return db_calculation
    except Exception as e:
        db.rollback() # Rollback in case of error
        logger.error(f"Error creating saved calculation in DB: {str(e)}", exc_info=True)
        raise # Re-raise the exception to be handled by the API layer

def update_saved_calculation(
    db: Session, calculation_id: int, calculation_update: SavedCalculationUpdate
) -> Optional[SavedCalculationDB]:
    """
    Updates an existing saved calculation in the database.
    Currently, this example only updates the 'calculation_name'.
    To update other fields, add them to the SavedCalculationUpdate Pydantic model
    and handle them here.
    """
    logger.info(f"Attempting to update saved calculation ID {calculation_id} with data: {calculation_update.model_dump_json(exclude_none=True)}")
    db_calculation = get_saved_calculation(db, calculation_id)

    if not db_calculation:
        logger.warning(f"No saved calculation found with ID {calculation_id} for update.")
        return None

    # Get fields to update from the Pydantic model, excluding unset values
    update_data = calculation_update.model_dump(exclude_unset=True)

    if not update_data:
        logger.info(f"No fields provided to update for calculation ID {calculation_id}.")
        return db_calculation # Return the existing object if no update data is provided

    for key, value in update_data.items():
        if hasattr(db_calculation, key):
            setattr(db_calculation, key, value)
            logger.debug(f"Updating field '{key}' for calculation ID {calculation_id}.")
        else:
            logger.warning(f"Field '{key}' not found in SavedCalculationDB model during update for ID {calculation_id}.")

    try:
        db.commit()
        db.refresh(db_calculation)
        logger.info(f"Successfully updated saved calculation with ID: {calculation_id}")
        return db_calculation
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating saved calculation ID {calculation_id} in DB: {str(e)}", exc_info=True)
        raise

def delete_saved_calculation(db: Session, calculation_id: int) -> Optional[SavedCalculationDB]:
    """
    Deletes a saved calculation by its ID from the database.
    Returns the deleted object or None if not found.
    """
    logger.info(f"Attempting to delete saved calculation with ID: {calculation_id}")
    db_calculation = get_saved_calculation(db, calculation_id)

    if not db_calculation:
        logger.warning(f"No saved calculation found with ID {calculation_id} for deletion.")
        return None

    try:
        db.delete(db_calculation)
        db.commit()
        logger.info(f"Successfully deleted saved calculation with ID: {calculation_id}")
        return db_calculation # Return the object that was deleted
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting saved calculation ID {calculation_id} from DB: {str(e)}", exc_info=True)
        raise

def count_saved_calculations(db: Session) -> int:
    """
    Counts the total number of saved calculations in the database.
    """
    logger.debug("Attempting to count all saved calculations.")
    count = db.query(SavedCalculationDB).count()
    logger.debug(f"Total saved calculations found: {count}")
    return count

