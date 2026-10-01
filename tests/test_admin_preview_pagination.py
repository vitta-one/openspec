"""Unit tests for local Administrator patient preview pagination helpers."""

import pytest

from vitta_one.admin_preview.state import (
    _filter_patient_rows,
    _patient_page_count,
    _patient_page_rows,
)


PATIENTS = [
    {"id": 1, "name": "Ana Souza", "cpf_masked": "***.***.***-10"},
    {"id": 2, "name": "Bruno Lima", "cpf_masked": "***.***.***-20"},
    {"id": 3, "name": "Carla Mendes", "cpf_masked": "***.***.***-30"},
    {"id": 4, "name": "Daniel Rocha", "cpf_masked": "***.***.***-40"},
    {"id": 5, "name": "Eduarda Alves", "cpf_masked": "***.***.***-50"},
]


def test_patient_filter_matches_name_and_masked_cpf() -> None:
    assert [row["id"] for row in _filter_patient_rows(PATIENTS, "bruno")] == [2]
    assert [row["id"] for row in _filter_patient_rows(PATIENTS, "-30")] == [3]
    assert _filter_patient_rows(PATIENTS, "  ANA  ")[0]["id"] == 1


def test_patient_filter_without_query_preserves_rows() -> None:
    assert _filter_patient_rows(PATIENTS, "") == PATIENTS
    assert _filter_patient_rows(PATIENTS, "   ") == PATIENTS


def test_patient_page_count_has_stable_empty_page_and_rejects_invalid_size() -> None:
    assert _patient_page_count(0, 2) == 1
    assert _patient_page_count(1, 2) == 1
    assert _patient_page_count(5, 2) == 3

    with pytest.raises(ValueError):
        _patient_page_count(5, 0)


def test_patient_page_rows_filters_then_paginates_and_clamps_page() -> None:
    assert [row["id"] for row in _patient_page_rows(PATIENTS, "", 1, 2)] == [1, 2]
    assert [row["id"] for row in _patient_page_rows(PATIENTS, "", 2, 2)] == [3, 4]
    assert [row["id"] for row in _patient_page_rows(PATIENTS, "", 99, 2)] == [5]
    assert [row["id"] for row in _patient_page_rows(PATIENTS, "", 0, 2)] == [1, 2]
    assert [row["id"] for row in _patient_page_rows(PATIENTS, "da", 1, 2)] == [4, 5]
