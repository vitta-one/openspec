"""Pure queue projection tests for wait duration and safe filtering."""

from datetime import datetime, timedelta, timezone

from vitta_one.patient_queue.state import (
    filter_active_queue,
    format_queue_wait,
    queue_wait_minutes,
)


def test_wait_uses_persisted_timestamp_and_never_goes_negative() -> None:
    now = datetime(2026, 10, 31, 15, 0, tzinfo=timezone.utc)
    assert queue_wait_minutes(now - timedelta(minutes=125), now) == 125
    assert queue_wait_minutes(now + timedelta(minutes=2), now) == 0
    assert queue_wait_minutes(now.replace(tzinfo=None), now) == 0
    assert format_queue_wait(125) == "2h 05min"
    assert format_queue_wait(9) == "9 min"
    assert format_queue_wait(-4) == "0 min"


def test_filters_preserve_order_returned_by_clinical_service() -> None:
    rows = [
        {"id": 3, "patient_name": "João", "priority": "VERMELHO"},
        {"id": 2, "patient_name": "Maria", "priority": "AMARELO"},
        {"id": 1, "patient_name": "Joana", "priority": "VERDE"},
    ]
    assert [row["id"] for row in filter_active_queue(rows, "", "TODAS")] == [3, 2, 1]
    assert [row["id"] for row in filter_active_queue(rows, "jo", "TODAS")] == [3, 1]
    assert [row["id"] for row in filter_active_queue(rows, "", "VERDE")] == [1]
    assert filter_active_queue(rows, "não existe", "TODAS") == []
