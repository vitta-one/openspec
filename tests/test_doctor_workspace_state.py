"""Calendar calculations used by the doctor's weekly schedule."""

from datetime import date

import pytest

from vitta_one.doctor_workspace.state import _week_window


@pytest.mark.parametrize(
    ("today", "expected_start", "expected_end"),
    [
        (date(2026, 11, 18), date(2026, 11, 16), date(2026, 11, 22)),
        (date(2026, 11, 22), date(2026, 11, 16), date(2026, 11, 22)),
        (date(2027, 1, 1), date(2026, 12, 28), date(2027, 1, 3)),
    ],
)
def test_week_window_returns_monday_through_sunday(today, expected_start, expected_end):
    assert _week_window(today) == (expected_start, expected_end)
