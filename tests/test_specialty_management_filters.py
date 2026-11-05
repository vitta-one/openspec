"""Filtering and status display rules for the persisted specialty directory."""

from vitta_one.professional_directory.state import filter_specialty_rows


_ROWS = [
    {"id": 1, "name": "Cardiologia", "is_active": True, "status_label": "Ativa"},
    {"id": 2, "name": "Clínica Médica", "is_active": True, "status_label": "Ativa"},
    {"id": 3, "name": "Dermatologia", "is_active": False, "status_label": "Inativa"},
]


def test_specialty_search_is_case_and_accent_insensitive() -> None:
    assert [row["id"] for row in filter_specialty_rows(_ROWS, "CLINICA", "all")] == [2]
    assert [row["id"] for row in filter_specialty_rows(_ROWS, " cardio ", "all")] == [1]


def test_specialty_search_and_status_filter_compose() -> None:
    assert [row["id"] for row in filter_specialty_rows(_ROWS, "derma", "inactive")] == [3]
    assert filter_specialty_rows(_ROWS, "derma", "active") == []
    assert [row["id"] for row in filter_specialty_rows(_ROWS, "", "active")] == [1, 2]


def test_reset_values_return_complete_persisted_projection() -> None:
    assert filter_specialty_rows(_ROWS, "", "all") == _ROWS
    assert filter_specialty_rows(_ROWS, "nada", "all") == []
    assert filter_specialty_rows([], "", "all") == []
