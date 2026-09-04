# GCP Smoke and Recovery Runbook

This runbook applies only to an approved, disposable adult-synthetic research
deployment. It is not a clinical continuity plan, an emergency procedure, or a
claim of cloud resilience. No real-person or protected health information may
be used in any smoke or recovery exercise. Every cloud command requires
explicit operator approval, authenticated least-privilege access, a recorded
project ID, and a rollback owner.

## Preconditions

- Confirm the target is a dedicated non-production research project.
- Confirm local synthetic identity is disabled and the identity-aware gateway
  maps only `participant`, `reviewer`, and `admin` research roles.
- Confirm Cloud Run has no public `allUsers` invoker and uses digest-pinned
  images.
- Confirm the current Terraform plan, database backup, retention owner, secret
  versions, and maintenance window have been reviewed.
- Use only the fixed repository scenarios. The simulated human-review queue is not staffed care
  and does not contact clinicians, emergency services, family, authorities, or
  any other third party.

## Read-only smoke sequence

With explicit approval and cloud tooling available, record the exact project,
region, image digests, migration revision, and UTC test window. Then:

1. Run `terraform fmt -check -recursive` and `terraform validate` after an
   approved provider initialization.
2. Inspect Cloud Run API, Web, and worker-pool configuration. Verify restricted
   ingress, distinct service accounts, production environment, and disabled
   local identity.
3. Inspect Cloud SQL regional availability, private IP, deletion protection,
   backups, and point-in-time recovery. Do not write synthetic sessions yet.
4. Inspect Memorystore TLS, authentication, and private connectivity. Redis is
   not an authoritative data source.
5. Through the approved OIDC gateway, call liveness/readiness and create one
   uniquely named fixed synthetic session. Verify status-only SSE and one atomic
   complete answer. Never paste a token, draft, secret, or real-person text into
   evidence logs.
6. Exercise one fixed input-override case and one fixed output-hold case. Verify
   that neither exposes an ordinary assistant response and that reviewer-only
   evidence remains outside the participant projection.
7. Close the fixed session, compare the canonical report with the recorded
   session identity, and perform an audited whole-session purge when the test
   window ends.

## Redis loss exercise

PostgreSQL remains authoritative throughout this exercise. After explicit
approval, isolate or replace the ephemeral Redis instance while retaining the
database and Cloud Run revisions. Confirm committed runtime events and outbox
rows remain present. Restore Redis connectivity, republish the committed outbox,
and verify consumers deduplicate by event ID and sequence. Do not reconstruct
authoritative state from Redis and do not release a fallback response during
the outage.

## Cloud SQL restore exercise

Never restore over the authoritative instance during a validation exercise.
Restore to a new Cloud SQL instance at an explicitly selected recovery point,
attach no participant traffic, and run migration/schema and append-only event
integrity checks against the isolated copy. Compare session state, event
sequence, idempotency records, review-queue correlation, and unpublished outbox
rows. Any mismatch stops the exercise. Promotion or connection-string change
requires explicit operator approval and a separately reviewed Terraform plan.

## Held-session reconciliation

Query for durable sessions whose last event is `DRAFT_HELD_FOR_REVIEW` but which
have no correlated queue row. Create no participant answer. An identified
research operator may reconstruct only a reviewer-side queue item from the
authoritative held event and quarantined draft evidence, using a new audited
idempotency identity. If complete evidence is unavailable, retain the hold and
record a system failure; never guess draft, finding, resource, or reviewer data.

## Evidence and stop conditions

Record command, exit status, resource revision, and synthetic case identity.
Do not record credentials or raw quarantined content. Stop on an unexpected
public answer, role bypass, non-contiguous event sequence, missing PostgreSQL
evidence, secret exposure, cross-session cursor acceptance, or failed restore
comparison. These checks describe software controls only and do not establish
clinical validity, treatment effectiveness, crisis detection, staffed review,
real-world safety, or a recovery-time guarantee.
