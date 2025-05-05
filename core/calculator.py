import math
from . import constants as const
from .models import GrossNetInput, GrossNetResult, InsuranceBreakdown


def calculate_gross_to_net(data: GrossNetInput) -> GrossNetResult:
    """
    Calculates Net Income from Gross Income based on Vietnamese regulations (Apr 2025).

    Args:
        data: A GrossNetInput Pydantic model containing calculation inputs.

    Returns:
        A GrossNetResult Pydantic model containing the calculated results.

    Raises:
        ValueError: If the provided region is invalid.
    """
    gross_income = data.gross_income
    num_dependents = data.num_dependents
    region = data.region

    if region not in const.REGIONAL_MINIMUM_WAGES:
        raise ValueError(f"Invalid region: {region}. Must be 1, 2, 3, or 4.")
    regional_min_wage = const.REGIONAL_MINIMUM_WAGES[region]

    insurance_base_input = gross_income
    insurance_base = max(insurance_base_input, regional_min_wage)

    bhxh_bhyt_cap = const.BHXH_BHYT_MAX_BASE
    bhtn_cap = regional_min_wage * const.BHTN_CAP_MULTIPLIER

    salary_base_bhxh_bhyt = max(min(insurance_base, bhxh_bhyt_cap), regional_min_wage)
    salary_base_bhtn = max(min(insurance_base, bhtn_cap), regional_min_wage)

    bhxh = salary_base_bhxh_bhyt * const.RATE_SOCIAL_INSURANCE
    bhyt = salary_base_bhxh_bhyt * const.RATE_HEALTH_INSURANCE
    bhtn = salary_base_bhtn * const.RATE_UNEMPLOYMENT_INSURANCE
    total_insurance = bhxh + bhyt + bhtn

    insurance_breakdown = InsuranceBreakdown(
        social_insurance=round(bhxh),
        health_insurance=round(bhyt),
        unemployment_insurance=round(bhtn),
        total=round(total_insurance),
    )

    pre_tax_income = gross_income - total_insurance

    personal_allowance = const.PERSONAL_ALLOWANCE
    dependent_allowance_total = num_dependents * const.DEPENDENT_ALLOWANCE
    total_allowances = personal_allowance + dependent_allowance_total

    taxable_income = pre_tax_income - total_allowances
    taxable_income = max(0, taxable_income)

    pit = 0.0
    previous_limit = 0
    for bracket in const.PIT_BRACKETS:
        if taxable_income > previous_limit:
            taxable_at_current_rate = (
                min(taxable_income, bracket["limit"]) - previous_limit
            )
            pit += taxable_at_current_rate * bracket["rate"]
        else:
            break
        previous_limit = bracket["limit"]

    pit = max(0, round(pit))

    net_income = gross_income - total_insurance - pit

    return GrossNetResult(
        gross_income=round(gross_income),
        net_income=round(net_income),
        personal_income_tax=pit,
        total_insurance_contribution=insurance_breakdown.total,
        insurance_breakdown=insurance_breakdown,
        taxable_income=round(taxable_income),
        pre_tax_income=round(pre_tax_income),
    )
