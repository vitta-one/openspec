"""Regression tests for the dedicated Reception patient registration form."""

import pytest

from vitta_one.patient_queue.state import (
    format_new_patient_phone_input,
    format_patient_cpf_input,
    validate_patient_registration_form,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),
        ("529", "529"),
        ("5299", "529.9"),
        ("5299822", "529.982.2"),
        ("5299822472", "529.982.247-2"),
        ("52998224725", "529.982.247-25"),
        ("529.982.247-25", "529.982.247-25"),
        ("529.982.247-25123", "529.982.247-25"),
    ],
)
def test_cpf_mask_formats_typing_and_paste(raw, expected):
    assert format_patient_cpf_input(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),
        ("11", "(11"),
        ("1198", "(11) 98"),
        ("1133334444", "(11) 3333-4444"),
        ("11988881234", "(11) 98888-1234"),
        ("(11) 98888-1234", "(11) 98888-1234"),
    ],
)
def test_optional_phone_mask_formats_partial_or_complete_input(raw, expected):
    assert format_new_patient_phone_input(raw) == expected


def test_registration_accepts_valid_masked_or_numeric_cpf_and_optional_phone():
    for cpf in ("52998224725", "529.982.247-25"):
        assert validate_patient_registration_form(
            "  Maria   da   Silva  ", cpf, ""
        ) == ("", "", "")
        assert validate_patient_registration_form(
            "Maria da Silva", cpf, "(11) 98888-1234"
        ) == ("", "", "")


@pytest.mark.parametrize(
    ("name", "cpf", "phone", "field"),
    [
        ("", "52998224725", "", "name"),
        (" \t ", "52998224725", "", "name"),
        ("N" * 161, "52998224725", "", "name"),
        ("Ana", "", "", "cpf"),
        ("Ana", "11111111111", "", "cpf"),
        ("Ana", "52998224726", "", "cpf"),
        ("Ana", "529abc98224725", "", "cpf"),
        ("Ana", "52998224725", "119", "phone"),
        ("Ana", "52998224725", "abc11988881234", "phone"),
    ],
)
def test_registration_reports_field_specific_errors(name, cpf, phone, field):
    errors = validate_patient_registration_form(name, cpf, phone)
    assert errors[{"name": 0, "cpf": 1, "phone": 2}[field]]
    assert sum(bool(error) for error in errors) == 1


def test_registration_reports_multiple_errors_without_discarding_form():
    errors = validate_patient_registration_form("  ", "123", "119")
    assert all(errors)
