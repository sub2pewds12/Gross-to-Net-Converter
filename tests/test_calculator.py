# tests/test_calculator.py

import pytest

# import pandas as pd  # Uncomment if using pandas to read test data
# from pathlib import Path
from core.calculator import calculate_gross_to_net
from core.models import GrossNetInput, GrossNetResult


def test_basic_gross_to_net_r1_1dep():
    input_data = GrossNetInput(gross_income=30_000_000, num_dependents=1, region=1)
    result = calculate_gross_to_net(input_data)

    assert result.net_income == 25_882_500
    assert result.personal_income_tax == 967_500
    assert result.total_insurance_contribution == 3_150_000
    assert result.taxable_income == 11_450_000
    assert result.pre_tax_income == 26_850_000
    assert result.insurance_breakdown.social_insurance == 2_400_000
    assert result.insurance_breakdown.health_insurance == 450_000
    assert result.insurance_breakdown.unemployment_insurance == 300_000


def test_lower_income_no_dependents_r1():
    input_data = GrossNetInput(gross_income=20_000_000, num_dependents=0, region=1)
    result = calculate_gross_to_net(input_data)

    assert result.net_income == 17_460_000
    assert result.personal_income_tax == 440_000
    assert result.total_insurance_contribution == 2_100_000
    assert result.taxable_income == 6_900_000


def test_high_income_with_dependents_r1():
    input_data = GrossNetInput(gross_income=100_000_000, num_dependents=2, region=1)
    result = calculate_gross_to_net(input_data)

    assert result.insurance_breakdown.social_insurance == 3_744_000
    assert result.insurance_breakdown.health_insurance == 702_000
    assert result.insurance_breakdown.unemployment_insurance == 992_000
    assert result.total_insurance_contribution == 5_438_000
    assert result.taxable_income == 74_762_000
    assert result.personal_income_tax == 16_578_600
    assert result.net_income == 77_983_400


def test_region_4_minimum_wage_level():
    input_data = GrossNetInput(gross_income=4_000_000, num_dependents=0, region=4)
    result = calculate_gross_to_net(input_data)

    assert result.net_income == 3_580_000
    assert result.personal_income_tax == 0
    assert result.total_insurance_contribution == 420_000
    assert result.taxable_income == 0


def test_invalid_region_raises_error():
    input_data = GrossNetInput(gross_income=10_000_000, num_dependents=0, region=5)
    with pytest.raises(ValueError, match="Invalid region: 5"):
        calculate_gross_to_net(input_data)


# @pytest.mark.skip(reason="Excel test data file not implemented/available")
# def test_gross_to_net_from_excel():
#     data_file = Path(__file__).parent / "data/data_test_gross_net.xlsx"
#     if not data_file.exists():
#         pytest.skip("Test data file not found")
#
#     df = pd.read_excel(data_file)
#
#     for index, row in df.iterrows():
#         input_data = GrossNetInput(
#             gross_income=row['GrossIncome'],
#             num_dependents=row['Dependents'],
#             region=row['Region']
#         )
#         result = calculate_gross_to_net(input_data)
#
#         assert result.net_income == pytest.approx(row['ExpectedNetIncome'])
#         assert result.personal_income_tax == pytest.approx(row['ExpectedPIT'])
