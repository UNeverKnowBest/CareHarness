# Agent Runtime Contract

Contract status: **FROZEN for Milestone 8**

## Product and release boundary

The runtime is a local research demonstration over synthetic role-play data. It
does not diagnose, treat, screen, classify clinical risk, provide crisis care,
or replace a clinician or emergency service. It must not accept real patient
data. The user-facing description is "MI/CBT-informed supportive session", not
therapy or treatment.

The patient-shaped surface is operated by an admissions reviewer or researcher
who has selected a versioned synthetic persona. No raw model token or
quarantined draft crosses that surface. Status updates may be streamed, but a
reply is released atomically only after all required gates pass.

## Runtime flow

1. Create a session from `SessionConfig` and a versioned synthetic scenario.
2. Run input safety routing before any model adapter.
3. Suppress ordinary support flow when an override is active.
4. Hold every model response as a server-side `ModelDraft`.
5. Run deterministic policy and enabled output-guard plugins.
6. Permit at most two rewrite attempts. A third failed draft is held for review.
7. Release an allowed reply atomically or create a pre-release review task.
8. Send normal released turns to the post-session audit queue.
9. Evaluate the complete ordered trajectory when the session closes.
10. Derive a concise participant-facing report and an evidence-rich research
    review report from raw artifacts.

`SafetyDisposition` is system-routing vocabulary, not a label about a person's
health. `SYSTEM_FAILURE` and every critical plugin failure fail closed.

## HTTP surface frozen for future API implementation

Milestone 8 freezes names and intent but does not add a web dependency.

| Endpoint | Purpose |
|---|---|
| `POST /v1/demo-sessions` | Create a local synthetic session from scenario, locale, and plugin profile. |
| `POST /v1/demo-sessions/{id}/turns` | Submit one synthetic role-play turn with an idempotency key. |
| `GET /v1/demo-sessions/{id}` | Read only released replies and public state. |
| `GET /v1/demo-sessions/{id}/events` | Stream state-only SSE events; never raw model content. |
| `POST /v1/review-tasks/{id}/decisions` | Record one typed reviewer decision and evidence reference. |
| `POST /v1/demo-sessions/{id}/close` | Close the session and request trajectory evaluation. |
| `GET /v1/demo-sessions/{id}/reports/{audience}` | Read `participant` or `research_review` output. |
| `POST /v1/experiments` | Request a versioned synthetic matched-pair run. |

The API implementation must call application services only. It must use strict
request/response models, reject unknown fields, require idempotency for writes,
and return no internal draft from participant-scoped endpoints.

## Plugin contract

`PluginManifestV1` is discovered through an allowlisted Python entry point. It
freezes plugin identity, version, kind, capability names, configuration schema,
dependencies, default state, and failure mode. Duplicate or self-dependencies
are invalid. Model providers, input detectors, output guards, and resource
catalogs are always `critical_fail_closed`; optional reporting and integration
plugins may use `optional_isolated`.

Configuration toggles are resolved before session creation. A session records
the exact enabled plugin versions and cannot hot-swap them. Changing a profile
requires a new session so replay and experiment comparisons remain meaningful.

## Append-only event and storage contract

The future PostgreSQL schema uses these logical tables:

| Table | Role and invariant |
|---|---|
| `demo_sessions` | Current lifecycle projection and immutable scenario/profile references. |
| `session_turns` | Ordered synthetic input and released assistant turns. |
| `runtime_events` | Authoritative append-only transition ledger with monotonic per-session sequence. |
| `drafts` | Quarantined provider outputs; never participant-readable. |
| `draft_gate_results` | Evidence-linked gate decisions and rewrite count. |
| `review_tasks` | Pending or resolved pre-release and post-session audit work. |
| `review_decisions` | Append-only reviewer decisions; corrections append a superseding decision. |
| `artifact_provenance` | Model, prompt, scenario, plugin, and resource-registry identities. |
| `reports` | Immutable references to derived participant and research-review artifacts. |
| `experiment_runs` | Manifest and output references for synthetic matched-pair runs. |

`runtime_events`, `drafts`, `draft_gate_results`, `review_decisions`, and
`artifact_provenance` are insert-only through the application service. Database
time, request duration, and UI metadata do not participate in deterministic
replay identity. Generated numbers are always recomputed from raw artifacts.

Each `RuntimeEvent` contains exactly `contract_version`, `event_id`,
`session_id`, `sequence`, `event`, `state_before`, `state_after`,
`causation_id`, and `evidence_ids`. The schema validates the recorded
before/event/after tuple against the same pure transition table used by the
runtime. The persistence adapter must enforce uniqueness of
`(session_id, sequence)`; corrections append a new event and never rewrite an
existing one.

## Deferred implementation

FastAPI, PostgreSQL, SQLAlchemy, Alembic, cloud SDKs, React, Docker Compose,
authentication, FHIR, and model calls are not part of M8. Their future adapters
must depend inward on this provider-neutral contract. The existing evaluator,
replay, CLI, frozen benchmark, and public Day 1 schemas remain unchanged.
