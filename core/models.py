# core/models.py

from pydantic import BaseModel, Field
from typing import Optional, List  # Keep List for Pydantic schemas
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func  # For default datetime

from .database import Base  # Import Base from your database.py


# --- SQLAlchemy Model for Saved Calculations ---
class SavedCalculationDB(Base):
    __tablename__ = "saved_calculations"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    calculation_name: Optional[str] = Column(
        String(255), index=True, nullable=True
    )  # User-defined name, added length

    # Input fields
    gross_income: float = Column(Float, nullable=False)
    num_dependents: int = Column(Integer, nullable=False)
    region: int = Column(Integer, nullable=False)

    # Output fields from calculation
    net_income: float = Column(Float, nullable=False)
    personal_income_tax: float = Column(Float, nullable=False)
    total_insurance_contribution: float = Column(Float, nullable=False)
    # Potentially store insurance breakdown as JSON if needed, or separate table for more detail
    # For simplicity, we'll assume the main results are stored.

    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --- Pydantic Schemas for API Input/Output (Gross-to-Net Calculator) ---
class GrossNetInput(BaseModel):
    """Input data for Gross to Net calculation."""

    gross_income: float = Field(..., gt=0, description="Gross monthly income in VND")
    num_dependents: int = Field(
        ..., ge=0, description="Number of registered dependents"
    )
    region: int = Field(..., ge=1, le=4, description="Region (1, 2, 3, or 4)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Basic Example",
                    "value": {
                        "gross_income": 30000000,
                        "num_dependents": 1,
                        "region": 1,
                    },
                }
            ]
        }
    }


class InsuranceBreakdown(BaseModel):
    """Breakdown of calculated insurance contributions (employee share)."""

    social_insurance: float
    health_insurance: float
    unemployment_insurance: float
    total: float


class GrossNetResult(BaseModel):
    """Output data for Gross to Net calculation."""

    gross_income: float
    net_income: float
    personal_income_tax: float
    total_insurance_contribution: float
    insurance_breakdown: InsuranceBreakdown
    taxable_income: float
    pre_tax_income: float


# --- Pydantic Schemas for CRUD Operations on Saved Calculations ---


# Schema for creating a new saved calculation (input to API)
class SavedCalculationCreate(BaseModel):
    calculation_name: Optional[str] = Field(None, max_length=255)
    gross_income: float = Field(..., gt=0)
    num_dependents: int = Field(..., ge=0)
    region: int = Field(..., ge=1, le=4)
    # Results are typically calculated and then stored, so they might not be in create schema
    # Or, if you save pre-calculated results:
    net_income: float
    personal_income_tax: float
    total_insurance_contribution: float


# Schema for updating an existing saved calculation (input to API)
# Typically only allows updating mutable fields like 'calculation_name'
class SavedCalculationUpdate(BaseModel):
    calculation_name: Optional[str] = Field(None, max_length=255)
    # You might allow updating inputs and re-calculating, or just the name.
    # For simplicity, let's assume only name can be updated for now.
    # gross_income: Optional[float] = Field(None, gt=0)
    # num_dependents: Optional[int] = Field(None, ge=0)
    # region: Optional[int] = Field(None, ge=1, le=4)


# Schema for representing a saved calculation in API responses (output from API)
class SavedCalculationResponse(BaseModel):
    id: int
    calculation_name: Optional[str] = None
    gross_income: float
    num_dependents: int
    region: int
    net_income: float
    personal_income_tax: float
    total_insurance_contribution: float
    created_at: datetime
    updated_at: datetime

    model_config = {  # Replaced orm_mode with model_config for Pydantic v2
        "from_attributes": True
    }


# Schema for a list of saved calculations in API responses
class SavedCalculationListResponse(BaseModel):
    items: List[SavedCalculationResponse]
    total: int
    skip: Optional[int] = None
    limit: Optional[int] = None
