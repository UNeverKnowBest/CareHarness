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
