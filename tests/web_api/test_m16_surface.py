import json
from pathlib import Path


def test_nextjs_role_separated_bilingual_surface_is_present() -> None:
    package = json.loads(Path("web/package.json").read_text(encoding="utf-8"))
    assert package["scripts"]["build"] == "next build"
    assert package["scripts"]["test:e2e"] == "playwright test"
    assert "next" in package["dependencies"]
    assert "@playwright/test" in package["devDependencies"]

    required = {
        "web/app/[locale]/participant/page.tsx",
        "web/app/[locale]/reviewer/page.tsx",
        "web/app/[locale]/admin/page.tsx",
        "web/app/[locale]/layout.tsx",
        "web/app/globals.css",
        "web/e2e/roles.spec.ts",
        "web/playwright.config.ts",
    }
    assert all(Path(item).is_file() for item in required)

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for pattern in ("*.ts", "*.tsx")
        for path in Path("web").rglob(pattern)
        if "node_modules" not in path.parts
    )
    assert "Adult synthetic role-play research only" in source
    assert "仅限成人合成角色扮演研究" in source
    assert "not staffed care" in source
    assert "不会联系临床人员、急救服务、家人或政府部门" in source
    assert "EventSource" in source
    for prohibited in ("draft_text", "chain_of_thought", "risk_score"):
        assert prohibited not in source


def test_compose_health_seed_and_observability_contract() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    for service in ("api:", "web:", "worker:", "postgres:", "redis:"):
        assert service in compose
    assert compose.count("healthcheck:") >= 4
    assert "CARELOOP_ENVIRONMENT: development" in compose
    assert 'CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY: "true"' in compose
    assert "careloop-data" in compose

    api_dockerfile = Path("docker/api.Dockerfile").read_text(encoding="utf-8")
    web_dockerfile = Path("docker/web.Dockerfile").read_text(encoding="utf-8")
    assert "--locked" in api_dockerfile
    for required_runtime_input in ("benchmarks", "policies", "seeds"):
        assert f"COPY {required_runtime_input}" in api_dockerfile
    assert "npm ci" in web_dockerfile
    assert "USER" in api_dockerfile
    assert "USER" in web_dockerfile
    assert "careloop.web_api.worker.WorkerSettings" in compose
    assert '"arq", "--check"' in compose

    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")
    assert "web/node_modules" in dockerignore
    assert "web/.next" in dockerignore
    assert ".venv" in dockerignore

    seeds = json.loads(Path("seeds/scenarios.v1.json").read_text(encoding="utf-8"))
    assert seeds["contract_version"] == "v1"
    assert {item["locale"] for item in seeds["scenarios"]} == {"en-US", "zh-CN"}
    assert all(item["adult_synthetic_role_play"] for item in seeds["scenarios"])
    assert all("input_text" not in item for item in seeds["scenarios"])


def test_m16_adapter_is_removable_from_inner_layers() -> None:
    inner_roots = (
        "src/careloop/domain",
        "src/careloop/process",
        "src/careloop/safety",
        "src/careloop/evaluation",
        "src/careloop/application",
        "src/careloop/reporting",
        "src/careloop/agent_runtime",
        "src/careloop/supervision",
    )
    for root in inner_roots:
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in Path(root).rglob("*.py")
        )
        assert "careloop.web_api" not in source
        assert "fastapi" not in source


def test_web_source_is_tracked_separately_from_generated_node_outputs() -> None:
    ignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "web/node_modules/" in ignore
    assert "web/.next/" in ignore
    assert "web/test-results/" in ignore
    assert "web/*.tsbuildinfo" in ignore
    assert "!web/lib/" in ignore
    assert "!web/lib/**" in ignore
