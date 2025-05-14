# core/__init__.py

# This file marks 'core' as a Python package.

# Import key components from submodules to make them
# directly accessible at the package level.
from .calculator import calculate_gross_to_net
from .models import (
    GrossNetInput,
    GrossNetResult,
    InsuranceBreakdown,
    SavedCalculationCreate,
    SavedCalculationUpdate,
    SavedCalculationResponse,
    SavedCalculationListResponse,
    SavedCalculationDB,  # SQLAlchemy model
)
from . import constants
from .exceptions import (
    CoreCalculationError,
    InvalidRegionError,
    InvalidInputDataError,
    CalculationLogicError,
    NegativeGrossIncomeError,
    NegativeDependentsError,
    InsuranceCalculationError,
    PITCalculationError,
    MissingConfigurationError,
)
from .database import Base, engine, SessionLocal, get_db, create_db_and_tables

# Explicitly import the crud_saved_calculations module to make it available
# when 'from core import crud_saved_calculations' is used.
from . import crud_saved_calculations

# Define what gets imported when someone does 'from core import *'
# (Though wildcard imports are generally discouraged)
__all__ = [
    "calculate_gross_to_net",
    "GrossNetInput",
    "GrossNetResult",
    "InsuranceBreakdown",
    "SavedCalculationCreate",
    "SavedCalculationUpdate",
    "SavedCalculationResponse",
    "SavedCalculationListResponse",
    "SavedCalculationDB",
    "constants",
    "CoreCalculationError",
    "InvalidRegionError",
    "InvalidInputDataError",
    "CalculationLogicError",
    "NegativeGrossIncomeError",
    "NegativeDependentsError",
    "InsuranceCalculationError",
    "PITCalculationError",
    "MissingConfigurationError",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "create_db_and_tables",
    "crud_saved_calculations",  # Add the module to __all__
]

# __version__ = "0.3.0" # Example version bump
