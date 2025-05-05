from pydantic import BaseModel, Field, model_validator
from typing import Optional


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
                    "description": "Calculate for 30M VND Gross, 1 Dependent, Region 1.",
                    "value": {
                        "gross_income": 30000000,
                        "num_dependents": 1,
                        "region": 1,
                    },
                },
                {
                    "summary": "No Dependents Example",
                    "description": "Calculate for 20M VND Gross, 0 Dependents, Region 1.",
                    "value": {
                        "gross_income": 20000000,
                        "num_dependents": 0,
                        "region": 1,
                    },
                },
            ]
        }
    }


class InsuranceBreakdown(BaseModel):
    """Breakdown of calculated insurance contributions (employee share)."""

    social_insurance: float = Field(..., description="BHXH contribution in VND")
    health_insurance: float = Field(..., description="BHYT contribution in VND")
    unemployment_insurance: float = Field(..., description="BHTN contribution in VND")
    total: float = Field(
        ..., description="Total employee insurance contribution in VND"
    )


class GrossNetResult(BaseModel):
    """Output data for Gross to Net calculation."""

    gross_income: float = Field(..., description="Original Gross Income in VND")
    net_income: float = Field(
        ..., description="Calculated Net Income (Take-home pay) in VND"
    )
    personal_income_tax: float = Field(
        ..., description="Calculated Personal Income Tax (PIT) in VND"
    )
    total_insurance_contribution: float = Field(
        ..., description="Total employee insurance contribution in VND"
    )
    insurance_breakdown: InsuranceBreakdown = Field(
        ..., description="Detailed insurance breakdown"
    )
    taxable_income: float = Field(
        ..., description="Income subject to PIT calculation in VND"
    )
    pre_tax_income: float = Field(
        ..., description="Income after insurance but before allowances in VND"
    )
