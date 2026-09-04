import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
DEPLOY = ROOT / "deploy" / "gcp"


def _all_terraform() -> str:
    files = sorted(DEPLOY.glob("*.tf"))
    assert {path.name for path in files} >= {
        "main.tf",
        "outputs.tf",
        "variables.tf",
        "versions.tf",
    }
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def test_gcp_template_has_required_services_and_no_public_invoker() -> None:
    terraform = _all_terraform()
    for resource in (
        'resource "google_cloud_run_v2_service" "api"',
        'resource "google_cloud_run_v2_service" "web"',
        'resource "google_cloud_run_v2_worker_pool" "worker"',
        'resource "google_sql_database_instance" "primary"',
        'resource "google_redis_instance" "ephemeral"',
        'resource "google_secret_manager_secret" "runtime"',
        'resource "google_service_account" "api"',
        'resource "google_service_account" "worker"',
    ):
        assert resource in terraform

    assert '"allUsers"' not in terraform
    assert re.search(
        r'name\s*=\s*"CARELOOP_ENVIRONMENT"\s+value\s*=\s*"production"',
        terraform,
    )
    assert re.search(
        r'name\s*=\s*"CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY"'
        r'\s+value\s*=\s*"false"',
        terraform,
    )


def test_postgres_is_authoritative_and_redis_is_ephemeral_hardened() -> None:
    terraform = _all_terraform()
    for phrase in (
        "deletion_protection = true",
        'availability_type = "REGIONAL"',
        "point_in_time_recovery_enabled = true",
        "ipv4_enabled    = false",
        'tier                    = "STANDARD_HA"',
        'transit_encryption_mode = "SERVER_AUTHENTICATION"',
        "auth_enabled            = true",
    ):
        assert phrase in terraform
    assert "redis" not in (DEPLOY / "outputs.tf").read_text(encoding="utf-8").casefold()


def test_template_uses_staged_secret_bootstrap_and_least_privilege_bindings() -> None:
    terraform = _all_terraform()
    variables = (DEPLOY / "variables.tf").read_text(encoding="utf-8")
    readme = (DEPLOY / "README.md").read_text(encoding="utf-8").casefold()

    assert 'variable "deploy_services"' in variables
    assert "default     = false" in variables
    assert "secretmanager.secretAccessor" in terraform
    assert "roles/owner" not in terraform
    assert "roles/editor" not in terraform
    assert "secret version" in readme
    assert "terraform state" in readme
    assert "does not deploy by default" in readme
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".terraform/" in ignore
    assert "*.tfstate" in ignore
    assert "*.tfplan" in ignore

    web_image = (ROOT / "docker" / "web.Dockerfile").read_text(encoding="utf-8")
    assert "ARG NEXT_PUBLIC_API_BASE" in web_image
    assert "ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE" in web_image


def test_recovery_and_smoke_runbooks_preserve_authoritative_boundaries() -> None:
    recovery = (
        (ROOT / "docs" / "gcp_recovery_runbook.md")
        .read_text(encoding="utf-8")
        .casefold()
    )
    for phrase in (
        "restore to a new cloud sql instance",
        "postgresql remains authoritative",
        "republish the committed outbox",
        "simulated human-review queue is not staffed care",
        "no real-person or protected health information",
        "requires explicit operator approval",
    ):
        assert phrase in recovery
