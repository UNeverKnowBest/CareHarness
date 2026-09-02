# Agent Runtime Contract

Contract status: **FROZEN through Milestone 11**

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

## Milestone 9 implemented boundary

M9 implements local manifest discovery only for the exact entry-point group
`careloop.plugins.v1`. `PluginAllowlistV1` pins each approved entry-point
name/value and plugin ID/version. Discovery checks those strings before load,
validates the returned `PluginManifestV1`, rejects missing dependencies and
cycles, and returns a stable dependency-before-dependant catalog.
No plugin package is bundled or enabled by default.

`ProviderNeutralModelRuntime` invokes one injected `ModelPort`. The M9 tests use
a deterministic test adapter; there is no real provider adapter and no network
call. A correlated, identity-matching `ModelDraft` remains available only as
`quarantined_draft` and advances from `DRAFTING` to `CHECKING_DRAFT`. Provider
exceptions, invalid drafts, and request/provider/model mismatches produce a
stable `ModelRuntimeFailureCode`, emit `RUNTIME_FAILURE`, and transition to
`FAILED_CLOSED` without retaining draft text or exception details.

Input routing, output-guard execution, bounded rewrite, review/release logic,
append-only storage and API endpoints remain deferred. Complete session
orchestration remains deferred. M9 adds no CLI command and does not alter the offline evaluator,
replay, benchmark, generated evidence, or reporting paths.

## Milestone 10 implemented contract

`RunSyntheticTurn` is the sole M10 application use case. It binds an immutable
`SessionConfig`, pre-routes the synthetic input with the existing safety
runtime, invokes the M9 model runtime only after support is allowed, and checks
every quarantined draft before release. `SyntheticTurnCommand`,
`ParticipantTurnView`, and `ResearchReviewTurnView` freeze the application and
audience boundaries. Participant data never contains drafts, gate decisions,
internal runtime events, or failure details.

An allowed gate result is persisted as `DRAFT_APPROVED` before an assistant
`Turn` is constructed. Rewrite decisions return to `DRAFTING` and permit at
most two new attempts. Hold or guidance suppression enters
`AWAITING_HUMAN_REVIEW`; M10 does not implement reviewer decisions. Critical
input, resource, model, gate, or ledger failure exposes no ordinary response
and records `RUNTIME_FAILURE` from the last persisted state whenever the ledger
remains writable.

`InMemoryRuntimeEventLedger` is append-only acceptance evidence. It enforces one
immutable session configuration, zero-based contiguous sequence, state-chain
continuity, and unique event IDs. Exact command retries are served from an
immutable in-process result projection; conflicting reuse of a request ID is
rejected. This is neither durable persistence nor a multi-process idempotency
claim.

## Milestone 11 implemented contract

`ResolveSyntheticReview` resolves only the pre-release hold produced by M10. A
strict `SyntheticReviewCommand` carries one existing typed `ReviewDecision`, the
reviewed quarantined draft, an optional decision-appropriate assistant turn,
and explicit evidence references. The resolver binds a detached authoritative
draft snapshot from the M10 research-review result and accepts the command only
when its complete revalidated draft equals that snapshot, the append-only ledger
is in `AWAITING_HUMAN_REVIEW`, and the last held event matches the draft identity.

Approval releases exactly the reviewed draft text; replacement releases the
explicit reviewer-supplied synthetic replacement; handoff and rejection close
the session without output. In every release path, the matching `REVIEW_*`
event is appended before the participant projection receives a turn. A failed
append releases nothing and attempts the existing `RUNTIME_FAILURE` transition.

Participant and research-review resolution projections are distinct. Draft,
decision evidence, runtime event, and failure category remain research-review
only. Exact local retries are idempotent and conflicting reuse rejects. M11
adds no reviewer queue, identity/authentication, durable decision table,
endpoint, staffed response, session-close evaluation, or claim that human
approval establishes model or clinical safety.
