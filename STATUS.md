# CareLoop Harness Status

Current phase: Milestone 4 complete
Next milestone: Milestone 5 application services, CLI, and minimal audit UI
Implementation status: COMPLETE for D1.0–D1.5 and M2.1–M4.5

## Status vocabulary

- **FROZEN**: approved temporary contract fact.
- **ASSUMPTION**: conservative interpretation, not implementation evidence.
- **TBD**: unresolved owner decision.

## Repository state before Contract Bootstrap

### FROZEN evidence

- Branch: `feat/domain-model`.
- HEAD: `5970828` (`docs: add Codex agent instructions`).
- Local `main`, `origin/main`, and `feat/domain-model` pointed to the same commit
  when bootstrap began.
- Tracked tree contained only `.gitignore`, `AGENTS.md`, and `LICENSE`.
- `CareLoop_Codex_工程化实施指南_ZH.md` existed as an untracked file.
- The original source specification, README, SPEC, ARCHITECTURE, PLAN, STATUS,
  `pyproject.toml`, `src/`, and `tests/` were absent.
- Tracked and staged diffs were empty before bootstrap.

## Contract Bootstrap result

### FROZEN

- The owner approved the existing engineering guide and preflight defaults as a
  temporary Day 1 contract.
- `SPEC.md` records product boundaries, version contracts, the frozen portion of
  the public schema, SafetyAction, dependency constraints, and explicit TBDs.
- `ARCHITECTURE.md` records the runtime/offline split, dependency direction,
  application boundaries, and Day 1 module boundary.
- `PLAN.md` contains only Contract Bootstrap and Day 1 tasks/gates.
- No source, tests, dependency configuration, fixtures, generated artifacts, or
  other implementation files were created or modified during bootstrap.

## Frozen Day 1 decisions

- Synthetic, offline-first, deterministic, and non-clinical boundary.
- Python 3.12 + `uv`; Pydantic v2 and Typer runtime; pytest, Ruff, and mypy
  development dependencies.
- Public model names listed in `SPEC.md`.
- SafetyAction exact four-value enum.
- Initial trajectory/policy/resource/evaluator/benchmark version token `v1`.
- `BenchmarkManifest`, `EvaluationManifest`, and `FinalAnswerView` fields defined
  in `SPEC.md`.
- Unknown schema/policy versions fail visibly.
- Runtime demonstration and offline evaluation core remain independent.
- Core-to-presentation/infrastructure dependency direction is prohibited;
  CLI/UI call application only.
- Day 1 stops at domain schema, validation, round-trip, and CLI help/version.
- `Turn` has exactly `turn_id`, `sequence`, `role`, and `text`; role accepts only
  `user` and `assistant`.
- `Trajectory` has exactly `trajectory_schema_version`, `trajectory_id`, `turns`,
  `process_markers`, and `safety_events`.
- `ProcessMarker` and `SafetyEvent` are embedded in `Trajectory`; `Finding`
  remains a standalone evaluator output validated against a trajectory.
- Exact public fields for `ProcessMarker`, `SafetyEvent`, `Finding`, and
  `CrisisResource` are frozen in `SPEC.md`.
- Every public model rejects unknown fields with no Day 1 extension mechanism.

## Assumptions

- Canonical JSON uses UTF-8, sorted keys, and stable compact separators, but hash
  and replay work remain outside Day 1.
- The benchmark target remains 8 matched pairs/16 trajectories plus four failure
  fixtures; this does not authorize creating fixtures on Day 1.

## D1.1 public contract resolution

### FROZEN evidence

- The owner froze the proposed minimal wire contract on 2026-08-29.
- One exact opaque version token, `v1`, is used for every initial version
  selector.
- Aggregate-level validation checks embedded marker/event references and
  standalone finding references without file I/O.
- All Day 1-blocking public schema and compatibility decisions are resolved.
- No package, source, test, fixture, policy, evaluator, detector, benchmark,
  adapter, service, or UI file was created during D1.1.

## Remaining TBDs

### TBD — required later, not a Day 1 blocker

- Exact benchmark case IDs, gold-label schema, rule IDs, and pair definitions.
- Canonical date/non-ASCII/newline serialization and hash algorithm before replay
  fixtures are frozen.

