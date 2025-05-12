# core/__init__.py

# This file marks 'core' as a Python package.

# Import key components from submodules to make them
# directly accessible at the package level.
from .calculator import calculate_gross_to_net
from .models import GrossNetInput, GrossNetResult, InsuranceBreakdown
from . import constants

# Import custom exceptions to make them available at the package level
from .exceptions import (
    CoreCalculationError,
    InvalidRegionError,
    InvalidInputDataError,
    CalculationLogicError,
    NegativeGrossIncomeError,
    NegativeDependentsError,
    InsuranceCalculationError,
    PITCalculationError,
    MissingConfigurationError
)

# Define what gets imported when someone does 'from core import *'
# (Though wildcard imports are generally discouraged)
__all__ = [
    "calculate_gross_to_net",
    "GrossNetInput",
    "GrossNetResult",
    "InsuranceBreakdown",
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
]

# You could also define a package-level version here if desired
# __version__ = "0.1.1" # Example version bump
