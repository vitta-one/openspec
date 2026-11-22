"""Catch invalid unitless CSS gap values in the Reflex UI source."""

import re
from pathlib import Path


def test_reflex_gap_values_use_css_lengths() -> None:
    source_root = Path(__file__).parents[1] / "vitta_one"
    invalid_gap = re.compile(r"\bgap\s*=\s*(['\"])\d+\1")
    offenders = [
        f"{path.relative_to(source_root)}:{line_number}: {line.strip()}"
        for path in source_root.rglob("*.py")
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if invalid_gap.search(line)
    ]

    assert offenders == [], "Unitless CSS gaps are ignored by Chromium:\n" + "\n".join(offenders)