## Day 1 acceptance criteria

### COMPLETE

- Python 3.12 src-layout project with a committed `uv.lock`.
- Approved versioned models and valid trajectory domain round-trip.
- Explicit failures for duplicate/non-monotonic turns, invalid references,
  invalid resource dates, override suppression violations, and unknown versions.
- SafetyAction contains only the approved system actions.
- `FinalAnswerView` contains only `text` and `turn_id`.
- No risk score/level, probability, diagnosis, or clinical disposition fields.
- CLI supports help/version only.
- Focused pytest, Ruff format/check, mypy, and full pytest results recorded here.

## Commands run during Contract Bootstrap

### FROZEN evidence

- Read-only repository inventory, Git status/diff/tree inspection, and targeted
  guide searches completed successfully.
- No test, lint, type-check, benchmark, dependency installation, or implementation
  command was run because Contract Bootstrap is documentation-only.

## Commands run during D1.1

### FROZEN evidence

- Read `AGENTS.md`, `SPEC.md`, `ARCHITECTURE.md`, `PLAN.md`, `STATUS.md`, and the
  relevant domain-model passages in `CareLoop_Codex_工程化实施指南_ZH.md`: exit 0.
- `git status --short`: exit 0; only the pre-existing engineering guide was
  untracked before D1.1 edits.
- `git diff -- AGENTS.md SPEC.md ARCHITECTURE.md PLAN.md STATUS.md`: exit 0; no
  tracked diff existed before D1.1 edits.
- `rg -n "TBD|BLOCKED|extra=|Turn|Trajectory|ProcessMarker|SafetyEvent|Finding|CrisisResource" SPEC.md ARCHITECTURE.md PLAN.md STATUS.md`:
  exit 0; only the explicitly later, non-Day-1 TBD section remains.
- `git diff --check`: initially exit 2 because three edited Markdown lines had
  trailing spaces; those spaces were removed before the final check.
- Two narrow `rg` checks containing quoted space-separated patterns exited 2
  because `cmd.exe` split their arguments; no repository content was changed by
  those failed read-only checks.
- `rg -n TBD SPEC.md ARCHITECTURE.md PLAN.md STATUS.md`: exit 0; matches are the
  status vocabulary, completed D1.1 history, canonical JSON decisions deferred
  beyond round-trip, and benchmark-fixture decisions deferred beyond Day 1.
- `rg -n BLOCKED SPEC.md ARCHITECTURE.md PLAN.md STATUS.md`: exit 0; its only
  match is the recorded text of an earlier audit command, not a current blocker.
- `rg -n status: SPEC.md ARCHITECTURE.md PLAN.md STATUS.md`: exit 0; reports both
  contracts frozen, D1.1 complete, and implementation ready for D1.2.
- Final `git diff --check`: exit 0; only line-ending conversion warnings were
  emitted.
- Tests, Ruff, and mypy were not run because D1.1 changes documentation only and
  the package/tool configuration does not exist until D1.2.

## D1.2 package and tool scaffold

### Implemented

- Added a Python 3.12-only `uv` project using the uv native build backend and a
  `src/` package layout.
- Runtime dependencies are Pydantic v2 and Typer only. The development group is
  pytest, Ruff, and mypy only.
- Generated `uv.lock` with 23 resolved packages and synchronized a Python
  3.12.11 environment.
- Exposed package version `0.1.0` and a Typer CLI with only `--help` and
  `--version`; no business commands exist.
- Added an empty `careloop.domain` package boundary without implementing domain
  behavior.

### Commands and results

- `python -m pytest tests\test_cli.py -q`: exit 2, one collection error because
  `careloop` did not exist; this was the intended pre-implementation CLI test.
- `uv lock --offline --python 3.12`: first exit 2 because the sandbox could not
  initialize the user uv cache; with cache access it exited 1 because the local
  cache lacked the complete Pydantic dependency chain.
- `uv lock --python 3.12`: exit 0; resolved 23 packages using Python 3.12.11.
- First `uv sync --locked`: exit 1 because uv_build inferred
  `src/careloop_harness`; `module-name = "careloop"` was then configured.
