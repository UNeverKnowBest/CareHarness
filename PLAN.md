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

Milestone 4 is complete. The exact next milestone is Milestone 5: compose the
verified core behind the three application use cases, CLI, and optional minimal
read-only audit UI without changing process or safety policy behavior.

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
