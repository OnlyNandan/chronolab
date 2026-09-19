import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from unit_conversion import standardize  # noqa: E402


def test_hba1c_percent_passthrough():
    value, unit, converted = standardize("HbA1c", 7.5, "%")
    assert value == 7.5
    assert unit == "%"
    assert converted is False


def test_hba1c_mmol_mol_converts_to_percent():
    # IFCC 58 mmol/mol == NGSP ~7.5%
    value, unit, converted = standardize("HbA1c", 58, "mmol/mol")
    assert round(value, 1) == 7.5
    assert unit == "%"
    assert converted is True


def test_glucose_mgdl_passthrough():
    value, unit, converted = standardize("Fasting Glucose", 95, "mg/dL")
    assert value == 95
    assert unit == "mg/dL"
    assert converted is False


def test_glucose_mmol_l_converts_to_mgdl():
    # 5.5 mmol/L ~= 99.1 mg/dL
    value, unit, converted = standardize("Fasting Glucose", 5.5, "mmol/L")
    assert round(value, 1) == 99.1
    assert unit == "mg/dL"
    assert converted is True


def test_cholesterol_mmol_l_converts_to_mgdl():
    # 5.0 mmol/L ~= 193.35 mg/dL
    value, unit, converted = standardize("Total Cholesterol", 5.0, "mmol/L")
    assert round(value, 2) == 193.35
    assert unit == "mg/dL"
    assert converted is True


def test_ldl_cholesterol_uses_same_conversion():
    value, unit, converted = standardize("LDL Cholesterol", 3.0, "mmol/L")
    assert round(value, 2) == 116.01
    assert unit == "mg/dL"
    assert converted is True


def test_unknown_test_name_passthrough():
    value, unit, converted = standardize("Unknown Test", 1.0, "widgets")
    assert (value, unit, converted) == (1.0, "widgets", False)


def test_case_insensitive_unit_matching():
    value, unit, converted = standardize("HbA1c", 58, "MMOL/MOL")
    assert converted is True
