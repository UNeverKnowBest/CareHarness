# CareLoop Harness Day 1 Plan

Plan status: Day 1 complete; D1.0 through D1.5 acceptance criteria are met.

## Status vocabulary

- **FROZEN**: required Day 1 task or gate.
- **ASSUMPTION**: conservative execution default that does not change a public
  contract.
- **TBD**: decision required before the affected task starts.

## Day 1 outcome

### FROZEN

Establish a minimal Python 3.12 `uv` src-layout package and versioned Pydantic v2
domain schemas with validation tests. Expose CLI help/version only. Do not start
evaluators, safety detection, policies, fixtures, replay, benchmark execution,
reporting, adapters, or UI.

## Task sequence

### D1.0 Contract Bootstrap

### FROZEN

- Create `SPEC.md`, `ARCHITECTURE.md`, `PLAN.md`, and `STATUS.md` from the approved
  engineering guide and preflight defaults.
- Mark unsupported public decisions as TBD instead of inventing them.
- Stop for owner review before creating implementation or tests.

Acceptance: only these four Markdown files change during Contract Bootstrap.

### D1.1 Resolve public contract TBDs

### COMPLETE — owner-frozen contract

Obtain explicit owner decisions for:

- exact wire fields and nesting for `Turn`, `Trajectory`, `ProcessMarker`,
  `SafetyEvent`, `Finding`, and `CrisisResource`;
- allowed turn-role values;
- unknown-field compatibility behavior.

Acceptance: `SPEC.md` and `ARCHITECTURE.md` contain no Day 1-blocking public TBD.

Owner decision recorded: exact fields use the schema tables in `SPEC.md`;
`Turn.role` accepts only `user` and `assistant`; `ProcessMarker` and
`SafetyEvent` are embedded in `Trajectory`; `Finding` remains standalone; and
all public models reject unknown fields.

### D1.2 Scaffold the package and tool configuration

### COMPLETE

- Add Python 3.12 `pyproject.toml`, `uv.lock`, and src-layout package.
- Configure only Pydantic v2, Typer, pytest, Ruff, and mypy.
- Add package version and CLI help/version; add no business commands.

Acceptance: package imports and CLI help/version execute in the locked local
environment.

Evidence is recorded in `STATUS.md`: the lock contains 23 packages, the local
environment uses Python 3.12.11, CLI help/version exit successfully, and the
non-domain scaffold tests pass.

### D1.3 Add failing domain contract tests

### COMPLETE — expected red state

Write tests before behavior for:

- valid trajectory round-trip;
- duplicate turn IDs and non-monotonic sequence;
- empty and unresolved finding/event turn references;
- override with `normal_flow_suppressed=false`;
- resource verified/expiry ordering;
- explicit unknown schema/policy-version rejection;
- `FinalAnswerView` exposing only `text` and `turn_id`;
- absence of risk score/level, diagnosis, and clinical disposition fields.

Acceptance: new tests fail for the intended missing behavior before the domain
implementation is added.

Evidence is recorded in `STATUS.md`: 19 domain contract tests fail because the
empty scaffold package does not yet expose the D1.4 models. No domain behavior
was implemented to make these tests pass.

### D1.4 Implement the minimum versioned domain schema

### COMPLETE

- Implement only the models and validation required by `SPEC.md` and the failing
  tests.
- Keep domain free of CLI/UI/tests/network/provider dependencies.
- Provide visible typed validation failures; never silently accept unknown
  versions or invalid references.
- Refactor only within the Day 1 domain scope after tests pass.

Acceptance: focused domain and architecture tests pass without changing the
frozen contract.

Evidence is recorded in `STATUS.md`: all frozen public models and aggregate
validation are implemented, and the focused domain suite passes 24 tests.

### D1.5 Verify and record evidence

### COMPLETE

Run, in order:

```text
uv run pytest <focused-domain-tests> -q
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

Update `STATUS.md` with exact commands, exit statuses, test counts, modified
public schemas, remaining risks, and the next milestone. Do not claim a command
passed unless it ran in this environment.

Evidence is recorded in `STATUS.md`: the required format, lint, type-check, and
full test commands all exit successfully, with 27 tests passing.

## Day 1 acceptance criteria

### FROZEN

- Python 3.12 `uv` src-layout package is reproducible from its lockfile.
- All approved public models round-trip deterministically at the domain level.
- Invalid IDs, ordering, references, date relations, and versions fail visibly.
- SafetyAction contains exactly the four approved system actions.
- No model exposes a risk score/level, probability, diagnosis, or clinical
  disposition.
- `FinalAnswerView` contains exactly `text` and `turn_id`.
- CLI exposes help/version and no business operation.
- Focused and full verification commands have recorded successful results.

## Explicitly not planned on Day 1

### FROZEN

- CBT/MI rules or evaluators;
- synthetic safety detector, crisis router, output policy, or resource routing;
- benchmark/gold fixtures, replay, canonical hashing, raw artifacts, or reports;
- real or scripted model adapters;
- Streamlit, Web API, database, network access, deployment, or UI.

## Milestone 2 — frozen fixtures, canonical hash, and replay

Plan status: **COMPLETE**. Work remained within Milestone 2 and did not change
the Day 1 public schema.

### M2.1 Freeze internal artifact decisions

### COMPLETE

- Freeze UTF-8 non-ASCII-preserving compact canonical JSON, ISO dates, no
  trailing newline, SHA-256, and exclusion of hash/runtime fields.
- Add a versioned internal trajectory artifact envelope around the unchanged
  `Trajectory` model.
- Keep gold as isolated JSON benchmark data outside the production package.

### M2.2 Add red contract and property tests

### COMPLETE

- Add tests for corpus/schema load, manifest ordering/uniqueness, canonical
  encoding/hash properties, exact replay reconstruction, mutation sensitivity,
  negative fixtures, zero external calls, gold isolation, matched-pair
  differences, synthetic labeling, and runtime metadata exclusion.
- Record the pre-implementation collection failure in `STATUS.md`.

### M2.3 Implement deterministic artifact replay

### COMPLETE

- Add canonical encoding/hash helpers, strict canonical artifact loading, and
  the `ReplayArtifact` application use case.
- Replay reconstructs only local frozen evidence and exposes no adapter/model/
  network/wall-clock input.

### M2.4 Generate and freeze the corpus

### COMPLETE

- Generate eight matched pairs/16 trajectories, 16 separately stored gold
  labels, four independent failure fixtures, and one ordered manifest.
- Keep a deterministic generator with a `--check` mode so frozen JSON is never
  hand-edited.
- Retain P2, P3, P5, P6, P7, and P8 and also include P1 and P4.

### M2.5 Verify and record evidence

### COMPLETE

- Run focused/property tests, fixture regeneration check, Ruff, mypy, and the
  complete test suite.
- Record exact commands, exit status, and counts in `STATUS.md`.

### Milestone 2 explicit exclusions

- No CBT/MI/safety evaluator or policy registry.
- No safety detector/router or resource selection.
- No CLI benchmark command, report generation, Streamlit, or model call.

## Exact next milestone

Milestone 7 is complete. No Milestone 8 or additional product behavior is
planned. Any future work requires a new owner-approved, versioned milestone that
preserves the frozen synthetic, offline, deterministic, non-clinical boundary.

## Milestone 3 — deterministic CBT-informed/MI-inspired process evaluator

Plan status: **COMPLETE**. Work remained within process evaluation for P1–P5;
no Milestone 4 safety runtime or ethical engine was started.

### M3.1 Freeze rule sources and process semantics

### COMPLETE

- Added `docs/source_map.md`, `docs/safety_and_limitations.md`, and
  `docs/test_matrix.md` before evaluator behavior.
- Froze seven ordered observable violation rules and exact
  present/absent/uncertain semantics in `SPEC.md` and
  `policies/process.v1.json`.

### M3.2 Add red process/state/metamorphic tests

### COMPLETE

- Added positive, absent, and uncertain coverage for every rule, legal MI
  backtracking, optional Planning, support-only/user-decline endings, stable
  output order, source/evidence integrity, untrusted user text, and safe-final
  metamorphism.
- Recorded the pre-implementation missing-package collection failure in
  `STATUS.md`.

### M3.3 Implement the process registry and evaluators

### COMPLETE

- Added strict immutable process policy metadata plus pure session-shell,
  CBT-informed, MI-inspired, and aggregate trajectory evaluators.
- Evaluators emit evidence-linked `Finding` objects in registry order and have
  no gold, application, CLI/UI, provider, network, or wall-clock dependency.

### M3.4 Align P3/P4 to the Day 3 contract

### COMPLETE — explicit owner authorization to revise frozen fixtures

- Revised P3 to permission-before-skill versus unpermitted direction and P4 to
  non-diagnostic wording versus a diagnosis claim.
- Regenerated changed trajectory hashes and P1–P5 gold metadata only through the
  deterministic generator. Day 1 public schemas remain unchanged.

### M3.5 Verify and record evidence

### COMPLETE

- Focused process/fixture/architecture tests, generator check, format, lint,
  mypy, lock, and full pytest pass with exact results in `STATUS.md`.
- The required benchmark command was run and truthfully records exit 2 because
  the benchmark CLI remains a later-milestone capability.

### Milestone 3 explicit exclusions

- No final-only evaluator or `EvaluateTrajectory` application orchestration.
- No crisis detector/router, ethical output gate, resource selection, benchmark
  runner/report, CLI business command, UI, adapter, model, or network call.

## Milestone 4 — crisis preemption and ethical policy engine

Plan status: **COMPLETE**. Work remained within synthetic safety runtime,
versioned crisis/ethical/resource policy, P6–P8, and corresponding tests.

### M4.1 Freeze crisis, ethical, and resource contracts

### COMPLETE

- Expanded source map, safety limitations, and test matrix before behavior.
- Added strict v1 crisis, ethical, and synthetic resource registries with exact
  signals, actions, source IDs, locale/date constraints, and output categories.

### M4.2 Add red safety and failure-injection tests

### COMPLETE

- Added P6–P8, signal-context, preemption, ordering, resource integrity,
  prompt-injection, ethical category, evidence, API-boundary, metamorphic, and
  detector/router/resource/output-policy exception tests.
- Recorded the pre-implementation missing-package collection failure in
  `STATUS.md`.

### M4.3 Implement fail-closed synthetic safety runtime

### COMPLETE

- Added exact-tag detector, crisis router, explicit-as-of resource selector,
  ethical output gate, and typed runtime result.
- Override calls no normal responder; safe normal output is gated before
  visibility; all safety subsystem failures suppress normal flow and require
  human review.

### M4.4 Align P6–P8 with the Day 4 contract

### COMPLETE — explicit owner authorization to revise frozen fixtures

- Regenerated P6 ambiguous clarification, P7 current-plan emergency action, and
  P8 exact-versus-wrong synthetic locale resource pairs, including canonical
  hashes, events, and gold metadata.

### M4.5 Verify and record evidence

### COMPLETE

- Focused/failure/metamorphic/fixture/architecture tests, generator check, Ruff,
  mypy, lock, and full pytest pass with exact results in `STATUS.md`.
- The required benchmark command truthfully records exit 2 because the benchmark
  CLI remains a Milestone 5 capability.

### Milestone 4 explicit exclusions

- No real-world detector, clinical classifier, screening instrument, complete
  safety plan, automatic third-party contact, real resource lookup, or clinical
  claim.
- No application orchestration, benchmark/report pipeline, CLI business command,
  UI, adapter, provider/model, network, database, or deployment work.

## Milestone 5 — application services, CLI, and static audit

Plan status: **COMPLETE**. The owner selected static offline HTML,
an evidence ledger without an aggregate score, and a dedicated milestone branch.

### M5.1 Freeze application and presentation contracts

### COMPLETE

- Froze the final-only/trajectory-aware inputs, offline P6–P8 observation
  registry, raw result/JSONL semantics, post-evaluation gold comparison, CLI
  exit behavior, and escaped no-script HTML boundary.
- Preserved all Day 1 public models, existing process/safety policies, frozen
  trajectories, gold files, dependencies, and version tokens.

### M5.2 Add red application, ordering, CLI, and audit tests

### COMPLETE

- Add final-only leakage, final-turn construction, P1–P8 localization, stable
  ledger order, evaluation-before-gold spy, manifest-order JSONL, repeatability,
  CLI error/smoke, HTML escaping/evidence-link, and UI-removability tests.
- Record the pre-implementation red result in `STATUS.md`.

### M5.3 Implement the three application use cases

### COMPLETE

- Add the final-only and complete-trajectory evaluators, `EvaluateTrajectory`,
  preserve `ReplayArtifact`, and add ordered `RunBenchmark` with comparison and
  raw artifact models.
- Add no fourth business use case and place no evaluator rule in application,
  CLI, report, or presentation code.

### M5.4 Add CLI and static audit presentation

### COMPLETE

- Expose `evaluate`, `replay`, and `benchmark` with deterministic outputs and
  understandable failures.
- Render the selected timeline/evidence/suppression/resource/hash audit page
  using only escaped application result data and inline CSS.

### M5.5 Verify, record, and deliver

### COMPLETE

- Run focused tests, fixture generator check, Ruff format/check, mypy, full
  pytest, lock check, and the required benchmark command.
- Review the complete diff, update `STATUS.md`, create one scoped commit, and
  push the dedicated Milestone 5 branch only if every required gate passes.

### Milestone 5 explicit exclusions

- No summary metrics, CI workflow, mutation proof, README/technical report,
  authentication, database, Web API, chat, model/provider, network, or deploy.
- No changes to process/crisis/ethical/resource policy behavior, frozen
  trajectories, gold labels, public Day 1 schemas, or dependency versions.

## Milestone 6 — derived summaries, CI, documentation, and mutation proof

Plan status: **COMPLETE**. Work was limited to deterministic raw verification,
the nine allowed descriptive summaries, CI/documentation, and temporary safety
mutation evidence.

### M6.1 Freeze report and verification contracts

### COMPLETE

- Freeze separate benchmark and verification raw JSONL, nine ordered descriptive
  evidence metrics, canonical JSON/deterministic Markdown, and prohibited claims.
- Preserve evaluator/gold decisions, frozen fixtures, policies, public schemas,
  dependency versions, and the 16-record manifest-order benchmark raw contract.

### M6.2 Add red raw-to-summary and delivery tests

### COMPLETE

- Add strict raw parsing, recomputation, metric semantics/order, no aggregate
  score, failure-reason, CLI output, CI order, README boundary, and reporting
  architecture tests before implementation.

### M6.3 Implement verification raw and pure derivation

### COMPLETE

- Extend `RunBenchmark` to record 16 replay checks and four expected invalid
  fixture rejections after normal benchmark evaluation.
- Derive summary JSON and Markdown only after both raw JSONL files exist, with no
  evaluator or gold decision logic in reporting or CLI.

### M6.4 Add CI and technical documentation

### COMPLETE

- Add lockfile-based GitHub Actions gates in the required order and verify that
  benchmark regeneration leaves tracked generated artifacts unchanged.
- Add README first-screen boundaries, threat model, and technical report linked
  to raw and generated summary evidence.

### M6.5 Prove mutation sensitivity, verify, and deliver

### COMPLETE

- In a temporary worktree, make the P7 current-plan branch continue ordinary
  response, record the focused safety test failing, restore the mutation, and
  record the same test passing. Never commit the mutation.
- Run focused tests, generator check, Ruff format/check, mypy, full pytest, lock
  check, benchmark, raw-to-summary byte recomputation, and complete diff review.

### Milestone 6 explicit exclusions

- No evaluator, gold, policy, frozen fixture, public schema, dependency, package
  version, adapter, model/provider, network, database, service, deployment, or
  audit-UI behavior change.
- No aggregate score, percentage, statistical significance, clinical metric, or
  real-world/population claim.

## Milestone 7 — clean reproduction and final read-only review

Plan status: **COMPLETE**. Milestone 7 added no product behavior and changed no
runtime dependency, public schema, evaluator, policy, fixture, gold label, or
generated result artifact.

### M7.1 Freeze the project-closing README contract

### COMPLETE

- State the completed milestone status, lockfile reproduction sequence,
  generated-artifact ownership, interpretation boundary, and maintenance rules.
- State that the CLI is the primary interface, there is no web application or
  server, and optional audit HTML is a local read-only file.
- Protect these statements with a delivery-contract test before editing README.

### M7.2 Reproduce from a clean locked environment

### COMPLETE

- Create an isolated detached worktree at the M7 README/test commit and verify it
  has no existing `.venv`.
- Run `uv sync --locked`, lock/version/help checks, the complete quality gate,
  benchmark regeneration, fixture generator check, and artifact diff check.
- Require a clean worktree after reproduction and remove the temporary worktree.

### M7.3 Conduct a separate strict read-only final review

### COMPLETE

- After reproduction, inspect only versioned files and Git evidence; do not edit
  the isolated checkout during review.
- Verify M7 changes no source, policy, benchmark, generated artifact, dependency,
  or lockfile; confirm no web/server dependency and inspect static HTML rendering.
- Treat tests, source, lockfile, raw artifacts, and Git diffs as evidence. README
  and status statements are not independent proof.

### M7.4 Record, verify, and deliver

### COMPLETE

- Record exact commands, exit statuses, counts, review findings, and residual
  limitations in `STATUS.md`.
- Re-run the complete locked quality gate in the primary worktree, review the
  final diff, commit the M7 evidence, and push the dedicated branch.

### Milestone 7 explicit exclusions

- No Web UI, Web API, server, chat surface, upload flow, provider/model adapter,
  network runtime, database, deployment, or new application use case.
- No clinical, real-world safety, treatment, population, aggregate-score, or
  statistical claim.

## Milestone 8 — synthetic agent-runtime contracts and state machine

Owner approval: the full-stack research plan approved after Milestone 7
authorizes this additive milestone while preserving all frozen clinical,
fixture, evaluator, replay, gold-isolation, and reporting boundaries.

### M8.1 Freeze public runtime and product boundaries

### COMPLETE

- Freeze non-clinical state, disposition, draft, review, model-port,
  provenance, and plugin vocabulary in `SPEC.md`.
- Freeze the future HTTP surface, logical append-only persistence model, plugin
  failure modes, and synthetic-only interaction contract.
- Extend the threat model for provider, draft-release, plugin, audit, role, and
  idempotency boundaries.

### M8.2 Add red contract and transition tests

### COMPLETE

- Add strict-model tests for exact versions, fields, enums, bounded rewriting,
  critical-plugin failure modes, provider neutrality, and prohibited fields.
- Add explicit transition-table, fail-closed, terminal-state, release-bypass,
  and review-bypass tests.
- Add documentation and architecture-boundary tests.

### M8.3 Implement the minimum provider-neutral core

### COMPLETE

- Add `careloop.agent_runtime` Pydantic contracts, asynchronous `ModelPort`, and
  pure state transition function.
- Add no provider, network, Web, persistence, authentication, or UI dependency.

### M8.4 Verify, record, and stop

### COMPLETE

- Run focused M8 tests and the complete locked verification sequence.
- Record exact results in `STATUS.md`, review the diff, and stop before M9.

### Milestone 8 explicit exclusions

- No real LLM call, provider adapter, plugin discovery, safety orchestration,
  API server, database, worker, browser UI, deployment, or new CLI command.
- No real-user or patient data and no clinical screening, diagnosis, risk score,
  treatment, or crisis-service claim.

## Exact next milestone

Milestone 9 — allowlisted plugin discovery and provider-neutral model runtime,
using deterministic test adapters first. It must not start until M8 passes all
required verification.

## Milestone 9 — allowlisted plugin discovery and provider-neutral model runtime

Plan status: **COMPLETE**. Work was limited to local manifest discovery and a
single quarantined draft-generation boundary. It does not add a live plugin,
real provider, complete session, new CLI command, or network behavior.

### M9.1 Freeze discovery and invocation contracts

### COMPLETE

- Freeze exact `careloop.plugins.v1` entry-point matching,
  `PluginAllowlistV1`, manifest identity/version pinning, complete dependency
  validation, and stable dependency-before-dependant order.
- Freeze the model-runtime success and failure result, exact failure categories,
  draft quarantine, explicit event identity/sequence, and exception-detail
  exclusion.
- Extend architecture, threat, safety/limitation, and test-matrix boundaries
  without changing existing evaluator, safety-policy, fixture, or report rules.

### M9.2 Add red discovery, adapter, and delivery tests

### COMPLETE

- Add pre-load allowlist, unapproved-entry isolation, identity/version,
  dependency/cycle, strict-schema, and deterministic-order tests.
- Add deterministic async adapter coverage for valid quarantined drafts,
  provider exceptions, invalid constructed models, and request/provider/model
  mismatch.
- Add failed-closed event, non-sensitive evidence, no-release-field,
  architecture, documentation, and README contract tests.

### M9.3 Implement the minimum removable runtime

### COMPLETE

- Add `careloop.plugin_runtime` using only local `importlib.metadata`, strict
  allowlist models, `PluginManifestV1` validation, and pure dependency ordering.
- Add `ProviderNeutralModelRuntime` over the existing `ModelPort`, revalidate
  all returned drafts, and return either quarantined evidence or a typed
  `RUNTIME_FAILURE`/`FAILED_CLOSED` result.
- Keep every adapter in tests. Register no project entry point or provider and
  add no dependency, credential, fallback, clock, random, file, or network use.

### M9.4 Verify, record, and stop

### COMPLETE

- Run focused M9 tests, the complete locked format/lint/mypy/pytest gate, the
  unchanged benchmark, fixture-generator check, generated-artifact diff, lock
  check, and final change-boundary review.
- Record exact exit statuses and counts in `STATUS.md`, then stop before M10
  implementation.

### Milestone 9 explicit exclusions

- No installed/default plugin, concrete provider, prompt builder, safety-plugin
  execution, rewrite/review/release orchestration, persistence, API, Web UI,
  worker, deployment, authentication, or new CLI command.
- No real-person data, clinical screening, diagnosis, risk classification,
  treatment, crisis-service behavior, model-quality claim, or real-world safety
  claim.

## Milestone 10 — deterministic synthetic turn orchestration and event ledger

Plan status: **COMPLETE**. The owner-authorized delivery remained limited to the
frozen application service and in-memory evidence boundary below.

### M10.1 Freeze one application use case and evidence boundary

### COMPLETE

- Define one `RunSyntheticTurn` application service for versioned synthetic
  role-play only. Freeze its request/result fields and exact composition of
  input routing, provider-neutral drafting, draft checks, bounded rewrite,
  review hold, atomic release, and failed-closed termination.
- Freeze a local append-only in-memory runtime ledger for acceptance evidence.
  Require monotonic `(session_id, sequence)`, exact causation/evidence
  references, no updates/deletes, and replay from events without clock/random
  identity.
- Freeze participant versus reviewer projections: participant output contains
  released turns only; drafts, failed attempts, and review evidence remain
  quarantined.

### M10.2 Add red orchestration and failure-injection tests

### COMPLETE

- Cover input safety before any model call, override with zero model calls,
  output checking before release, two rewrites maximum, review hold, no bypass,
  and atomic release.
- Inject model, input-router, output-guard, resource, and ledger failures and
  require a final append-only `RUNTIME_FAILURE` transition with no visible
  ordinary output or fallback reply.
- Cover idempotent causation, monotonic ledger sequence, reconstruction,
  participant/reviewer projection isolation, plugin-profile immutability, and
  deterministic repeated results.

### M10.3 Implement the minimum in-memory orchestration

### COMPLETE

- Compose only existing versioned contracts, the existing synthetic safety
  runtime, M9 model runtime, injected deterministic draft-check adapters, and a
  local in-memory ledger behind declared ports.
- Implement no database, HTTP endpoint, background worker, browser UI, real
  plugin package, or provider/network adapter. Add no CLI command unless a
  separately frozen M10 contract explicitly requires one before tests.

### M10.4 Verify, record, and stop

### COMPLETE

- Run focused failure/metamorphic/architecture tests and the complete locked
  verification sequence, including the unchanged offline benchmark and
  generated-artifact diff.
- Update `STATUS.md` with exact evidence and stop before any Web, database,
  cloud-provider, credential, or real-participant milestone.

### Milestone 10 acceptance gates

- No draft or partial token reaches the participant projection before every
  required gate passes; an override or critical failure releases no ordinary
  response.
- Rewrites stop after two attempts and then enter typed review hold. Review hold
  cannot be bypassed by another turn.
- The append-only ledger alone reconstructs the exact session state and rejects
  duplicate/non-monotonic events without rewriting history.
- Removing the orchestration package leaves evaluator, replay, benchmark,
  reporting, existing CLI commands, frozen fixtures, and generated artifacts
  fully operational.

### Milestone 10 explicit exclusions

- No FastAPI, PostgreSQL, SQLAlchemy, Alembic, WebSocket/SSE server, React,
  Docker, authentication, real provider/plugin, credential access, deployment,
  FHIR, real-user data, or clinical claim.

## Milestone 11 — deterministic synthetic review resolution

Plan status: **COMPLETE**. The owner authorized the harness to freeze the
smallest next milestone from the mission and completed M10 boundary. M11 is
limited to resolving one synthetic pre-release review hold through existing
typed decisions and the append-only in-memory event ledger.

### M11.1 Freeze review command, projection, and transition contracts

### COMPLETE

- Freeze exact strict command/result/status/failure fields and decision-specific
  release requirements.
- Require correlation with the last held draft, append-before-release,
  participant/reviewer isolation, exact retry idempotency, and category-only
  ledger failure evidence.
- Preserve all existing enums, Day 1 schemas, policies, fixtures, gold,
  benchmark/report bytes, dependencies, and CLI commands.

### M11.2 Add red review-resolution and failure-injection tests

### COMPLETE

- Cover all four existing review decisions, held-draft/session correlation,
  strict schemas, projection isolation, event-before-release, exact/conflicting
  retries, detached snapshots, and terminal-state rejection.
- Inject one-shot and persistent ledger failures and require no released turn,
  deterministic failed-closed evidence where writable, and typed unavailability
  otherwise.

### M11.3 Implement the minimum library-only resolver

### COMPLETE

- Add `ResolveSyntheticReview` and its strict models in a removable application
  module over `RuntimeEventLedgerPort`.
- Reuse only `ReviewDecision`, `SessionEvent`, `SessionState`, `RuntimeEvent`,
  `Turn`, and `ModelDraft`; add no adapter, store, endpoint, command, dependency,
  policy logic, provider, or reviewer workflow.

### M11.4 Verify, record, and stop

### COMPLETE

- Run focused review/storage/architecture tests and the complete locked quality
  gate, unchanged benchmark, fixture check, lock check, and generated-artifact
  diff.
- Record exact evidence in `STATUS.md` and stop before session-close evaluation,
  durable persistence, Web/API, real provider/plugin, or real-participant work.

### Milestone 11 acceptance gates

- A reviewed draft or replacement reaches the participant projection only after
  the matching append-only review event succeeds.
- Handoff and rejection close the synthetic session without releasing draft or
  replacement text.
- A stale, mismatched, terminal, or non-held command rejects without mutation;
  ledger failure never falls back to an ordinary reply.
- Participant results contain no draft, decision evidence, internal event, or
  failure detail; exact retries do not append twice.
- Removing M10/M11 runtime modules leaves the frozen offline harness and
  generated artifacts operational.

### Milestone 11 explicit exclusions

- No reviewer queue/assignment, authentication, durable storage, database,
  HTTP/API/SSE/WebSocket, UI, worker, notification, real provider/plugin,
  credential, network, deployment, FHIR, real-user data, or clinical claim.
- No session-close trajectory construction, evaluation/report orchestration, or
  Milestone 12 behavior.

## Exact next milestone

No Milestone 12 was approved at M11 close. The owner's later instruction to
complete M12 authorizes only the versioned session-close boundary below.

## Milestone 12 — deterministic synthetic session close and evaluation

Plan status: **COMPLETE**. Work is limited to one library-only close service,
in-memory trajectory assembly, reuse of existing offline evaluators, and
append-before-report evidence.

### M12.1 Freeze close, snapshot, and projection contracts

### COMPLETE

- Freeze exact strict snapshot, command, status, failure, participant, and
  research-review fields.
- Require complete submit/override/release evidence, in-memory canonical artifact
  identity, evaluator-before-close execution, and close-append-before-report
  release.
- Preserve existing states/events, public schemas, policies, fixtures, gold,
  benchmark/report bytes, dependencies, and CLI commands.

### M12.2 Add red close, failure-injection, and delivery tests

### COMPLETE

- Cover direct release and suppressed override assembly, identity/evidence
  mismatch, evaluator ordering, close append, exact/conflicting retries,
  strict schemas, projection isolation, and detached snapshots.
- Inject evaluator, one-shot ledger, and persistent ledger failures and require
  category-only failed-closed evidence with no report release.
- Add architecture, normative-document, and README boundary tests.

### M12.3 Implement the minimum library-only close service

### COMPLETE

- Add `CloseSyntheticSession` over `RuntimeEventLedgerPort`, canonical in-memory
  artifact construction, and `EvaluateTrajectory.evaluate_artifact`.
- Add no file writer, gold comparison, mutable store, endpoint, CLI command,
  dependency, policy logic, provider/plugin, network, clock, or randomness.

### M12.4 Verify, record, and stop

### COMPLETE

- Run focused M10–M12, evaluation, storage, architecture, and delivery tests,
  then the complete locked quality gate and unchanged benchmark/fixture/artifact
  checks.
- Record exact evidence in `STATUS.md` and stop before durable persistence,
  Web/API, real provider/plugin, operational review, or real-participant work.

### Milestone 12 acceptance gates

- A complete trajectory is evaluated only when every turn has submit,
  suppressed-override, or release evidence and the session is
  `RESPONSE_RELEASED`.
- The existing final-only evaluator receives only `FinalAnswerView`; the
  complete evaluator receives the assembled trajectory and never gold.
- No participant or research report is returned unless `CLOSE_SESSION` appends;
  evaluation/ledger failure produces no final answer or raw evaluation report.
- Exact retries append no second close; conflicting, stale, mismatched, or
  unevidenced input rejects before mutation.
- Removing M10–M12 leaves evaluate, replay, benchmark, reporting, frozen
  fixtures, and generated artifacts fully operational.

### Milestone 12 explicit exclusions

- No durable session/turn/draft/review/report store, transaction, concurrency or
  distributed idempotency, post-session review queue, authentication,
  HTTP/API/SSE/WebSocket, UI, worker, notification, real provider/plugin,
  credential, network, deployment, FHIR, real-user data, or clinical claim.
- No Milestone 13 behavior.

## Exact next milestone

No Milestone 13 is approved. Stop after M12. Any later work requires a new
versioned milestone that preserves the offline core, synthetic-only data,
draft/projection isolation, append-only evidence, and generated-artifact
ownership.
