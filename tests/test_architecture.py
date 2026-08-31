import ast
from pathlib import Path

DOMAIN_ROOT = Path("src/careloop/domain")
PROCESS_ROOT = Path("src/careloop/process")
SAFETY_ROOT = Path("src/careloop/safety")
EVALUATION_ROOT = Path("src/careloop/evaluation")
APPLICATION_ROOT = Path("src/careloop/application")
PRESENTATION_ROOT = Path("src/careloop/presentation")
REPORTING_ROOT = Path("src/careloop/reporting")
FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "httpx",
    "requests",
    "streamlit",
    "tests",
    "typer",
}

CORE_FORBIDDEN_IMPORT_ROOTS = FORBIDDEN_IMPORT_ROOTS | {
    "benchmarks",
    "careloop.application",
    "careloop.cli",
    "gold",
}


def test_domain_has_no_presentation_test_or_network_dependencies() -> None:
    imported_roots: set[str] = set()

    for path in DOMAIN_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_process_has_no_presentation_application_gold_or_network_dependencies() -> None:
    imported_modules: set[str] = set()

    for path in PROCESS_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

    assert all(
        not any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for forbidden in CORE_FORBIDDEN_IMPORT_ROOTS
        )
        for module in imported_modules
    )


def test_safety_has_no_presentation_application_gold_or_network_dependencies() -> None:
    imported_modules: set[str] = set()

    for path in SAFETY_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

    assert all(
        not any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for forbidden in CORE_FORBIDDEN_IMPORT_ROOTS
        )
        for module in imported_modules
    )
    for path in SAFETY_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "datetime.now" not in source
        assert "date.today" not in source


def _imported_modules(root: Path) -> set[str]:
    imported_modules: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    return imported_modules


def test_evaluation_has_no_application_presentation_gold_or_network_dependency() -> (
    None
):
    forbidden = CORE_FORBIDDEN_IMPORT_ROOTS | {
        "careloop.presentation",
    }
    imported_modules = _imported_modules(EVALUATION_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )
    for path in EVALUATION_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "datetime.now" not in source
        assert "date.today" not in source


def test_application_and_core_do_not_depend_on_optional_presentation() -> None:
    imported_modules = _imported_modules(APPLICATION_ROOT)
    imported_modules.update(_imported_modules(EVALUATION_ROOT))

    assert all(
        module != "careloop.presentation"
        and not module.startswith("careloop.presentation.")
        for module in imported_modules
    )


def test_presentation_contains_no_policy_detector_or_evaluator_logic() -> None:
    forbidden = {
        "careloop.process",
        "careloop.safety",
        "benchmarks",
        "gold",
    }
    imported_modules = _imported_modules(PRESENTATION_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )


def test_reporting_contains_no_evaluator_policy_gold_cli_or_network_logic() -> None:
    forbidden = CORE_FORBIDDEN_IMPORT_ROOTS | {
        "careloop.application",
        "careloop.cli",
        "careloop.presentation",
        "careloop.process",
        "careloop.safety",
    }
    imported_modules = _imported_modules(REPORTING_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )
    for path in REPORTING_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8").casefold()
        assert "datetime.now" not in source
        assert "date.today" not in source
        assert "benchmarks/gold" not in source
        assert "benchmarks\\gold" not in source
        assert "load_gold_case" not in source
