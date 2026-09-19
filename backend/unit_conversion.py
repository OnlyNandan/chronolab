"""
Deterministic unit conversions for canonical lab values.

These must never be delegated to an LLM (MIGRATION_PLAN.md Phase 2) — the model's
job is only to canonicalize test names and pass through raw_value/raw_unit; this
module decides the standardized value/unit and whether a conversion happened.
"""

STANDARD_UNITS = {
    "HbA1c": "%",
    "Fasting Glucose": "mg/dL",
    "Total Cholesterol": "mg/dL",
    "LDL Cholesterol": "mg/dL",
}

_GLUCOSE_TESTS = {"Fasting Glucose"}
_CHOLESTEROL_TESTS = {"Total Cholesterol", "LDL Cholesterol"}


def hba1c_mmol_mol_to_percent(value: float) -> float:
    return (value / 10.929) + 2.15


def mmol_l_to_glucose_mg_dl(value: float) -> float:
    return value * 18.0182


def mmol_l_to_cholesterol_mg_dl(value: float) -> float:
    return value * 38.67


def standardize(test_name_canonical: str, raw_value: float, raw_unit: str) -> tuple[float, str, bool]:
    """Returns (standardized_value, standardized_unit, unit_was_converted).

    Falls back to (raw_value, raw_unit, False) for anything outside the fixed
    vocabulary or an already-standard unit.
    """
    target_unit = STANDARD_UNITS.get(test_name_canonical)
    if target_unit is None:
        return raw_value, raw_unit, False

    unit = raw_unit.strip().lower()

    if test_name_canonical == "HbA1c":
        if unit == "mmol/mol":
            return round(hba1c_mmol_mol_to_percent(raw_value), 2), target_unit, True
        return raw_value, target_unit, False

    if test_name_canonical in _GLUCOSE_TESTS:
        if unit == "mmol/l":
            return round(mmol_l_to_glucose_mg_dl(raw_value), 2), target_unit, True
        return raw_value, target_unit, False

    if test_name_canonical in _CHOLESTEROL_TESTS:
        if unit == "mmol/l":
            return round(mmol_l_to_cholesterol_mg_dl(raw_value), 2), target_unit, True
        return raw_value, target_unit, False

    return raw_value, raw_unit, False
