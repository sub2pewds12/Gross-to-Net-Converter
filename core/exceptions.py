# core/exceptions.py

class CoreCalculationError(Exception):
    """Base class for custom errors in the core calculation logic."""
    def __init__(self, message="An error occurred during core calculation"):
        self.message = message
        super().__init__(self.message)

class InvalidRegionError(CoreCalculationError):
    """Raised when an invalid region is provided for calculation."""
    def __init__(self, region_value, message="Invalid region provided for calculation."):
        self.region_value = region_value
        self.message = f"{message} Received: '{region_value}'. Valid regions are 1, 2, 3, 4."
        super().__init__(self.message)

class InvalidInputDataError(CoreCalculationError):
    """Raised for other invalid input data not caught by Pydantic model validation
       but identified during the calculation process."""
    def __init__(self, field_name, field_value, reason="Invalid data provided for calculation."):
        self.field_name = field_name
        self.field_value = field_value
        self.reason = reason
        self.message = f"{reason} Field: '{field_name}', Value: '{field_value}'."
        super().__init__(self.message)

class CalculationLogicError(CoreCalculationError):
    """Raised for unexpected errors or issues within the calculation steps themselves."""
    def __init__(self, message="An unexpected error occurred within the calculation logic."):
        self.message = message
        super().__init__(self.message)

# --- More specific input data errors ---

class NegativeGrossIncomeError(InvalidInputDataError):
    """Raised when gross income is zero or negative."""
    def __init__(self, gross_income):
        super().__init__(
            field_name="gross_income",
            field_value=gross_income,
            reason="Gross income cannot be zero or negative."
        )

class NegativeDependentsError(InvalidInputDataError):
    """Raised when the number of dependents is negative."""
    def __init__(self, num_dependents):
        super().__init__(
            field_name="num_dependents",
            field_value=num_dependents,
            reason="Number of dependents cannot be negative."
        )

# --- More specific calculation logic errors ---

class InsuranceCalculationError(CalculationLogicError):
    """Raised if an error occurs during insurance contribution calculation."""
    def __init__(self, detail_message, original_exception=None):
        message = f"Error during insurance calculation: {detail_message}"
        if original_exception:
            message += f" (Caused by: {type(original_exception).__name__})"
        super().__init__(message)
        self.original_exception = original_exception

class PITCalculationError(CalculationLogicError):
    """Raised if an error occurs during Personal Income Tax calculation."""
    def __init__(self, detail_message, original_exception=None):
        message = f"Error during PIT calculation: {detail_message}"
        if original_exception:
            message += f" (Caused by: {type(original_exception).__name__})"
        super().__init__(message)
        self.original_exception = original_exception

class MissingConfigurationError(CoreCalculationError):
    """Raised if a required configuration or constant is missing."""
    def __init__(self, missing_item, message="Required configuration is missing."):
        self.missing_item = missing_item
        self.message = f"{message} Missing item: '{missing_item}'."
        super().__init__(self.message)