- `uv lock --python 3.12`: exit 0 after the module-name correction.
- Final `uv sync --locked`: exit 0; all 23 packages audited.
- `uv run --locked python --version`: exit 0; `Python 3.12.11`.
- `uv run --locked careloop --help`: exit 0; displayed only `--version` and
  `--help` options.
- `uv run --locked careloop --version`: exit 0; output `0.1.0`.
- `uv run --locked pytest tests\test_cli.py tests\test_architecture.py -q`:
  exit 0; 3 passed.

## D1.3 failing domain contract tests

### Implemented

- Added synthetic-only contract tests for round-trip, duplicate IDs, sequence
  ordering, empty and unresolved turn references, override suppression,
  resource dates, exact action values, version rejection, forbidden clinical
  fields, unknown fields, final-answer isolation, and duplicate benchmark case
  IDs.
- Added an architecture test protecting the domain package from presentation,
  test, and network dependencies.
- `docs/safety_and_limitations.md` and `docs/test_matrix.md` were checked but do
  not yet exist. Tests therefore use the frozen `SPEC.md` and `ARCHITECTURE.md`
  contract and do not add safety policy or detector behavior.

### Commands and results

- `uv run --locked pytest tests\domain\test_contracts.py -q`: exit 1; 19 failed
  as expected because D1.4 models are intentionally absent.
- Initial `uv run --locked ruff format --check .`: exit 0; 12 files already
  formatted.
- Initial `uv run --locked ruff check .`: exit 1; two import-order findings.
- `uv run --locked ruff check . --fix`: exit 0; two mechanical import-order
  findings fixed.
- Final `uv run --locked ruff format --check .`: exit 0; 12 files already
  formatted.
