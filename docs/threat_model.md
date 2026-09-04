# Agent Runtime Threat Model

Status: **FROZEN and implemented through the Milestone 16 research surface**

## Assets and trust boundaries

Protected assets are quarantined drafts, released synthetic turns, policy and
prompt versions, plugin configuration, reviewer decisions, raw evaluation
artifacts, and provider credentials. Scenario text, role-play input, model
output, provider responses, plugin packages, and browser data are untrusted.
The project uses Synthetic data only and is not approved for real patient data.

## Threats and mandatory controls

| Threat | Boundary | Required control and acceptance evidence |
|---|---|---|
| Prompt injection | Scenario and role-play text attempts to alter system rules or enable plugins. | Treat text only as data; input routing precedes generation; configuration is never derived from model text. |
| Unsafe draft release | A model draft contains prohibited or crisis-flow content. | Quarantine every draft, run all required guards, release atomically, and expose no raw-token stream. |
| Unbounded repair | Rewriting repeatedly hides a persistent failure or consumes resources. | Enforce the contract constant of two rewrites, then hold for human review. |
| Provider failure | Timeout, malformed response, authentication error, or unavailable cloud service. | Record structured failure evidence, emit `RUNTIME_FAILURE`, and fail closed without a fallback reply. |
| Plugin supply chain | Unapproved, incompatible, or malicious plugin executes in the runtime. | Discover only allowlisted entry points, validate `PluginManifestV1`, pin versions, reject conflicts, and fail closed for critical kinds. |
| Sensitive data disclosure | Input, draft, prompt, secret, or report leaks through logs or provider calls. | Synthetic data only; redact operational logs; secrets never enter events; provider adapter sends only the declared request; no chain-of-thought is stored. |
| Audit tampering | A transition, draft decision, or review outcome is overwritten. | Use an append-only event ledger, immutable provenance, monotonic sequence, and superseding decisions rather than updates. |
| Role boundary bypass | Participant-facing code reads a quarantined draft or reviewer-only evidence. | Separate response projections and application queries; participant endpoints return released content only. |
| Cross-session confusion | Retry or concurrent submission associates output with the wrong turn. | Require session-scoped IDs, write idempotency keys, explicit causation IDs, and transactional state transition checks. |
| Replay nondeterminism | Clock, network, random provider result, or mutable plugin profile changes evidence. | Replay reads frozen artifacts only; store exact prompt/plugin/model identities; exclude runtime metadata from canonical identity. |
| False clinical interpretation | A reviewer mistakes system routing for diagnosis or validated safety assessment. | Use non-clinical vocabulary and persistent research-only limitations in UI and reports; do not expose scores or probabilities. |
| Resource guessing | Missing locale causes an invented emergency contact. | Select only allowlisted, versioned, jurisdiction-matched resources at explicit `as_of`; otherwise require review with no guessed contact. |

## Milestone 9 implemented controls

- Plugin discovery matches the exact local entry-point group, name, and value
  before load, then validates exact manifest identity/version and the complete
  dependency graph. Unallowlisted entries are not loaded.
- The project bundles no plugin or default allowlist. Discovery does not install
  packages, access credentials, or use the network.
- Provider output is revalidated even when an adapter returns a `ModelDraft`
  instance. Request, provider, and model identity mismatches fail closed.
- Provider exception text is not copied into failure evidence. The result stores
  only a stable failure category and the validated `RUNTIME_FAILURE` event.
- Successful generation yields quarantined data only. M9 has no release field,
  raw-token stream, fallback provider, or participant projection.

## Milestone 10 implemented controls

- Input pre-routing completes before a session enters drafting or a model port
  is called. Synthetic override evidence never coexists with an ordinary
  released response for that command.
- Draft text remains reviewer-only until the gate allows it and the
  `DRAFT_APPROVED` event is durably appended to the in-memory ledger. A failed
  approval append produces no released turn.
- Exact request retries use an immutable local result projection; changed input
  under the same request ID rejects. This does not claim distributed
  idempotency.
- The in-memory ledger validates the full state/sequence chain before append and
  exposes tuple snapshots only. There is no update/delete method or wall-clock
  identity.
- Persistent ledger unavailability can prevent recording even the failure
  transition. The service still exposes no reply, but durable recovery and
  multi-process consistency remain deferred to a later versioned milestone.

## Milestone 11 implemented controls

- Review resolution binds a detached authoritative held-draft snapshot and
  requires both complete draft equality and the ledger's exact current
  last-held identity. A stale, cross-session, same-ID-content-substituted, or
  different-ID draft rejects before an event append.
