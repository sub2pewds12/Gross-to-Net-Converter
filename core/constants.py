PERSONAL_ALLOWANCE = 11_000_000
DEPENDENT_ALLOWANCE = 4_400_000

RATE_SOCIAL_INSURANCE = 0.08
RATE_HEALTH_INSURANCE = 0.015
RATE_UNEMPLOYMENT_INSURANCE = 0.01

BASE_SALARY_FOR_CAPS = 2_340_000
BHXH_BHYT_CAP_MULTIPLIER = 20
BHTN_CAP_MULTIPLIER = 20

BHXH_BHYT_MAX_BASE = BASE_SALARY_FOR_CAPS * BHXH_BHYT_CAP_MULTIPLIER

REGIONAL_MINIMUM_WAGES = {
    1: 4_960_000,
    2: 4_410_000,
    3: 3_860_000,
    4: 3_450_000,
}

PIT_BRACKETS = [
    {"limit": 5_000_000, "rate": 0.05, "deduction": 0},
    {"limit": 10_000_000, "rate": 0.10, "deduction": 250_000},
    {"limit": 18_000_000, "rate": 0.15, "deduction": 750_000},
    {"limit": 32_000_000, "rate": 0.20, "deduction": 1_650_000},
    {"limit": 52_000_000, "rate": 0.25, "deduction": 3_250_000},
    {"limit": 80_000_000, "rate": 0.30, "deduction": 5_850_000},
    {"limit": float("inf"), "rate": 0.35, "deduction": 9_850_000},
]