- Final `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 3 source files.
- Final `uv run --locked pytest tests\test_cli.py tests\test_architecture.py -q`:
  exit 0; 3 passed.
- Final `uv run --locked pytest -q`: exit 1; 19 expected domain failures and 3
  passing scaffold/architecture tests. This is the required D1.3 red state, not
  a claim that the full suite passes.
- `uv lock --check`: exit 0; `pyproject.toml` and `uv.lock` are synchronized with
  23 resolved packages.
- `git diff --check`: exit 0; only Git line-ending conversion warnings were
  emitted for the four edited contract documents.

## D1.4 minimum versioned domain schema

### Implemented public schema

- `Turn`: exact fields `turn_id`, `sequence`, `role`, and `text`; only `user` and
  `assistant` roles are accepted.
- `Trajectory`: exact version, identity, ordered turns, embedded process markers,
  and embedded safety events. Aggregate validation rejects empty trajectories,
  duplicate turn IDs, non-increasing sequences, and unresolved marker/event turn
  references.
- `ProcessMarker`: exact marker, turn, observable type/value, source, and process
  policy version fields.
- `SafetyEvent`: exact triggering evidence, typed system action, override and
  suppression flags, sources, resource references, and crisis policy version.
  Required override with unsuppressed normal flow is rejected.
- `Finding`: exact rule, outcome, turn evidence, source, and evaluator version
  fields. `Trajectory.validate_finding` rejects unresolved standalone evidence.
- `EvaluationManifest`: independently stores trajectory, process, ethical,
  crisis, resource, and evaluator versions.
- `BenchmarkManifest`: stores benchmark/resource versions, explicit `as_of`, and
  ordered unique case IDs.
- `CrisisResource`: requires explicit jurisdiction/contact/source, allowlisting,
  resource version, and non-reversed verified/expiry dates. It performs no
  resource selection.
- `FinalAnswerView`: exposes exactly `text` and `turn_id`.
- `SafetyAction`: exposes exactly the four frozen system actions.
- All public models reject unknown fields and unknown versions. Identifier,
  reference, source, label, jurisdiction, contact, and URL strings reject blank
  values. No model contains a risk score/level, probability, diagnosis, or
  clinical disposition.

### Test-first evidence

- Added four test functions covering five previously implicit frozen cases:
  empty trajectories, blank turn IDs, unknown roles, unresolved process-marker
  references, and non-allowlisted resources.
- `uv run --locked pytest tests\domain\test_contracts.py -q` before behavior:
  exit 1; 23 failed because the models were absent.
- The same focused command after the minimum implementation: exit 0; 23 passed.
- Added exact field-set coverage for every public Pydantic model.
- Final focused `uv run --locked pytest tests\domain\test_contracts.py -q`:
  exit 0; 24 passed.

## D1.5 verification

### Required commands and real results

- First `uv run ruff format --check .`: exit 1; one long condition in
  `models.py` required formatting. It was corrected with a scoped edit.
- Final `uv run ruff format --check .`: exit 0; 13 files already formatted.
- Final `uv run ruff check .`: exit 0; all checks passed.
- Final `uv run mypy src`: exit 0; no issues in 4 source files.
- Final `uv run pytest -q`: exit 0; 27 passed in 0.15 seconds.
- `uv lock --check`: exit 0; the lock remains synchronized with 23 resolved
  packages.
- `git diff --check`: exit 0; only Git LF-to-CRLF conversion warnings were
  emitted for edited contract documents.
- `rg -n -e streamlit -e fastapi -e requests -e httpx -e typer src\careloop\domain`:
  exit 1 because no forbidden dependency match exists in the domain package.
- The benchmark command was not run because Day 1 did not add or change a
  benchmark runner, manifest, fixtures, gold labels, or result artifacts.

### Remaining risks outside Day 1

- `docs/safety_and_limitations.md` and `docs/test_matrix.md` are still absent.
  Day 1 implements typed safety evidence only, not detector, routing, policy, or
  resource-selection behavior.
- Canonical non-ASCII/date/newline/hash details remain intentionally unresolved
  before replay fixtures.
- Benchmark case IDs, pair definitions, rule IDs, and gold-label schema remain
  intentionally unresolved before benchmark fixture creation.

## Next exact action

Stop after Day 1. The current approved `PLAN.md` defines no later milestone.
Before further implementation, freeze a new milestone that preserves the
professional, crisis, dependency, evaluation-leakage, replay, and benchmark
boundaries in `AGENTS.md` and `ARCHITECTURE.md`.

## Milestone 2 frozen fixtures, canonical hash, and replay

### Implemented

- Preserved every Day 1 public model field and the exact `v1` version values.
  Added a separate internal frozen-trajectory artifact envelope instead of
  modifying `Trajectory`.
- Froze canonical JSON as UTF-8 without BOM/trailing newline, non-ASCII
  preserving, sorted-key, compact JSON with ISO dates. Froze self-describing
  SHA-256 hashes and exclusion of `canonical_hash` and `runtime_metadata` from
  hashed bytes.
- Added strict local artifact loading. It rejects noncanonical storage, unknown
  artifact/domain versions, invalid domain references, and content-hash
  mismatch.
- Implemented `ReplayArtifact` as a local-path-only application use case. It
  reconstructs canonical payload bytes, the hash, and the validated domain
  object without any adapter, model, network, evaluator, wall clock, or gold
  input.
- Added a deterministic fixture generator and `--check` mode. Generated all
  eight matched pairs (16 trajectories), 16 separately stored gold files, four
  independent failure fixtures, and the ordered `manifest.v1.json`.
- Froze manifest order as `p1-good`, `p1-bad`, through `p8-good`, `p8-bad`, with
  `benchmark_version=v1`, `as_of=2026-08-29`, and
  `resource_registry_version=v1`.
- Kept every final assistant turn byte-identical within its pair. The only
  primary contrast is the middle process behavior for P1/P2/P3/P5/P8, marker
  presence for P4, and crisis/fail-closed action evidence for P6/P7.
- Gold describes only observable frozen artifact behavior. P6 through P8 contain
  no severity or probability labels. All turn text is explicitly synthetic,
  contains no real identity information, and P8 preserves instruction-like text
  only as untrusted scenario data.
- Gold remains JSON data in a non-Python directory. Production code neither
  imports nor names a gold loader.

### Test-first and focused evidence

- Initial sandboxed `uv run --locked pytest tests\test_milestone2_artifacts.py -q`:
  exit 2 before test startup because the sandbox could not access the existing
  uv cache.
- Pre-implementation `uv run --locked pytest tests\test_milestone2_artifacts.py -q`
  with cache access: exit 2 with one expected collection error,
  `ModuleNotFoundError: careloop.application`.
- First post-implementation focused command: exit 0; 27 passed in 0.13 seconds.
- Expanded final focused/property command: exit 0; 29 passed in 0.13 seconds.
- `.venv\Scripts\python.exe tools\generate_milestone2_fixtures.py --check`:
  exit 0; all 37 generated JSON files exactly match generator output (16
  trajectories, 16 gold files, four failure fixtures, and one manifest).
- Initial `.venv\Scripts\ruff.exe format --check .`: exit 1; three new Python
  files required formatting. They were mechanically formatted.
- Initial `.venv\Scripts\ruff.exe check .`: exit 1; import/type-alias findings
  and fixture-source line-width findings were corrected without changing
  generated bytes.
- Initial `.venv\Scripts\mypy.exe src`: exit 1; four errors from a dynamically
  unpacked artifact constructor were fixed by explicit typed arguments.
- Final local preflight format/lint/mypy/generator checks all exited 0.

### Required full verification

- `uv run ruff format --check .`: exit 0; 21 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 10 source files.
- `uv run pytest -q`: exit 0; 56 passed in 0.24 seconds.
- `uv lock --check`: exit 0; the unchanged lock remains synchronized with 23
  resolved packages.
- `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`: exit 2;
  `No such command 'benchmark'`. This was run because benchmark fixtures changed.
  The result is the expected scope boundary: the Milestone 2 request explicitly
  prohibits implementing the benchmark CLI, so this is not reported as a pass.

### Explicitly unresolved and out of scope

- No CBT/MI/safety evaluator, policy registry, synthetic detector/router,
  resource selection, benchmark runner, report, Streamlit UI, adapter, or model
  call exists.
- P6 through P8 are frozen synthetic control-flow fixtures only. They provide no
  real-world detector validation, clinical classification, or safety claim.
- `docs/source_map.md` and `docs/test_matrix.md` do not yet exist. Milestone 3
  must create and freeze them before deriving evaluator rules; fixture gold is
  not an evaluator policy source.

## Next exact milestone

Stop after Milestone 3. Milestone 4 is the synthetic crisis-preemption and
ethical-policy milestone for P6 through P8. It must implement fail-closed routing,
override suppression, fixed-`as_of` locale-aware resource integrity, and output
policy tests without adding clinical risk classification or real-world claims.

## Milestone 3 deterministic process evaluator

### Implemented

- Created and froze `docs/source_map.md`, `docs/test_matrix.md`, and the current
  non-clinical limitations before evaluator logic. Gold is explicitly excluded
  as a policy source.
- Added `policies/process.v1.json` with exact `v1` policy/evaluator selectors,
  three source records, and seven ordered rules: collaborative agenda, autonomy
  after decline, permission before a fictional skill, diagnosis claim, action
  plan ownership, one agreed CBT skill path, and MI transition validity.
- Defined finding outcomes for violation-named rules: `present` is frozen
  observable violation evidence, `absent` requires a frozen counter-signal, and
  `uncertain` preserves insufficient evidence. Present evidence takes precedence
  over later counter-signals so a calm final turn cannot erase an earlier issue.
- Added strict immutable registry validation for unknown versions/fields,
  duplicate IDs, unresolved sources, and invalid transition metadata.
- Added pure session-shell, CBT-informed, MI-inspired, and aggregate process
  evaluators. They receive validated policy plus a complete ordered trajectory,
  return evidence-linked standalone findings in stable registry order, and do
  not import application, CLI/UI, gold, benchmark labels, provider/network code,
  safety runtime, report code, or wall clock.
- Froze the MI graph with adjacent forward/backward movement and self-transition.
  Planning is optional; fewer than two markers is uncertain. Support-only,
  no-plan, and user-decline endings do not create a violation.
- Enforced at most one agreed CBT skill path by counting marker records, including
  multiple marker records attached to the same turn.
- Under the owner's explicit authorization to revise frozen details for full Day
  3 completion, aligned P3 with permission-before-skill and P4 with diagnosis
  claim detection. P3/P4 retain a single middle-turn text contrast and identical
  final assistant text within each pair.
- Updated the generator, then regenerated P3/P4 trajectory bytes/hashes and
  P1–P5 gold rule/source/outcome metadata. No generated JSON was hand-edited.
  Day 1 public schemas, dependencies, lockfile, P6–P8 fixtures, and manifest case
  order remain unchanged.

### Test-first and focused evidence

- Initial sandboxed
  `uv run --locked pytest tests\process\test_process_evaluator.py tests\test_architecture.py -q`:
  exit 2 before test startup because the sandbox could not access the existing
  uv cache.
- The same pre-implementation command with cache access: exit 2 with the expected
  collection error `ModuleNotFoundError: No module named 'careloop.process'`.
- First post-implementation focused command: exit 1; 20 passed and four failed.
  All four failures were the pre-identified P3/P4 frozen-fixture conflict.
- After generator-owned P3/P4 alignment,
  `uv run --locked pytest tests\process\test_process_evaluator.py tests\test_milestone2_artifacts.py tests\test_architecture.py -q`:
  exit 0; 53 passed in 0.18 seconds.
- Final focused command after same-turn marker and untrusted-user-text coverage:
  exit 0; 54 passed in 0.17 seconds.
- `.venv\Scripts\python.exe tools\generate_milestone2_fixtures.py --check`:
  exit 0; all generated files match generator output.

### Preflight quality evidence

- Initial `.venv\Scripts\ruff.exe format --check .`: exit 1; seven new Python
  files required mechanical formatting.
- Initial `.venv\Scripts\ruff.exe check .`: exit 1; 11 line-length findings.
- Initial `.venv\Scripts\mypy.exe src`: exit 1; two `Literal` type-width errors.
- `.venv\Scripts\ruff.exe format .`: exit 0; seven files reformatted.
- Final local format check: exit 0; 32 files already formatted.
- Final local Ruff check: exit 0; all checks passed.
- Final local mypy: exit 0; no issues in 17 source files.
- Final local fixture generator check: exit 0.

### Required full verification

- `uv run ruff format --check .`: exit 0; 32 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 17 source files.
- `uv run pytest -q`: exit 0; 80 passed in 0.64 seconds.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock is
  synchronized.
- `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`: exit 2;
  `No such command 'benchmark'`. The command was required because generated
  benchmark fixtures changed. Milestone 3 explicitly excludes implementing the
  benchmark CLI, so this is recorded as an unresolved scope limitation and is
  not claimed as a pass.

### Remaining risks and explicit exclusions

- Exact phrase matching is deliberately limited to frozen synthetic artifacts;
  it is not natural-language understanding and cannot support clinical or
  real-world performance claims.
- The owner-authorized P3/P4 and P1–P5 gold revision retains benchmark version
  `v1` before any benchmark runner exists. This exception is documented in
  `SPEC.md` and is a version-history limitation for later independent review.
- No final-answer evaluator, safety detector/router, ethical engine, resource
  selection, benchmark/report pipeline, CLI business command, UI, adapter,
  model/provider, or network behavior was added.

## Milestone 4 crisis preemption and ethical policy engine

### Implemented

- Added strict `crisis.v1`, `ethical.v1`, and `resources.v1` registries with exact
  version rejection, duplicate/reference validation, and documented local source
  provenance. Gold is not a policy source.
- Implemented `SyntheticSafetySignalDetector` as exact matching of explicit
  synthetic tags only. Ambiguous/historical/third-party/quoted contexts map to
  clarify; current plan/preparation/already-acted tags map to the typed
  emergency-help action. No risk category or probability exists.
- Implemented crisis routing before the injected responder. Every matched signal
  creates a typed override event, suppresses normal flow, and leaves responder
  call count at zero.
- Implemented resource selection using only explicit jurisdiction and `as_of`.
  It requires exact locale, active dates, allowlisting, registered `.invalid`
  source URL, unique ID/jurisdiction, and registry version. Missing, wrong,
  stale, invalid, or failed resource evidence never guesses a contact.
- Added an ethical output gate after responder execution but before visibility.
  Ten ordered observable categories cover role impersonation, diagnosis,
  medication, coercion, invalidation, over-reassurance, dependency,
  confidentiality, clinical overclaim, and crisis-flow continuation.
- Detector, router, resource-loader, and output-policy exceptions return a typed
  `HUMAN_REVIEW_REQUIRED` fail-closed result with a suppressed event and no
  visible normal output. No exception path resumes ordinary flow.
- Preserved blocked output only as internal audit evidence so its Finding turn
  reference can be validated; `visible_output` remains empty.
- Proved scenario prompt injection remains inert data, a single denial cannot
  release `you are safe`, and ordinary CBT continuation after override creates
  the dedicated crisis-flow finding.
- Under the owner's explicit authorization, updated the generator and regenerated
  all six P6–P8 trajectory files and six gold files. P6 now freezes ambiguous
  clarification, P7 current-plan emergency override, and P8 correct-versus-wrong
  synthetic jurisdiction resource evidence. Generated JSON was not hand-edited.
- Day 1 public models, dependency set, lockfile, manifest case order, and P1–P5
  fixtures remain unchanged.

### Test-first and focused evidence

- Pre-implementation
  `uv run --locked pytest tests\safety tests\test_architecture.py -q`: exit 2
  with two expected collection errors,
  `ModuleNotFoundError: No module named 'careloop.safety'`.
- First post-implementation focused command: exit 1; 36 passed and three failed.
  All three failures were the pre-identified P6/P7/P8 fixture conflict.
- After generator-owned P6–P8 alignment,
  `uv run --locked pytest tests\safety tests\test_milestone2_artifacts.py tests\test_architecture.py -q`:
  exit 0; 68 passed in 0.19 seconds.
- Final focused command after ordering, blocked-output evidence, API field, and
  wall-clock guards: exit 0; 71 passed in 0.19 seconds.
- `.venv\Scripts\python.exe tools\generate_milestone2_fixtures.py --check`:
  exit 0; all generated files match generator output.

### Preflight quality evidence

- Initial `.venv\Scripts\ruff.exe format --check .`: exit 1; nine Python files
  required mechanical formatting.
- Initial `.venv\Scripts\ruff.exe check .`: exit 1; three line-length findings.
- Initial `.venv\Scripts\mypy.exe src`: exit 0; no issues in 24 source files.
- Initial local generator check: exit 0.
- `.venv\Scripts\ruff.exe format .`: exit 0; nine files reformatted.
- Final local format check: exit 0; 41 files already formatted.
- Final local Ruff check: exit 0; all checks passed.
- Final local mypy: exit 0; no issues in 24 source files.
- Final local fixture generator check: exit 0.

### Required full verification

- `uv run ruff format --check .`: exit 0; 41 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 24 source files.
- `uv run pytest -q`: exit 0; 120 passed in 0.32 seconds.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock remains
  synchronized.
- `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`: exit 2;
  `No such command 'benchmark'`. The command was required because P6–P8 benchmark
  fixtures changed. Milestone 4 explicitly excludes the Milestone 5 benchmark
  CLI, so this is not claimed as a pass.

### Remaining risks and explicit exclusions

- Exact tags and exact output phrases prove only deterministic behavior on frozen
  synthetic inputs. They provide no evidence of real-world detection, clinical
  correctness, treatment quality, or safety improvement.
- Resource entries are deliberately synthetic `.invalid` fixtures and must never
  be presented as real help contacts.
- The owner-authorized P6–P8/gold revision retains benchmark version `v1` before
  a runner exists. This remains a documented version-history limitation.
- No final-answer evaluator, application orchestration, benchmark/report runner,
  CLI business command, UI, real adapter, model/provider, network access,
  database, or deployment behavior was added.

## Next exact milestone

Stop after Milestone 4. Milestone 5 composes the verified core into exactly three
application use cases (`EvaluateTrajectory`, `ReplayArtifact`, and
`RunBenchmark`), their CLI commands, and an optional minimal read-only audit UI.
It must not change frozen process or safety policy behavior.
