"""WCAG contrast checks for the shared Vitta-One color tokens.

This protects the committed palette at build time. Browser QA separately checks
rendered components, including the select/dialog portals.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


def token(name: str) -> str:
    match = re.search(rf"^\s*--vitta-{re.escape(name)}:\s*(#[0-9a-fA-F]{{6}});", CSS, re.M)
    assert match is not None, f"Token CSS ausente: --vitta-{name}"
    return match.group(1)


def _linear(hex_pair: str) -> float:
    value = int(hex_pair, 16) / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    red, green, blue = (_linear(color[i:i+2]) for i in (1, 3, 5))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(front: str, back: str) -> float:
    high, low = sorted((luminance(front), luminance(back)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_operational_text_colors_meet_wcag_aa():
    for foreground, background in (
        ("text", "surface"),
        ("text-muted", "surface"),
        ("text-subtle", "surface"),
        ("primary", "surface"),
        ("info", "surface"),
        ("warning", "warning-soft"),
        ("success", "success-soft"),
        ("danger", "danger-soft"),
    ):
        ratio = contrast_ratio(token(foreground), token(background))
        assert ratio >= 4.5, f"{foreground} em {background}: {ratio:.2f}:1"


def test_active_navigation_and_control_borders():
    assert contrast_ratio("#ffffff", token("primary")) >= 4.5
    # Fields need a 3:1 visible boundary to remain distinguishable.
    assert contrast_ratio(token("contrast-border"), token("surface")) >= 3.0
    # Primary controls should not rely on pale placeholders.
    assert contrast_ratio("#475569", token("surface")) >= 4.5
    assert ".vitta-input::placeholder" in CSS
    assert ".rt-SelectContent" in CSS
    assert ".rt-DialogContent" in CSS
    assert ".vitta-task-tabs" in CSS


def test_clinic_address_textarea_has_single_visible_focus_ring():
    """The settings field has one Radix wrapper border and one keyboard focus ring."""
    wrapper = ".vitta-clinic-settings-form .rt-TextAreaRoot.vitta-textarea"

    def declarations(selector: str) -> str:
        match = re.search(re.escape(selector) + r"\s*\{([^{}]*)\}", CSS)
        assert match is not None, f"Regra CSS não encontrada: {selector}"
        return match.group(1)

    assert "min-height: 5.75rem;" in declarations(wrapper)
    assert "padding: 0;" in declarations(wrapper)
    inner = declarations(f"{wrapper} .rt-TextAreaInput")
    assert "border: 0 !important;" in inner
    assert "outline: none !important;" in inner
    focus = declarations(f"{wrapper}:focus-within")
    assert "outline: 2px solid var(--vitta-focus);" in focus
