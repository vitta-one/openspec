"""Filtering and status display rules for the persisted specialty directory."""

from vitta_one.professional_directory.state import (
    filter_specialty_rows,
    normalize_directory_page_size,
)


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


def test_professional_link_filter_uses_persisted_relationship_counts() -> None:
    rows = [
        {**_ROWS[0], "professional_count": 2},
        {**_ROWS[1], "professional_count": 0},
        {**_ROWS[2], "professional_count": 1},
    ]
    assert [row["id"] for row in filter_specialty_rows(
        rows, "", "all", "linked"
    )] == [1, 3]
    assert [row["id"] for row in filter_specialty_rows(
        rows, "", "all", "unlinked"
    )] == [2]
    assert [row["id"] for row in filter_specialty_rows(
        rows, "", "inactive", "linked"
    )] == [3]


def test_directory_page_size_accepts_only_supported_values() -> None:
    assert [normalize_directory_page_size(value) for value in ("10", "25", "50")] == [
        10, 25, 50,
    ]
    assert normalize_directory_page_size("0") is None
    assert normalize_directory_page_size("100") is None
    assert normalize_directory_page_size("invalid") is None
