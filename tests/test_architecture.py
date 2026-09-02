import ast
from pathlib import Path

DOMAIN_ROOT = Path("src/careloop/domain")
AGENT_RUNTIME_ROOT = Path("src/careloop/agent_runtime")
PLUGIN_RUNTIME_ROOT = Path("src/careloop/plugin_runtime")
RUNTIME_STORAGE_ROOT = Path("src/careloop/runtime_storage")
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


def test_agent_runtime_contracts_have_no_adapter_or_outer_layer_dependencies() -> None:
    forbidden = CORE_FORBIDDEN_IMPORT_ROOTS | {
        "careloop.application",
        "careloop.evaluation",
        "careloop.presentation",
        "careloop.reporting",
        "careloop.safety",
        "careloop.plugin_runtime",
        "openai",
        "pydantic_ai",
        "sqlalchemy",
    }
    imported_modules = _imported_modules(AGENT_RUNTIME_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )


def test_plugin_runtime_is_removable_and_has_no_outer_or_network_dependency() -> None:
    forbidden = CORE_FORBIDDEN_IMPORT_ROOTS | {
        "careloop.application",
        "careloop.cli",
        "careloop.evaluation",
        "careloop.presentation",
        "careloop.reporting",
        "careloop.safety",
        "http",
        "openai",
        "pydantic_ai",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    imported_modules = _imported_modules(PLUGIN_RUNTIME_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )


def test_runtime_storage_is_removable_and_has_no_outer_dependency() -> None:
    forbidden = CORE_FORBIDDEN_IMPORT_ROOTS | {
        "careloop.application",
        "careloop.cli",
        "careloop.evaluation",
        "careloop.plugin_runtime",
        "careloop.presentation",
        "careloop.reporting",
        "careloop.safety",
        "http",
        "openai",
        "pydantic_ai",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    imported_modules = _imported_modules(RUNTIME_STORAGE_ROOT)

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )


def test_m10_application_has_no_cli_ui_gold_provider_network_or_clock_logic() -> None:
    source_path = APPLICATION_ROOT / "synthetic_turn.py"
    imported_modules = _imported_modules(source_path.parent)
    forbidden = {
        "careloop.cli",
        "careloop.plugin_runtime",
        "careloop.presentation",
        "benchmarks",
        "gold",
        "httpx",
        "openai",
        "requests",
        "socket",
        "sqlalchemy",
        "urllib",
    }

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )
    source = source_path.read_text(encoding="utf-8").casefold()
    assert "datetime.now" not in source
    assert "date.today" not in source
    assert "benchmarks/gold" not in source
    assert "synthetic_turn" not in (APPLICATION_ROOT / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "synthetic_turn" not in Path("src/careloop/cli.py").read_text(
        encoding="utf-8"
    )


def test_m11_review_resolution_is_removable_and_has_no_outer_logic() -> None:
    source_path = APPLICATION_ROOT / "synthetic_review.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        "careloop.cli",
        "careloop.evaluation",
        "careloop.plugin_runtime",
        "careloop.presentation",
        "careloop.process",
        "careloop.reporting",
        "careloop.safety",
        "benchmarks",
        "gold",
        "httpx",
        "openai",
        "requests",
        "socket",
        "sqlalchemy",
        "urllib",
    }

    assert all(
        not any(module == root or module.startswith(f"{root}.") for root in forbidden)
        for module in imported_modules
    )
    source = source_path.read_text(encoding="utf-8").casefold()
    assert "datetime.now" not in source
    assert "date.today" not in source
    assert "random" not in source
    assert "synthetic_review" not in (APPLICATION_ROOT / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "synthetic_review" not in Path("src/careloop/cli.py").read_text(
        encoding="utf-8"
    )


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
