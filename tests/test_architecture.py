import ast
from pathlib import Path

DOMAIN_ROOT = Path("src/careloop/domain")
FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "httpx",
    "requests",
    "streamlit",
    "tests",
    "typer",
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