- Approval text must be byte-identical to the reviewed draft; replacement text
  is explicit reviewer-supplied synthetic data. Neither becomes participant
  visible until the matching append-only review event succeeds.
- Handoff and rejection transition to `CLOSED` without exposing draft or
  replacement content. Terminal state cannot be reopened through review.
- Participant resolution data excludes the draft, decision evidence, internal
  event, and failure category. Exact local retries return detached snapshots
  and do not append another decision.
- A one-shot decision append failure records `RUNTIME_FAILURE` when possible;
  persistent ledger failure exposes no reply. This remains process-local
  control-flow evidence, not durable audit or effective human oversight.

## Milestone 12 implemented controls

- Close binds a detached synthetic snapshot and exact session/trajectory
  identity. Every user turn requires submit or suppressed-override evidence;
  every assistant turn requires an existing direct or reviewed release event.
- The canonical artifact is built and evaluated in memory. The existing
  final-only evaluator still receives only `FinalAnswerView`, the trajectory
  evaluator receives the complete ordered trajectory, and neither receives
  gold.
- Evaluation identity, hash, and trajectory are revalidated. No participant or
  research report is returned until the append-only `CLOSE_SESSION` event
  succeeds.
- Evaluation and ledger failures expose only stable categories, append
  `RUNTIME_FAILURE` when possible, and return neither a final answer nor raw
  evaluation. Persistent ledger failure releases no report.
- Exact close retries return detached local snapshots without a second event.
  This is not durable, concurrent, or distributed session/report storage.

## Existing offline harness controls retained

| Threat | Required control |
|---|---|
| Artifact identity or reference tampering | Canonical-byte comparison, SHA-256 reconstruction, strict schemas, and aggregate reference validation reject the artifact. |
| Gold leakage | Evaluators cannot import gold; application orchestration records actual evaluation before loading gold. |
| Stale or handwritten summaries | Strict raw parsing and deterministic regeneration derive every count; CI checks generated artifact diffs. |
| Static audit injection | Untrusted artifact text is escaped and the page contains no script or remote asset. |
| Dependency drift | Python 3.12, the committed `uv.lock`, and locked verification preserve the offline evaluator environment. |

## Out-of-scope claims and residual risk

The controls demonstrate artifact and orchestration behavior, not real-world
safety, clinical validity, treatment benefit, diagnostic accuracy, or crisis
detection accuracy. Model and policy defects can remain after all gates pass.
Human review in the local demo is simulated and is not an emergency response
service. A later real-participant study requires a new threat model, ethics and
privacy approval, operational response ownership, and jurisdiction-specific
legal review.

## Milestone 13 future full-stack threats

These controls are frozen acceptance requirements, not implemented M13
capabilities.

| Threat | Required future control |
|---|---|
| Demo identity enabled in production | Production startup rejects local identity configuration; CI tests both environment modes. |
| OIDC role bypass | Validate issuer, audience, expiry, nonce, and server-side role mapping on every protected request; deny by default. |
| SSE content leakage | Participant streams use a strict public envelope and contain status plus only an atomic already gated answer; test every internal field as prohibited. |
| Cross-instance event loss | Commit PostgreSQL event first, resume by `Last-Event-ID`, and treat Redis only as a wake-up hint. |
| Tool-call excessive agency | Permit only session-profile allowlisted tools, validate arguments and authorization server-side, and require application-service execution. |
| Report injection | Escape untrusted text in HTML, prohibit active content, isolate PDF rendering, and test malicious bilingual fixtures. |
| Server-side request forgery | No model-selected URL fetching; external adapters use fixed allowlisted destinations and deny private/link-local targets. |
| Secret disclosure | Keep provider/OIDC/database secrets in server-side secret stores; redact headers, tool arguments, errors, traces, and reports. |
| Database race or duplicate release | Transactionally lock session state, enforce unique idempotency/event constraints, and append before projection. |
| Retention bypass | Apply visible synthetic-session retention and audited whole-session purge without mutating frozen benchmark evidence. |
| Unstaffed review mistaken for care | Persistent UI/report disclosure states the queue is simulated and supplies no emergency response or clinical SLA. |
| Model or guard disagreement | Map uncertainty to `hold_for_review`; no voting rule, rewrite, or provider fallback may create an allow decision. |
| Resource exhaustion | Bound request size, concurrency, provider duration, repair count, SSE lifetime, and queued work; failure releases no ordinary answer. |
| Dependency or image compromise | Pin Python/Node/container/IaC dependencies, scan artifacts, use minimal images, and record build provenance before cloud delivery. |

