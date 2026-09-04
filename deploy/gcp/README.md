# GCP Terraform template

This directory is a non-production research template for adult synthetic
role-play only. It does not deploy by default: `deploy_services=false` creates
the private network, regional Cloud SQL instance, ephemeral Memorystore,
least-privilege service accounts, and empty Secret Manager containers, but not
the Cloud Run API, Web service, or worker pool.

The template deliberately creates no `allUsers` invoker binding. A deployment
owner must supply an identity-aware ingress and an OIDC tenant, keep the local
synthetic identity disabled, and authorize only research users. The current Web
client is a local demonstration; a production OIDC browser flow and gateway are
deployment-owned prerequisites, not supplied here.

## Staged bootstrap

1. Create a dedicated GCP project and an encrypted, versioned GCS Terraform
   state bucket. Initialize with `terraform init -backend-config=...`; never put
   credentials in this repository or command history.
2. Copy `terraform.tfvars.example` outside the repository, replace every
   placeholder, keep `deploy_services=false`, and review `terraform plan`.
3. Apply the infrastructure stage only after explicit operator approval.
4. Add a secret version out of band for `database-url`, `redis-url`, and
   `oidc-public-key`. Secret values must never be passed as ordinary Terraform
   variables because Terraform state and plan files can retain them.
5. Build digest-pinned images. Build the Web image with the final restricted API
   origin as `NEXT_PUBLIC_API_BASE`; do not use a floating tag.
6. Set `deploy_services=true`, review the new plan, and apply only after the OIDC
   gateway, secret access, migrations, retention, and rollback owner are ready.
7. Run the authorized smoke and recovery checks in
   `docs/gcp_recovery_runbook.md`. Do not enter real-person or protected health
   information.

Terraform and gcloud were unavailable in the M17 development environment, so
no `init`, `validate`, `plan`, `apply`, cloud smoke test, or recovery exercise is
claimed. Static repository tests verify the intended resource and permission
boundaries. Provider schema and managed-service behavior must still be validated
in an approved disposable research project.
