from pathlib import Path

from apps.api.app.main import app

RUNTIME_ROOTS = (Path("apps/api"), Path("core/vericlose"))
FORBIDDEN_IMPORTS = ("synthetic.truth", "evaluation.truth")


def test_runtime_does_not_import_hidden_truth() -> None:
    violations: list[str] = []

    for root in RUNTIME_ROOTS:
        for path in root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_IMPORTS:
                if forbidden in source:
                    violations.append(f"{path}: imports or references {forbidden}")

    assert violations == []


def test_runtime_api_does_not_expose_truth_routes() -> None:
    paths = {
        path.lower()
        for route in app.routes
        if isinstance((path := getattr(route, "path", None)), str)
    }
    assert all("truth" not in path and "ground_truth" not in path for path in paths)
