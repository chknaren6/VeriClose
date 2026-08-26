from pathlib import Path

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
