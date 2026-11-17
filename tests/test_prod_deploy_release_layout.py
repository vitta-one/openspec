"""Regression checks for the production release directory lifecycle.

These are source-contract checks: an actual VPS deploy still requires a
separate, authorized operational smoke test and verified database readiness.
"""

from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/deploy/poll-prod.sh"


def test_venv_is_built_only_after_the_release_has_its_final_path():
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'as_app python3.12 -m venv "$WORK/.venv"' not in source
    assert 'as_app python3.12 -m venv "$RELEASE/.venv"' in source
    assert source.index('mv -T -- "$WORK" "$RELEASE"') < source.index(
        'as_app python3.12 -m venv "$RELEASE/.venv"'
    )


def test_release_marker_requires_valid_entrypoint_and_preflight():
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'release_usable() {' in source
    assert '"$(head -n 1 "$RELEASE/.venv/bin/alembic")" == "#!$RELEASE/.venv/bin/python"' in source
    assert 'as_app "$RELEASE/.venv/bin/alembic" --version' in source
    assert source.index('as_app "$RELEASE/.venv/bin/reflex" compile --dry') < source.index(
        'as_app touch "$RELEASE/.ready"'
    )


def test_invalid_release_is_preserved_and_live_release_is_protected():
    source = SCRIPT.read_text(encoding="utf-8")

    assert '"$RELEASE" != "$PREVIOUS"' in source
    assert '"$RELEASES/.invalid-' in source
    assert 'mv -T -- "$RELEASE" "$QUARANTINE"' in source
    assert 'as_app "$RELEASE/.venv/bin/alembic" current --check-heads' in source
    assert 'alembic upgrade head' not in source
