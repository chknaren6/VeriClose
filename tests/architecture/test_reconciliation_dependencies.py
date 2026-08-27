"""Reconciliation may consume canonical events, never source-parser details."""

import ast
from pathlib import Path

RECONCILIATION_ROOT = Path("core/vericlose/reconciliation")
FORBIDDEN_IMPORT_PREFIXES = (
    "core.vericlose.adapters",
    "core.vericlose.ingestion",
    "pandas",
    "openpyxl",
)


def test_reconciliation_does_not_depend_on_source_adapters_or_file_parsers() -> None:
    violations: list[str] = []
    for path in RECONCILIATION_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        ]
        imported_modules.extend(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        for module in imported_modules:
            if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                violations.append(f"{path}: imports {module}")

    assert not violations, "\n".join(violations)
