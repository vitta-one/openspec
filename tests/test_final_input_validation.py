"""Contract tests for form-friendly formatting and server-authoritative validation."""
import pytest

from vitta_one.patient_queue.service import (
    PatientValidationError,
    is_valid_cpf,
    normalize_patient_phone,
)
from vitta_one.patient_queue.state import format_patient_phone_input


@pytest.mark.parametrize("value", [
    "52998224725",
    "529.982.247-25",
    " 529.982.247-25 ",
])
def test_cpf_accepts_known_valid_numeric_or_masked_input(value):
    assert is_valid_cpf(value)


@pytest.mark.parametrize("value", [
    "", "11111111111", "5299822472", "52998224726",
    "529abc98224725", "<52998224725>", "529.982.247-2x",
])
def test_cpf_rejects_missing_invalid_and_injected_characters(value):
    assert not is_valid_cpf(value)


@pytest.mark.parametrize("value, expected", [
    ("11988881234", "11988881234"),
    ("(11) 98888-1234", "11988881234"),
    ("1133334444", "1133334444"),
    ("(11) 3333-4444", "1133334444"),
    ("", None),
])
def test_phone_normalizes_masked_digits_and_optional_empty(value, expected):
    assert normalize_patient_phone(value) == expected


@pytest.mark.parametrize("value", [
    "119888812", "119888812345", "abc11988881234",
    "(11) abc98888-1234", "119 98888@1234",
])
def test_phone_rejects_invalid_length_and_non_phone_characters(value):
    with pytest.raises(PatientValidationError):
        normalize_patient_phone(value)


@pytest.mark.parametrize("value, expected", [
    ("11988881234", "(11) 98888-1234"),
    ("1133334444", "(11) 3333-4444"),
    ("", ""),
    (None, ""),
])
def test_phone_edit_fields_show_normalized_brazilian_mask(value, expected):
    assert format_patient_phone_input(value) == expected
