import ast
from pathlib import Path

DOMAIN_ROOT = Path("core/vericlose/domain")
FORBIDDEN_ROOTS = {
    "fastapi",
    "duckdb",
    "polars",
    "pandas",
    "openai",
    "anthropic",
    "apps",
    "evaluation",
    "synthetic",
}


def test_domain_does_not_import_delivery_or_infrastructure() -> None:
    violations: list[str] = []

    for path in DOMAIN_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]

            for name in names:
                if name.split(".", maxsplit=1)[0] in FORBIDDEN_ROOTS:
                    violations.append(f"{path}:{node.lineno}: {name}")

    assert violations == []
