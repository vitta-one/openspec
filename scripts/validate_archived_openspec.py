#!/usr/bin/env python3
"""Valida o snapshot OpenSpec acadêmico sem repovoar specs/ no repositório."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "archive" / "openspec-specs-2026-11-22"
CONFIG = ROOT / "openspec" / "config.yaml"
CLI = ROOT / "tools" / "openspec-validator" / "node_modules" / ".bin" / "openspec"


def main() -> int:
    files = sorted(SNAPSHOT.glob("*/spec.md"))
    if len(files) != 25:
        print(f"Snapshot incompleto: esperado 25, encontrado {len(files)}", file=sys.stderr)
        return 2
    if not CONFIG.is_file() or not CLI.is_file():
        print("Instale o validador: npm ci --prefix tools/openspec-validator --ignore-scripts --no-audit --no-fund", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="vitta-openspec-archive-") as work:
        root = Path(work) / "openspec"
        root.mkdir()
        shutil.copy2(CONFIG, root / "config.yaml")
        shutil.copytree(SNAPSHOT, root / "specs")
        (root / "changes").mkdir()
        print(f"Validando {len(files)} contratos arquivados em diretório temporário", flush=True)
        result = subprocess.run(
            [str(CLI.resolve()), "validate", "--all", "--strict", "--no-interactive"],
            cwd=work,
            check=False,
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