## Milestone 14 implemented controls

- Authoritative event, outbox, and projection writes share one SQL transaction;
  the adapter locks the session row and enforces state and sequence again before
  commit.
- Database uniqueness protects event and request identity. Exact idempotency
  replay is immutable; changed reuse rejects.
- Redis contains notifications only. A failed publish leaves the SQL outbox
  pending and a replacement worker can retry it. Delivery is at least once, so
  downstream consumers must deduplicate.
- Plugin profiles require all safety-critical kinds enabled and locked and
  reject duplicate or changed identities.
- Provider credentials are `SecretStr` constructor inputs and are not included
  in drafts, outbox events, failure categories, or object representations.
- Provider parsing accepts only a complete non-blank string and never exposes a
  partial token or executes a tool call. The existing model runtime converts
  adapter exceptions into a category-only failed-closed result.
- Live PostgreSQL/Redis availability, TLS, credential rotation, connection-pool
  sizing, database backup, and multi-instance load behavior are not proven by
  M14 local tests and remain deployment risks for M16/M17.

## Milestone 16 implemented controls

- FastAPI authorizes every protected route through one injected identity
  boundary. Participant reads also compare the authenticated subject with the
  authoritative stored owner; a guessed session ID does not disclose a
  projection.
- OIDC tokens require an asymmetric signature and configured issuer, audience,
  expiry, nonce, and exact role. The separate header-driven synthetic identity
  exists only for the explicit local Compose server and refuses production mode.
- Participant contracts cannot contain quarantined drafts or reviewer evidence.
  Status-only SSE replays committed PostgreSQL rows by a session-bound
  `Last-Event-ID`; only `answer_released` can contain one complete assistant turn.
- Public projection and event writes share a SQL transaction after existing
  input routing, draft gates, bounded repair, and runtime append. Exact create
  retries return their recorded projection, while conflicting reuse and
  cross-subject session creation reject.
- Reviewer HTML escapes untrusted report fields and contains no script or remote
  asset. The deterministic PDF contains no JavaScript, open action, or link.
  Participant JSON omits the reviewer evidence object entirely.
- API request text is bounded, model/provider destinations remain server-owned,
  plugin criticality is revalidated by immutable profiles, and active sessions
  never load code or hot-swap a profile from model output.
- Compose images run as non-root users, build from lockfiles, exclude local
  build/dependency directories, provide health checks, and persist PostgreSQL.
  The worker publishes only committed outbox rows; Redis remains ephemeral.
- Remaining operational threats include absent live PostgreSQL/Redis concurrency
  and crash-recovery evidence, rate limiting, TLS/secret rotation, backup/purge
  execution, full OIDC discovery/key rotation, dependency/image scanning, and
  production load testing. These are not represented as M16 passes.

## Milestone 17 deployment-template controls

| Threat | Implemented template or delivery control | Residual validation |
|---|---|---|
| Accidental public research surface | Cloud Run resources use restricted ingress and create no `allUsers` invoker binding. | Deployment-owned gateway/IAP and OIDC browser flow must be reviewed in an approved project. |
| Development identity in production | Strict production settings accept only `production` with local synthetic identity disabled; Terraform injects those exact values. | OIDC discovery, key rotation, tenant configuration, and end-user flow were not exercised. |
| Secret disclosure through source or state | Terraform creates empty secret containers and grants per-secret access; README requires out-of-band versions and encrypted remote state. | Operator plan/state handling, rotation, and audit logging require a live exercise. |
| Excessive cloud identity | API, Web, and worker use separate service accounts; no Owner/Editor role is granted. | Organization policy and effective IAM must be inspected after apply. |
| Redis mistaken for authoritative storage | Only PostgreSQL retains events/outbox/projections; recovery guidance republishes committed outbox rows after Redis loss. | Live disconnect/reconnect, duplicate delivery, and multi-instance behavior remain untested. |
| Destructive database recovery | Deletion protection and PITR are configured; the runbook restores to a new Cloud SQL instance and requires explicit approval before promotion. | Backup creation, restore duration, integrity comparison, and RTO/RPO are not claimed. |
| Provider/IaC drift | Provider and Terraform version constraints, static contract tests, digest-image inputs, and generated evidence checks are committed. | Terraform/gcloud were unavailable, so provider initialization, schema validation, plan, policy scan, and apply were not run. |
| Cloud template mistaken for production assurance | README, safety limits, release checklist, and generated M17 evidence label the stack synthetic/non-clinical and enumerate unverified operations. | Independent security, privacy, legal, cost, load, recovery, and operational review remain mandatory. |
