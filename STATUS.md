# CareLoop Harness Status

Current phase: Milestone 15 complete
Next milestone: Milestone 16 — research Web/API, OIDC, reports, and Docker Compose
Implementation status: COMPLETE for D1.0–D1.5 and M2.1–M15

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

### M8 upstream pull and main merge-conflict resolution

- Committed the already verified M8 tree as `2c17370`
  (`feat-m8-freeze-agent-runtime-contract`). The owner's pre-existing
  `.python-version` and Chinese implementation-guide file were explicitly
  excluded.
- `git fetch origin --prune`: exit 0; updated
  `origin/feat/m7-final-reproduction` from `ffdd0f1` to `eceecef` and
  `origin/main` from `c9b9bea` to `f1ef18d`.
- `git pull --no-rebase --no-edit`: exit 0; created merge commit `a56be79`
  with the ort strategy and no content conflict.
- `git merge --no-edit origin/main`: exit 1 with four expected content
  conflicts in `PLAN.md`, `README.md`, `STATUS.md`, and
  `tests/test_delivery_contract.py`.
- Resolved each hunk by retaining main's completed M7 history and the
  owner-approved additive M8 contract/status. No whole-file ours/theirs
  selection, reset, fixture edit, or generated-artifact edit was used.
- `git diff --name-only --diff-filter=U` and `git ls-files -u`: exit 0 with
  no output after staging the four resolutions.
- Post-resolution `uv run --locked ruff format --check .`: exit 0; 72 files
  already formatted.
- Post-resolution `uv run --locked ruff check .`: exit 0; all checks passed.
- Post-resolution `uv run --locked mypy src`: exit 0; no issues in 41 source
  files.
- Post-resolution `uv run --locked pytest -q`: exit 0; 198 passed in 0.60
  seconds.
- Concluded the main merge as `213e5c1`
  (`merge-origin-main-resolve-m8-conflicts`).
- Both `git merge-base --is-ancestor origin/main HEAD` and
  `git merge-base --is-ancestor origin/feat/m7-final-reproduction HEAD`
  exited 0. The branch is four commits ahead and zero behind its upstream.
- No push was performed as part of the pull/merge request.

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

## Milestone 5 application, CLI, and static audit

### Approved contract and pre-implementation red state

- The owner selected deterministic static offline HTML, an evidence ledger with
  no aggregate score, and a dedicated milestone branch. Work began on
  `feat/m5-application-cli-audit` from `df9efaa`.
- M5 freezes final-only and complete-trajectory evaluator inputs, a separate
  offline safety-artifact observation registry, post-evaluation gold loading,
  deterministic raw JSON/JSONL, exact CLI commands, and escaped no-script HTML.
- No Day 1 public schema, process/crisis/ethical/resource runtime behavior,
  dependency, frozen trajectory, or gold label is authorized to change.
- Pre-implementation focused command:
  `.venv\Scripts\python.exe -m pytest tests\evaluation tests\presentation tests\e2e tests\test_cli.py tests\test_architecture.py -q`.
  It exited 2 with three expected collection errors because
  `EvaluateTrajectory` was not yet exported from `careloop.application`.

### Implemented

- Added strict `evaluation.v1` policy metadata for three offline observations:
  ambiguous clarify override, emergency-help override, and exact active
  synthetic resource identity. This registry observes frozen artifacts and does
  not alter any Milestone 4 runtime policy or behavior.
- Added `FinalAnswerEvaluator` with an enforced `FinalAnswerView` input. It emits
  the same ordered ten-rule ledger while history-dependent rules remain
  `uncertain`; it cannot receive markers, safety events, resources, gold, file
  paths, adapters, network, or wall clock.
- Added `TrajectoryEvaluator`, combining the unchanged seven process rules with
  three offline safety-artifact rules. P1–P8 localize their frozen middle-turn,
  source-linked action, or resource contrast at the expected evidence turn.
- Added `EvaluateTrajectory`. It verifies one canonical artifact, chooses the
  final assistant turn, runs both evaluator boundaries, resolves registered
  synthetic resource provenance, and optionally writes canonical raw JSON with
  no gold/comparison content.
- Preserved `ReplayArtifact` and added `RunBenchmark`. The benchmark follows all
  16 manifest cases and invokes the injectable gold loader only after the actual
  result for that case exists. Comparison checks rule, outcome, turn, source,
  and evaluator version while retaining but not comparing finding identity.
- Added deterministic benchmark JSONL with one final newline and no timestamp or
  duration. Re-running the command produced identical bytes.
- Replaced the help/version-only CLI boundary with exactly `evaluate`, `replay`,
  and `benchmark`. Valid application/data failures exit one; usage errors remain
  exit two.
- Added the owner-selected static HTML audit: timeline, finding-to-turn links,
  side-by-side evidence ledgers, suppression banner, resource provenance, and
  replay hash. It escapes untrusted artifact text and contains inline CSS only,
  with no script, remote asset, editable control, server, or aggregate score.
- Generated, through the CLI only, `artifacts/raw/benchmark.v1.jsonl`, one
  `p8-good` evaluation JSON, and its HTML audit. No generated file was hand
  edited.

### Test-first, focused, and regression evidence

- First post-implementation focused run without an explicit pytest temp path:
  23 passed and seven setup errors because the environment denied access to
  `C:\Users\guosh\AppData\Local\Temp\pytest-of-guosh`; no test body failed.
- The same focused scope with an explicit writable `--basetemp`: exit 0;
  30 passed.
- Expanded focused application/evaluation/presentation/CLI/architecture and
  Milestone 2 artifact regression suite: exit 0; 61 passed in 0.35 seconds.
- First full suite after implementation: 144 passed and one failed. The frozen
  gold-isolation test found only the CLI default-path literal
  `benchmarks/gold`; composing the same path from two segments removed the
  misleading production-source marker without weakening the test or changing
  load order.
- Final local full suite with explicit writable temp path: exit 0; 147 passed in
  0.39 seconds.
- Fixture generator check: exit 0; every existing trajectory/gold/failure
  fixture still exactly matches generator output.

### Required full verification

- `uv run ruff format --check .`: exit 0; 55 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 34 source files.
- Final `uv run pytest -q`: exit 0; 148 passed in 0.41 seconds.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock is
  synchronized.
- `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`: exit 0;
  16 cases evaluated and raw JSONL written to
  `artifacts/raw/benchmark.v1.jsonl`.
- Local CLI smoke commands for evaluate, replay, and benchmark all exited 0.
  Evaluate wrote ten final-only and ten trajectory-aware findings; replay
  verified the frozen P1 hash; benchmark wrote 16 ordered records.
- Repeated artifact Git blob hashes were unchanged:
  benchmark JSONL `710032423c367587780d7533db9f20f0e457d326`, P8 evaluation
  JSON `c6e8f5b38dbec9eef963112f1142e9b7ef2ee315`, and P8 audit HTML
  `6008780acedf24c3e81dcc8887857c123817e648`.

### Schema, policy, fixture, dependency, and risk statement

- No Day 1 public schema, process/crisis/ethical/resource policy behavior,
  frozen trajectory, gold label, dependency, lock entry, or package version
  changed. The only new policy is the internal offline `evaluation.v1` registry.
- Exact tag/phrase and typed-event agreement proves deterministic behavior on
  the frozen synthetic corpus only. It is not clinical, real-world, population,
  or statistical performance evidence.
- The HTML contract is covered by deterministic, escaping, no-script/no-remote-
  asset smoke tests. A visual browser screenshot was not produced because no
  browser executable is installed in this environment.
- Aggregate summary metrics, raw-to-summary derivation, CI, threat model,
  README/technical report, and mutation proof remain explicitly unimplemented
  until Milestone 6.

## Next exact milestone

Stop after Milestone 5. Milestone 6 must derive only the allowed synthetic
benchmark summaries from raw JSONL, add CI and technical documentation, and run
the temporary P7 mutation proof. It must not change evaluator decisions, gold,
frozen fixtures, or introduce an aggregate clinical/quality score.

## Milestone 6 derived reports, CI, documentation, and mutation proof

### Frozen scope and implementation

- Work began on `feat/m6-benchmark-ci-docs` from Milestone 5 commit `369d586`.
- Froze a separate verification raw stream so the existing 16-record
  manifest-order benchmark JSONL and its bytes remain unchanged.
- Extended `RunBenchmark`, without adding a fourth application use case, to
  replay all 16 evaluated local artifacts and exercise the four frozen failure
  fixtures for exact expected rejection categories.
- Added `careloop.reporting` with strict canonical raw parsers, immutable raw and
  summary models, nine ordered allowed metrics, canonical summary JSON, and
  deterministic Markdown. Derivation loads neither evaluators, policy registries,
  CLI/presentation, nor gold files.
- Summary metrics contain only satisfied/applicable counts plus satisfied and
  unsatisfied evidence IDs. No percentage, combined score, rank, confidence,
  significance, clinical metric, or population estimate exists.
- The benchmark CLI now writes benchmark raw, verification raw, summary JSON,
  and summary Markdown. All result artifacts were generated through that CLI;
  no generated number was edited manually.
- Added a least-privilege GitHub Actions workflow with immutable official action
  SHAs. It performs locked sync, format, lint, mypy, pytest, benchmark, and a
  generated-artifact diff check in order.
- Added README first-screen boundaries, a threat model, and a technical report
  that links to generated evidence instead of copying result counts.

### Test-first and focused evidence

- Pre-implementation focused command:
  `.venv\Scripts\python.exe -m pytest tests\reporting\test_summary.py tests\test_delivery_contract.py tests\e2e\test_cli_commands.py tests\test_architecture.py --basetemp .pytest-tmp-m6-red -q`.
  It exited 2 during collection with the expected missing M6 export,
  `ImportError: cannot import name 'BenchmarkReportPaths'`.
- First post-implementation focused command: exit 1; 16 passed and two failed.
  One README phrase crossed a line boundary. The other test incorrectly banned
  raw `gold_*` comparison field names instead of banning gold imports/loaders;
  it was corrected to enforce the actual architecture invariant without changing
  application behavior.
- Final focused command: exit 0; 18 passed in 0.30 seconds.
- Expanded reporting/evaluation/safety/E2E/artifact/CLI/architecture regression
  command: exit 0; 106 passed in 0.50 seconds.
- Staged-diff review added a manifest-order regression test. Before the parser
  guard it exited 1 because reordered canonical records were accepted; after the
  minimum v1 order check the same test exited 0 with one pass in 0.11 seconds.
- Initial local preflight found four unformatted files, one import-order issue,
  line-width/generic-style issues, and seven mypy errors. Mechanical formatting
  plus explicit typed metric/observation boundaries corrected them.
- Final local preflight: format 71 files, Ruff passed, and mypy passed for 37
  source files.

### P7 mutation proof

- Created a detached temporary worktree at Milestone 5 commit `369d586` and
  changed only its safety runtime so `current_plan` bypassed override and called
  the ordinary responder.
- The first attempted mutation command loaded the main editable package and
  passed; it was rejected as invalid evidence rather than reported as proof.
- Valid red command, with the temporary `src` placed first by pytest:
  `C:\Users\guosh\project\care-harness\.venv\Scripts\python.exe -m pytest -o pythonpath=src tests\safety\test_safety_runtime.py::test_p7_current_plan_fixture_uses_emergency_action_and_zero_agent_calls --basetemp C:\Users\guosh\AppData\Local\Temp\careloop-m6-mutation-proof\.pytest-mutation-2 -q`.
  It exited 1; the assertion showed responder call count `1` instead of `0`.
- Restored the single temporary mutation and ran the same targeted test with a
  fresh basetemp. It exited 0; one test passed in 0.10 seconds.
- The temporary worktree had no content diff after restoration and was removed
  from Git's worktree registry. No deliberately broken code entered this branch.

### Required full verification

- First sandboxed
  `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`: exit 2
  before project startup because the sandbox could not access the existing uv
  cache. The same command with cache access exited 0 and generated all M6 raw and
  summary artifacts.
- `uv run ruff format --check .`: exit 0; 64 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 37 source files.
- An intermediate final `uv run ruff format --check .` exited 1 for one newly
  added test expression; Ruff mechanically formatted that file before the full
  sequence was restarted.
- Final `uv run ruff format --check .`: exit 0; 64 files already formatted.
- Final `uv run ruff check .`: exit 0; all checks passed.
- Final `uv run mypy src`: exit 0; no issues in 37 source files.
- Final `uv run pytest -q`: exit 0; 157 passed in 1.01 seconds.
- Final `uv run careloop benchmark --manifest benchmarks/manifest.v1.json`:
  exit 0; 16 benchmark cases, 20 verification records, and both derived summary
  formats written.
- `.venv\Scripts\python.exe tools\generate_milestone2_fixtures.py --check`:
  exit 0; all frozen generated fixtures remain unchanged.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock remains
  synchronized.
- `uv run pytest tests\reporting\test_summary.py::test_recomputing_summary_from_unchanged_raw_is_byte_identical -q`:
  exit 0; one raw-to-summary recomputation test passed in 0.14 seconds.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0 after the
  final benchmark regeneration; tracked generated files match staged bytes.
- `git diff --cached --check`: exit 0; the complete 25-file staged change has no
  whitespace error.

### Generated evidence and change boundary

- Existing benchmark JSONL Git blob remained
  `710032423c367587780d7533db9f20f0e457d326`, identical to Milestone 5.
- New verification JSONL Git blob:
  `4303d9f5e431e622b6f1f8dbde839b60009ec837`.
- New summary JSON Git blob:
  `ef1ad32376c5173d66375b7aaef4cdd403b1f0f8`.
- New summary Markdown Git blob:
  `7258b620cb5400d1c28e0a5acf32bafe2a4b0ef8`.
- No public schema, evaluator decision, process/crisis/ethical/resource/evaluation
  policy, frozen trajectory, gold label, dependency, lock entry, or package
  version changed.
- These counts prove only deterministic behavior for frozen synthetic artifacts.
  The first hosted GitHub Actions execution exposed the CLI-help portability
  regression recorded below.

### M6 hosted CI portability regression

- The first hosted Linux command `uv run --locked pytest -q` exited 1 with one
  failed and 156 passed tests. Rich ANSI styling split the raw `--version` byte
  sequence even though the rendered help was successful and showed the option.
- The CLI contract test now forces colored output, removes ANSI control sequences
  with a standard-library regular expression, and asserts the visible
  `--version`, `Commands`, `evaluate`, `replay`, and `benchmark` text. This adds
  no dependency and does not change CLI or application behavior.
- A local forced-color run before normalization exited 0 with two passed tests,
  confirming the triggering rendering difference is platform-specific rather
  than reproducible on Windows.
- The first normalization attempt imported transitive package `click`; focused
  collection exited 2 with `ModuleNotFoundError`. It was replaced rather than
  adding or exposing a dependency.
- Final `uv run --locked pytest tests\test_cli.py -q`: exit 0; two passed in
  0.17 seconds.
- Final `uv run --locked ruff format --check .`: exit 0; 64 files already
  formatted.
- Final `uv run --locked ruff check .`: exit 0; all checks passed.
- Final `uv run --locked mypy src`: exit 0; no issues in 37 source files.
- Final `uv run --locked pytest -q`: exit 0; 157 passed in 0.53 seconds.
- Final `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases and all four artifact paths
  were written.
- Final `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0;
  tracked generated artifacts are byte-identical.
- No evaluator, safety behavior, gold label, frozen fixture, generated artifact,
  public schema, dependency, or lock entry changed in this CI-only correction.

### M6 PR #6 merge-conflict resolution

- Fetched `origin/main` at `c9b9bea` and confirmed from the GitHub PR metadata
  that PR #6 targets `main` from `feat/m6-benchmark-ci-docs`.
- `git merge --no-commit --no-ff origin/main` exposed 28 conflicted paths.
  The code, architecture, test, and documentation conflicts were M6 additions
  over the same M5 content already represented in `main`, so the M6 versions
  were retained.
- The only tree difference between the M6 base `369d586` and current `main` was
  an added EOF newline in 14 frozen gold/trajectory JSON files. An initial
  resolution that accepted those bytes made `uv run --locked python
  tools\generate_milestone2_fixtures.py --check` exit 1 at
  `benchmarks\gold\p1-good.json`. The files were restored to the
  generator-produced M6 bytes; no frozen semantic content or canonical hash
  changed.
- Final `uv run --locked python
  tools\generate_milestone2_fixtures.py --check`: exit 0.
- Focused `uv run --locked pytest
  tests\test_milestone2_artifacts.py tests\test_cli.py
  tests\e2e\test_cli_commands.py tests\reporting\test_summary.py -q`:
  exit 0; 40 passed in 0.38 seconds.
- `uv run --locked ruff format --check .`: exit 0; 64 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 37 source files.
- `uv run --locked pytest -q`: exit 0; 157 passed in 0.54 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases and all four artifact
  paths were written.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0;
  generated artifacts remain byte-identical.
- No evaluator decision, safety behavior, public schema, dependency, lock entry,
  frozen fixture, gold label, or generated artifact changed.

## Milestone 7 clean reproduction and final review

### README and interaction contract

- Work began on `feat/m7-final-reproduction` from the conflict-free M6 commit
  `dd9adb4`.
- Added a delivery-contract test before the README change. The red command
  `uv run --locked pytest tests\test_delivery_contract.py -q` exited 1
  with one failed and three passed tests because the M7 completion/interaction
  statements were absent.
- The README now records the closed v1 milestone status, complete lockfile
  reproduction sequence, generated-artifact ownership, maintenance rules, and
  evidence/interpretation boundary.
- The README explicitly states that CLI is the primary interaction surface,
  there is no web application/API/server/chat/upload session, and optional
  audit HTML is a local read-only static file.
- The same focused delivery-contract command after the README change exited 0;
  four tests passed in 0.01 seconds.
- README/test commit used for clean reproduction:
  `44cbce745f1d5d23a001e0daa627aebd0de471b1`.

### Clean lockfile reproduction

- Created detached worktree
  `C:\Users\guosh\AppData\Local\Temp\careloop-m7-repro-44cbce7`
  at `44cbce7`; `Test-Path .venv` returned `False` before synchronization.
- `uv sync --locked`: exit 0; created a new `.venv` with CPython 3.12.11,
  resolved and installed 23 locked packages, and installed CareLoop Harness
  0.1.0 from the isolated checkout.
- `uv lock --check`: exit 0; 23 packages resolved.
- `uv run --locked python --version`: exit 0; Python 3.12.11.
- `uv run --locked careloop --version`: exit 0; `0.1.0`.
- `uv run --locked careloop --help`: exit 0; exposed help/version plus exactly
  `evaluate`, `replay`, and `benchmark`.
- `uv run --locked ruff format --check .`: exit 0; 63 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 37 source files.
- `uv run --locked pytest -q`: exit 0; 158 passed in 0.66 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases and all four artifact
  paths were written.
- `uv run --locked python
  tools\generate_milestone2_fixtures.py --check`: exit 0.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0;
  regenerated artifacts were byte-identical.
- Final isolated `git status --short`: exit 0 with no tracked or untracked
  output. The exact temporary worktree and its generated `.venv` were removed
  after review; `Test-Path` returned `False`.

### Separate strict read-only final review

- After reproduction, no file in the isolated checkout was edited during the
  review phase.
- `git diff --exit-code dd9adb4 44cbce7 -- src policies benchmarks artifacts
  pyproject.toml uv.lock`: exit 0; M7 changed no implementation, policy, frozen
  input, generated evidence, dependency declaration, or lock entry.
- `git diff --check dd9adb4..44cbce7`: exit 0.
- An initial dependency search using unquoted pipe-separated alternatives
  exited 255 because `cmd.exe` interpreted the pipes. It changed no file and
  was replaced with explicit ripgrep `-e` arguments.
- Final `rg -n -i -e streamlit -e fastapi -e flask -e uvicorn -e websocket
  -e httpx -e requests -e socketserver -e http.server pyproject.toml src`:
  exit 1 with no matches, which is the expected negative result.
- Direct inspection of `pyproject.toml` confirmed only Pydantic and Typer at
  runtime and pytest, Ruff, and mypy for development. The sole project entry
  point is `careloop = careloop.cli:main`.
- Direct inspection of `src/careloop/presentation/audit_html.py` confirmed
  deterministic escaped HTML bytes, inline CSS, local file output, and no
  script, remote asset, server, editable control, or network implementation.
- Final isolated `git status --porcelain=v1`: exit 0 with no output.
- Review result: no blocker. README is operating guidance, not independent
  evidence; the source, lockfile, tests, raw artifacts, and Git diff support
  the recorded conclusions.

### Final primary-worktree verification

- `uv lock --check`: exit 0; 23 packages resolved.
- `uv run --locked ruff format --check .`: exit 0; 64 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 37 source files.
- `uv run --locked pytest -q`: exit 0; 158 passed in 0.55 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases and all generated paths
  were written.
- `uv run --locked python
  tools\generate_milestone2_fixtures.py --check`: exit 0.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0.
- No public schema, evaluator decision, process/crisis/ethical/resource/
  evaluation policy, frozen fixture, gold label, dependency, lock entry,
  package version, generated artifact, or application behavior changed.

### Residual limitations

- Deterministic success applies only to the frozen synthetic corpus and exact
  local contracts. It provides no clinical, real-world safety, treatment,
  population, or statistical evidence.
- There is deliberately no interactive web product. The optional audit surface
  is a generated local static HTML file and was not turned into a server or UI
  application in M7.
- The hosted CI run for the final M7 branch is not independently observed until
  the branch is pushed.

## M7 closing state (superseded by M8 owner approval)

At M7 close, no Milestone 8 had been planned. The later owner-approved
full-stack research contract authorized M8 while preserving the frozen
professional, safety, architecture, replay, gold-isolation, and reporting
boundaries.

## Milestone 8 synthetic agent-runtime contracts and state machine

### Owner-approved change boundary

- The owner approved the full-stack research plan after M7. In accordance with
  the one-milestone rule, this delivery implements M8 only and stops before the
  provider/plugin runtime planned for M9.
- Added a provider-neutral inner `careloop.agent_runtime` package. It contains
  strict `v1` schemas, an asynchronous model port, an explicit session
  transition table, and a validated append-only runtime-event model.
- Frozen non-clinical routing, draft, review, provenance, plugin manifest, future
  HTTP, logical persistence, and threat boundaries. The interaction remains
  synthetic role-play for researchers and admissions reviewers.
- Draft release requires a checked or explicitly reviewed path. Critical
  runtime failure fails closed, terminal states cannot reopen, and rewriting is
  limited to two attempts.
- The existing Day 1 domain models, evaluator rules, CLI commands, frozen
  fixtures, gold data, benchmark, generated artifacts, dependencies, and
  lockfile did not change.
- No Web server, database, plugin loader, cloud adapter, model call, credential
  access, network behavior, real-user workflow, or clinical capability was
  added.

### Test-first and focused evidence

- Initial `uv run --locked pytest tests\agent_runtime
  tests\test_agent_runtime_contract_docs.py -q`: exit 2 during collection with
  two expected `ModuleNotFoundError` errors because
  `careloop.agent_runtime` did not exist.
- After the initial implementation, `uv run --locked pytest
  tests\agent_runtime tests\test_agent_runtime_contract_docs.py
  tests\test_architecture.py -q`: exit 0; 42 passed in 0.17 seconds.
- After the complete documentation contract, `uv run --locked pytest
  tests\agent_runtime tests\test_agent_runtime_contract_docs.py
  tests\test_architecture.py tests\test_delivery_contract.py -q`: exit 0;
  47 passed in 0.15 seconds.
- The first full `uv run --locked pytest -q`: exit 2 during collection because
  the new test basename duplicated `tests/domain/test_contracts.py`. The new
  test file was renamed without changing behavior.
- The next full `uv run --locked pytest -q`: exit 0; 194 passed in 0.77
  seconds.
- Runtime-event completeness red test, `uv run --locked pytest
  tests\agent_runtime -q`: exit 2 during collection because `RuntimeEvent`
  was intentionally not implemented yet.
- After adding the event schema and remaining validation, the same focused
  command exited 0; 37 passed in 0.09 seconds.

### Required final verification

- `uv run --locked ruff format --check .`: exit 0; 72 files already
  formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 41 source files.
- `uv run --locked pytest -q`: exit 0; 198 passed in 0.56 seconds.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks artifacts
  policies`: exit 0; dependencies, lock entries, frozen inputs, policies, and
  generated evidence are unchanged.
- Benchmark regeneration was not run because M8 changes no benchmark input,
  evaluator, raw record, summary, or generated artifact.

### Residual limitations

- The model port and future HTTP/database/plugin descriptions are contracts,
  not implemented adapters or an operational full-stack product.
- Deterministic state-machine and schema tests do not establish model-output
  safety, clinical validity, real-world crisis handling, or effective human
  review.
- The working tree still contains the owner's pre-existing untracked
  `.python-version` and Chinese implementation-guide file; M8 did not modify
  or add them to its change set.

## Next exact milestone

Stop after Milestone 8. Milestone 9 is allowlisted plugin discovery and a
provider-neutral model runtime using deterministic test adapters before any
real cloud connection.

## Milestone 9 allowlisted plugin discovery and model runtime

### Implemented change boundary

- Added strict immutable `PluginAllowlistEntry` and `PluginAllowlistV1`
  contracts for exact local entry-point name/value and plugin ID/version
  pinning. The only discovery group is `careloop.plugins.v1`.
- Added removable `careloop.plugin_runtime` discovery. It matches the allowlist
  before `load()`, never loads unapproved candidates, validates the returned
  `PluginManifestV1`, rejects missing/ambiguous/invalid/mismatched entries, and
  returns a deterministic dependency-before-dependant catalog. Missing
  dependencies and cycles reject.
- Added `ProviderNeutralModelRuntime` over the existing asynchronous `ModelPort`.
  A valid exact request/provider/model response remains a `quarantined_draft`
  and emits the validated `DRAFT_GENERATED` transition.
- Added five stable `ModelRuntimeFailureCode` categories for provider exception,
  invalid draft, request mismatch, provider mismatch, and model mismatch. Each
  failure retains no draft or exception text and emits `RUNTIME_FAILURE` to
  `FAILED_CLOSED` with category-only evidence.
- Provider-returned `ModelDraft` instances are dumped and revalidated, so an
  adapter cannot bypass validation with `model_construct`.
- Froze M9 behavior and limitations in `SPEC.md`, `ARCHITECTURE.md`, the agent
  runtime contract, threat model, safety limitations, test matrix, and README.
- Added no dependency, project entry point, plugin package, default allowlist,
  provider SDK, real adapter, credential access, network call, CLI command,
  persistence, Web/API/UI behavior, evaluator/policy change, or generated
  artifact change. Deterministic adapters exist only in tests.

### Test-first and focused evidence

- Baseline `uv run --locked pytest -q`: exit 0; 198 tests passed in 0.57
  seconds before M9 edits.
- First sandboxed focused command, `uv run --locked pytest
  tests\plugin_runtime\test_discovery.py
  tests\agent_runtime\test_model_runtime.py -q`: exit 2 before test startup
  because the sandbox could not read the existing uv cache.
- The same pre-implementation command with cache access: exit 2 with the two
  expected collection errors: missing `careloop.plugin_runtime` and missing
  `ModelRuntimeFailureCode` export.
- First post-implementation focused command: exit 0; 17 passed in 0.12 seconds,
  with two Pydantic instance-field deprecation warnings in the new test. The
  tests were corrected to inspect the model class without changing behavior.
- Initial focused format/lint/mypy preflight found six unformatted files, five
  Ruff findings, and three mypy errors. Scoped formatting and type-safe callable/
  state imports corrected them; final focused tests then passed 18 cases and
  mypy passed 45 source files.
- Documentation/delivery red command, `uv run --locked pytest
  tests\test_m9_contract_docs.py tests\test_delivery_contract.py -q`: exit 1;
  three failed and three passed because the normative documents and README still
  described M8 only.
- Draft-result consistency red command, `uv run --locked pytest
  tests\agent_runtime\test_model_runtime.py -q`: exit 1; one failed and ten
  passed because inconsistent success evidence was initially accepted. After
  enforcing exact success/failure evidence tuples, the same command exited 0;
  11 passed.
- Intermediate documentation/architecture runs exposed line-wrap-sensitive
  contract assertions: first one failed and 14 passed, then the expanded scope
  had one failed and 73 passed. Whitespace normalization made the assertion
  formatting-independent without weakening its required phrases.
- Final focused command, `uv run --locked pytest tests\plugin_runtime
  tests\agent_runtime tests\test_m9_contract_docs.py
  tests\test_agent_runtime_contract_docs.py tests\test_architecture.py
  tests\test_delivery_contract.py -q`: exit 0; 74 passed in 0.18 seconds.

### Required final verification

- Initial `uv run --locked ruff format --check .`: exit 1; four changed test
  files required mechanical formatting. `uv run --locked ruff format .` exited
  0 and reformatted exactly four files.
- Final `uv run --locked ruff format --check .`: exit 0; 79 files already
  formatted.
- Final `uv run --locked ruff check .`: exit 0; all checks passed.
- Final `uv run --locked mypy src`: exit 0; no issues in 45 source files.
- Final `uv run --locked pytest -q`: exit 0; 221 passed in 0.61 seconds in the
  post-documentation rerun.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases completed and all four existing
  raw/summary artifact paths were regenerated.
- `uv run --locked python tools\generate_milestone2_fixtures.py --check`:
  exit 0; all generator-owned frozen fixtures remain unchanged.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock remains
  synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0;
  regenerated evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks artifacts
  policies`: exit 0; dependency declarations, lock data, frozen inputs,
  generated evidence, and evaluator/safety policies are unchanged.
- `rg` checks for network/provider/process/clock/random imports in the M9 source
  and for a registered `careloop.plugins` entry point in `pyproject.toml` each
  exited 1 with no matches, the expected negative result.
- `git diff --check`: exit 0; only Windows LF-to-CRLF conversion warnings were
  emitted.

### Residual limitations

- An allowlisted Python entry point is trusted enough to execute its manifest
  factory in-process; M9 validates identity and dependency metadata but adds no
  package signature, process sandbox, installer, or supply-chain attestation.
- The runtime verifies only one provider call and draft quarantine. It does not
  yet compose input routing, output guards, bounded rewrite, review, release,
  or append-only session persistence.
- Deterministic synthetic adapters and failure tests do not establish model
  quality, model-output safety, clinical validity, real-world crisis handling,
  or effective human review.
- The owner's pre-existing untracked `.python-version` and Chinese engineering
  guide remain untouched and outside the M9 change set.

## Exact next milestone

Milestone 10 is the planned deterministic synthetic `RunSyntheticTurn`
orchestration plus append-only in-memory event ledger described in `PLAN.md`.
It must preserve draft/reviewer projection isolation and prove input routing,
bounded rewriting, atomic release, and fail-closed failure injection using only
deterministic adapters. It must not add a real plugin/provider, network, Web/API,
database, credential, deployment, real-user workflow, or clinical capability.

## Milestone 10 deterministic synthetic turn orchestration and event ledger

### Implemented change boundary

- Added strict `SyntheticTurnCommand`, `ParticipantTurnView`, and
  `ResearchReviewTurnView` contracts plus exact application status/failure
  enums. The participant projection cannot contain quarantined drafts, gate
  results, internal runtime events, or failure details.
- Added `RunSyntheticTurn` as an explicitly imported, library-only application
  service. The existing `careloop.application` exports and CLI remain limited to
  the original three offline use cases, so removing the M10 module does not
  break evaluate, replay, benchmark, or reporting.
- Added `SyntheticSafetyRuntime.route_input` and refactored the unchanged
  synchronous `handle` method through it. Input detector/router/resource
  routing now has an explicit pre-model API while all existing safety behavior
  and tests remain unchanged.
- Safe input appends `SUBMIT_TURN`, invokes M9 `ProviderNeutralModelRuntime`,
  quarantines and revalidates the draft, then invokes an injected gate. A turn
  is constructed only after `DRAFT_APPROVED` is successfully appended.
- Added `EthicalDraftGate`, which maps the existing deterministic ethical output
  policy to allow, rewrite, or review-hold decisions. It permits at most two
  rewrites and holds the third blocked draft for review.
- Added category-only failure handling for input/router/resource, model, gate,
  and ledger failures. Failures release no ordinary output; a writable ledger
  receives `RUNTIME_FAILURE` from the last persisted state.
- Added exact in-process request idempotency. Commands and cached results are
  deep-revalidated snapshots, so caller mutation cannot change a prior command
  or result. Changed content under the same request ID rejects.
- Added `RuntimeEventLedgerPort` and removable
  `InMemoryRuntimeEventLedger`. It binds immutable session configuration,
  revalidates every event, enforces zero-based contiguous sequence, exact state
  chaining, globally unique event IDs, and returns detached tuple snapshots.
  It exposes no update/delete operation.
- Added no dependency, provider/plugin implementation, entry-point registration,
  network, credential, clock, randomness, database, Web/API/UI, worker,
  deployment, or new CLI command. Existing public domain schemas, policies,
  frozen fixtures, gold, evaluator decisions, benchmark, and generated reports
  remain unchanged.

### Test-first and focused evidence

- Pre-implementation `uv run --locked pytest tests\runtime_storage
  tests\application_runtime tests\test_m10_contract_docs.py -q`: exit 2 with
  the two expected collection errors: missing `careloop.runtime_storage` and
  missing `EthicalDraftGate`/M10 application exports.
- First post-implementation focused command including existing safety runtime
  regressions: exit 0; 37 passed in 0.20 seconds.
- Boundary-hardening red command covering deep idempotency snapshots,
  pre-mutation command validation, strict override state, and detached ledger
  snapshots: exit 1; three failed and one passed for the intended missing
  protections.
- After boundary revalidation and deep snapshot implementation, the same four
  tests exited 0; four passed in 0.14 seconds.
- README/architecture red command: exit 1; one failed and 14 passed because the
  README still reported M9. The architecture boundary tests already passed.
- Initial M10 focused/static preflight found six unformatted files, three Ruff
  findings, and one mypy import error. Mechanical formatting and scoped import/
  line-length corrections resolved them.
- An expanded focused run after the first README update had one failed and 54
  passed because a required phrase crossed a Markdown line boundary. The test
  now normalizes whitespace while preserving every required phrase.
- Final focused command, `uv run --locked pytest tests\runtime_storage
  tests\application_runtime tests\test_m10_contract_docs.py
  tests\safety\test_safety_runtime.py tests\test_architecture.py
  tests\test_delivery_contract.py -q`: exit 0; 56 passed in 0.25 seconds.

### Required final verification

- `uv run --locked ruff format --check .`: exit 0; 85 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 48 source files.
- Final post-documentation `uv run --locked pytest -q`: exit 0; 245 passed in
  0.67 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases completed and all four existing
  raw/summary artifact paths were regenerated.
- `uv run --locked python tools\generate_milestone2_fixtures.py --check`:
  exit 0; all generator-owned frozen fixtures remain unchanged.
- `uv lock --check`: exit 0; 23 packages resolved and the unchanged lock remains
  synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0;
  regenerated evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks artifacts
  policies`: exit 0; dependencies, lock data, frozen inputs, generated evidence,
  and process/safety/evaluation policies are unchanged.
- Negative `rg` checks found no provider/network/database/clock/random imports
  in M10 source and no M10 import or command in CLI/application exports; both
  exited 1 with no matches as expected.
- `git diff --check`: exit 0; only Windows LF-to-CRLF conversion warnings were
  emitted.

### Residual limitations

- The ledger and idempotency cache are process-local demonstrations. They do not
  provide durability, concurrency control, transaction recovery, or
  multi-process/distributed idempotency.
- If ledger writes remain persistently unavailable, even the failure transition
  cannot be recorded. `RuntimeLedgerUnavailable` exposes no participant reply,
  but durable recovery remains outside M10.
- M10 stops at review hold. It does not implement review decisions, session
  close/evaluation/report orchestration, a participant endpoint, or staffed
  human response.
- Exact synthetic routing and output phrases plus deterministic test adapters do
  not establish model quality, real-world output safety, clinical validity,
  crisis detection, treatment effect, or effective review.
- The owner's pre-existing untracked `.python-version` and Chinese engineering
  guide remain untouched and outside the M10 change set.

## M10 closing state (superseded by M11 owner authorization)

At M10 close, no Milestone 11 had been approved. The owner's later instruction
authorized the harness to freeze and implement the smallest next milestone from
the mission and current project state while preserving the existing offline
core, professional/safety boundaries, draft isolation, append-only evidence,
and generated-artifact ownership.

## Milestone 11 deterministic synthetic review resolution

### Frozen and implemented change boundary

- The owner authorized the harness to freeze the smallest next milestone from
  the project mission and completed M10 boundary. M11 resolves only one
  synthetic pre-release review hold and stops before session-close evaluation,
  durable storage, Web/API, real provider/plugin, or real-user work.
- Added strict `SyntheticReviewCommand`, `ParticipantReviewView`, and
  `ResearchReviewResolutionView` models plus exact review status and
  ledger-failure enums. Participant data contains no draft, decision evidence,
  internal event, or failure detail.
- Added library-only `ResolveSyntheticReview`. It binds a detached authoritative
  `ModelDraft` snapshot, requires the complete command draft and final held
  ledger event to match it, and rejects stale, cross-session, terminal,
  different-ID, or same-ID-content-substituted input before mutation.
- Reused the existing four `ReviewDecision` and `REVIEW_*` transitions without
  changing the state machine. Approval releases only byte-identical reviewed
  draft text; replacement releases only an explicit synthetic reviewer turn;
  handoff and rejection close with no output.
- A review event must append before a participant turn is projected. A one-shot
  append failure records category-only `RUNTIME_FAILURE` and releases nothing;
  persistent unavailability raises `ReviewLedgerUnavailable` with no reply.
- Exact process-local `(session_id, request_id)` retries return detached cached
  results and append no second decision; changed reuse rejects.
- Added no dependency, CLI command, state/event/decision value, policy rule,
  provider/plugin, network, credential, database, clock, randomness, Web/API/UI,
  worker, authentication, or deployment behavior. Existing Day 1 schemas,
  policies, frozen fixtures, gold, evaluator decisions, benchmark, and generated
  reports remain unchanged.

### Test-first and focused evidence

- Pre-implementation `uv run --locked pytest
  tests\application_runtime\test_synthetic_review.py
  tests\test_m11_contract_docs.py tests\test_architecture.py
  tests\test_delivery_contract.py -q`: exit 2 with the intended collection
  error `ModuleNotFoundError: No module named
  'careloop.application.synthetic_review'`.
- First post-implementation focused command: exit 1; 29 passed and one delivery
  test failed because README intentionally still said M11 was in progress.
- After authoritative full-draft snapshot binding, the same scope exited 1;
  30 passed and only the same final README completion assertion remained red.
- Expanded M10/M11 application, storage, contract, and architecture regression:
  exit 0; 49 passed in 0.28 seconds.
- Final focused command including delivery contracts: exit 0; 53 passed in
  0.25 seconds.
- Initial `uv run --locked ruff format --check .`: exit 1; four changed Python
  files required mechanical formatting. Initial Ruff check found one import
  ordering issue. `uv run --locked ruff check
  tests\application_runtime\test_synthetic_review.py --fix` and scoped
  `ruff format` corrected only those mechanical findings.
- Initial `uv run --locked mypy src`: exit 0; no issues in 49 source files.

### Required final verification

- `uv run --locked ruff format --check .`: exit 0; 88 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 49 source files.
- `uv run --locked pytest -q`: exit 0; 261 passed in 0.72 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases completed and the existing
  four raw/summary paths were regenerated.
- `uv run --locked python tools\generate_milestone2_fixtures.py --check`:
  exit 0; all generator-owned frozen fixture bytes remain unchanged.
- `uv lock --check`: exit 0; 23 packages resolved and the lock remains
  synchronized.
- `git diff --exit-code -- artifacts/raw artifacts/summary`: exit 0; generated
  evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks artifacts
  policies`: exit 0; dependencies, lock data, frozen inputs, generated evidence,
  and policies are unchanged.
- Post-status `uv run --locked pytest tests\test_m12_contract_docs.py
  tests\test_delivery_contract.py tests\test_architecture.py -q`: exit 0; 19
  passed in 0.08 seconds.
- Negative import/clock/random and CLI/export `rg` checks each exited 1 with no
  matches, as expected. `git diff --check` exited 0 with only Windows
  LF-to-CRLF conversion warnings.
- Post-status documentation check, `uv run --locked pytest
  tests\test_m11_contract_docs.py tests\test_delivery_contract.py
  tests\test_architecture.py -q`: exit 0; 18 passed in 0.07 seconds.

### Residual limitations

- The authoritative held draft, ledger, and idempotency cache are process-local
  demonstrations. There is no durable draft/decision store, transaction,
  concurrency control, distributed idempotency, reviewer identity, queue,
  assignment, staffing, notification, or correction workflow.
- `HANDOFF` is only a closed typed state; it contacts no person or external
  service. Approval or replacement does not establish model-output safety,
  clinical appropriateness, effective human review, or real-world safety.
- Session-close trajectory construction/evaluation/report orchestration remains
  unimplemented and is not implicitly authorized.
- The owner's pre-existing untracked `.python-version` and Chinese engineering
  guide remain untouched and outside the M11 change set.

## M11 closing state (superseded by M12 owner authorization)

At M11 close, no Milestone 12 had been approved. The owner's later instruction
to complete M12 authorized the smallest next runtime milestone: deterministic
synthetic session close, in-memory trajectory assembly/evaluation, and
append-before-report evidence. It did not authorize persistence, Web/API, real
providers/plugins, operational review, deployment, or real-participant work.

## Milestone 12 deterministic synthetic session close and evaluation

### Frozen and implemented change boundary

- Added strict `SyntheticSessionSnapshot`, `SyntheticSessionCloseCommand`,
  `ParticipantSessionCloseView`, and `ResearchSessionCloseView` contracts plus
  exact close status and failure enums. The participant projection contains no
  trajectory, findings, canonical hash, runtime event, failure category, draft,
  hidden reasoning, score, diagnosis, or clinical disposition.
- Added library-only `CloseSyntheticSession`. It binds a deep detached synthetic
  session snapshot, requires exact command session/trajectory identity and
  `RESPONSE_RELEASED`, and validates every user/assistant turn against submit,
  suppressed-override, direct approval, or reviewed-release evidence before
  evaluator execution or ledger mutation.
- The service builds the unchanged domain `Trajectory` and canonical
  `FrozenTrajectoryArtifact` in memory. Added
  `EvaluateTrajectory.evaluate_artifact`, with the existing file-based `run`
  method delegating to the same no-gold evaluation path.
- Evaluation result case ID, canonical hash, and trajectory are revalidated.
  `CLOSE_SESSION` records the evaluated identity and must append before either
  participant or research-review result is returned.
- Evaluation or one-shot close-append failure records category-only
  `RUNTIME_FAILURE`, exposes neither final answer nor raw evaluation, and reaches
  `FAILED_CLOSED`. Persistent ledger failure raises typed local unavailability
  and releases no report.
- Exact process-local `(session_id, request_id)` retries return detached cached
  results and append no second close; changed reuse rejects.
- Added no state/event value, Day 1 public field, policy rule, dependency, CLI
  command, file writer, provider/plugin, network, credential, database, clock,
  randomness, Web/API/UI, worker, authentication, or deployment behavior.
  Existing fixtures, gold, benchmark decisions, and generated evidence remain
  unchanged.

### Test-first and focused evidence

- Baseline `uv run --locked pytest -q`: exit 0; 261 passed in 0.68 seconds.
- Pre-implementation `uv run --locked pytest
  tests\application_runtime\test_synthetic_close.py -q`: exit 1 during
  collection with the intended `ModuleNotFoundError: No module named
  'careloop.application.synthetic_close'`.
- First implementation/evaluation focused command: exit 0; 25 passed in 0.16
  seconds.
- Documentation/architecture red command: exit 1; three intended documentation
  failures and 16 passes because normative files and README still described
  M11. After freezing M12, the same scope exited 0; 19 passed in 0.12 seconds.
- Expanded M10–M12/storage/evaluation/architecture focused command: exit 0; 71
  passed in 0.32 seconds. The strengthened M12 close suite then exited 0; 14
  passed in 0.14 seconds.
- Initial focused preflight: mypy passed 50 source files and 71 tests passed;
  format check reported four changed files and Ruff reported import/line-length
  findings. Scoped Ruff formatting changed exactly those four files.

### Required final verification

- The first restarted `uv run --locked ruff format --check .`: exit 0; 91 files
  already formatted. The following Ruff check exited 1 for one 89-character
  error-message line; it was wrapped without behavior change and the complete
  sequence restarted.
- The next complete sequence passed format, Ruff, and mypy, but `uv run --locked
  pytest -q` exited 1 with two historical M11 documentation failures and 276
  passes. Those tests were updated to preserve the M11 closing fact and M11
  implemented section without requiring the current project to remain frozen at
  M11. Focused M11/M12 documentation regression then exited 0; four passed.
- Final `uv run --locked ruff format --check .`: exit 0; 91 files already
  formatted.
- Final `uv run --locked ruff check .`: exit 0; all checks passed.
- Final `uv run --locked mypy src`: exit 0; no issues in 50 source files.
- Final `uv run --locked pytest -q`: exit 0; 278 passed in 0.71 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases completed and the existing
  four raw/summary paths were regenerated.
- `uv run --locked python tools\generate_milestone2_fixtures.py --check`:
  exit 0 with no output; all generator-owned frozen fixture bytes remain
  unchanged.
- `uv lock --check`: exit 0; 23 packages resolved and the lock remains
  synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0; generated
  evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks artifacts
  policies`: exit 0; dependencies, lock data, frozen inputs, generated evidence,
  and policies are unchanged.

### Residual limitations

- The authoritative transcript snapshot, event ledger, idempotency cache, and
  close reports are process-local demonstrations. There is no durable turn or
  report store, transaction, concurrency control, distributed idempotency,
  correction workflow, post-session queue, or recovery coordinator.
- M12 trusts the application-supplied snapshot as authoritative after strict
  schema and event-identity correlation. The append-only M10/M11 ledger does not
  retain released turn text, so it cannot independently reconstruct transcript
  bytes without the bound snapshot.
- Evaluation uses the existing exact synthetic policy rules. A successful close
  does not establish session quality, model-output safety, clinical
  appropriateness, treatment effectiveness, effective review, or real-world
  safety.
- The owner-directed post-M11 commit added the formerly untracked Python version
  file and Chinese engineering guide; M12 did not modify either file.

## Exact next milestone

No Milestone 13 is approved. Stop after M12. Any later implementation requires a
new versioned milestone that preserves the offline core, synthetic-only data,
draft/projection isolation, append-only evidence, and generated-artifact
ownership.

## Milestone 13 full-stack research contract freeze

### Owner-approved and implemented change boundary

- The owner approved the five-milestone M13–M17 research-only full-stack plan
  after M12. In accordance with the one-milestone rule, this delivery implements
  only M13 governance, contracts, threat analysis, and tests and stops before
  M14 persistence or provider work.
- Updated the engineering contract to adult synthetic role-play, no protected
  health information, non-diagnostic safety-signal routing, bounded repair, and
  a simulated human-review queue that is not clinical or emergency care.
- Froze future `ReleaseDispositionV1` values as `allow`, `hold_for_review`, and
  `system_failure`. This future API vocabulary does not change the implemented
  M8 `SafetyDisposition` or any M8–M12 schema.
- Froze exact `/api/v1` endpoint intent, status-only resumable SSE, atomic gated
  answers, OIDC roles, PostgreSQL authority, Redis non-authority, 30-day default
  synthetic-session retention, and locked safety-plugin behavior.
- Froze provider-neutral future vLLM, Ollama, and DeepSeek adapter boundaries.
  Model tool arguments remain untrusted, server-validated data and grant no
  direct authority.
- Added `evidence/evidence_registry.v1.json` with ten linked governance,
  fidelity, security, and technical sources. Every source remains
  `advisor_review_pending`; none is executable policy or claimed approval.
- Extended the threat model for production demo-identity leakage, OIDC bypass,
  SSE leakage, excessive tool agency, cross-instance event loss, report
  injection, SSRF, secret disclosure, database races, retention, and resource
  exhaustion.
- Added no source implementation, dependency, lock entry, provider, plugin,
  endpoint, database, worker, Web UI, container, cloud resource, CLI command,
  real-person data, or clinical behavior. Frozen fixtures, policies, gold,
  benchmark decisions, and generated evidence remain unchanged.

### Test-first evidence

- Initial sandboxed `uv run --locked pytest tests\test_m13_contract_docs.py
  tests\test_delivery_contract.py -q`: exit 2 before test startup because the
  restricted process could not read the existing user-level uv cache.
- The same pre-documentation command with approved cache access: exit 1; five
  intended failures and three passes. Missing evidence included M13 normative
  text, `/api/v1` paths, full-stack threats, the evidence registry, and the M13
  README status.
- First post-documentation focused compatibility run: exit 1; seven passes and
  three failures. The remaining failures were exact wording and the historical
  M12 status assertion, not implementation behavior.
- Final `uv run --locked pytest tests\test_m13_contract_docs.py
  tests\test_delivery_contract.py tests\test_m12_contract_docs.py -q`: exit 0;
  10 passed in 0.04 seconds.
- Initial `uv run --locked ruff format --check .`: exit 1; one edited delivery
  test required mechanical formatting.
- Initial `uv run --locked ruff check .`: exit 1; one new test import block
  required mechanical ordering.
- Initial `uv run --locked mypy src`: exit 0; no issues in 50 source files.
- Scoped Ruff fix/format corrected only the two M13 test files.

### Required final verification

- `uv run --locked ruff format --check .`: exit 0; 92 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 50 source files.
- Final post-status `uv run --locked pytest -q`: exit 0; 282 passed in 0.83
  seconds.
- The first sandboxed `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 2 before project startup because the
  restricted process could not read the user-level uv cache.
- The same benchmark command with approved cache access: exit 0; 16 cases and
  the existing four raw/summary paths were written.
- The first sandboxed `uv run --locked python
  tools\generate_milestone2_fixtures.py --check`: exit 2 for the same uv-cache
  restriction. The approved rerun exited 0 with no output; all frozen generated
  fixture bytes match.
- `uv lock --check`: exit 0; 23 packages resolved and the lock is synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0; regenerated
  evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock benchmarks policies src`:
  exit 0; dependencies, lock data, source implementation, frozen inputs, and
  policies are unchanged.
- `git diff --check`: exit 0; only Windows LF-to-CRLF conversion warnings were
  emitted.

### Residual limitations

- M13 is a decision-complete contract, not an operational full-stack product.
  FastAPI, durable storage, provider adapters, authentication, Web UI, Docker,
  GCP, and simulated reviewer operation remain unimplemented.
- Evidence-registry entries have not been approved by a clinical, ethics, or
  security advisor. They cannot be treated as a clinical protocol or proof of
  compliance.
- Existing exact synthetic policies and deterministic tests do not establish
  model-output safety, clinical validity, treatment effectiveness, crisis
  detection, effective oversight, or real-world performance.

## Exact next milestone

Milestone 14 only: durable PostgreSQL/Redis runtime adapters, provider-neutral
vLLM/Ollama/DeepSeek gateways, and immutable plugin profiles. Do not start M15
supervised orchestration, M16 Web/API, or M17 cloud delivery until their prior
milestone passes its complete recorded gate.

## Milestone 14 durable runtime, model gateway, and plugin profiles

### Implemented change boundary

- Added SQLAlchemy 2 metadata and `PostgresRuntimeStore` behind the existing
  synchronous `RuntimeEventLedgerPort`. Session config is immutable; append
  locks and revalidates state/sequence, inserts event plus outbox, and advances
  the projection in one transaction.
- Added immutable distributed idempotency records and immutable strict
  `PluginProfileV1` persistence. Profiles require enabled/locked provider,
  input-safety, output-guard, and resource-catalog entries.
- Added Alembic revision `20260902_0001` for PostgreSQL JSONB session, event,
  outbox, idempotency, and plugin-profile tables. The repository contains no
  database credential.
- Added Redis transactional-outbox publishing. Redis failure leaves committed
  work pending; a new publisher can retry. Delivery is at least once and event
  identity remains authoritative in SQL.
- Added an ARQ-compatible worker function and `WorkerSettings` with deployment
  resources injected rather than read by the core.
- Added DeepSeek and vLLM OpenAI-compatible adapters and one native Ollama
  adapter. All explicitly disable streaming, validate one complete response,
  return only a quarantined draft, and perform no fallback or tool execution.
- Added SQLAlchemy, Alembic, psycopg, redis-py, ARQ, and HTTPX as explicit
  locked outer-adapter dependencies. No provider SDK or Web framework was
  introduced.
- Existing public Day 1/M8–M13 schemas, state/events, policies, fixtures, gold,
  evaluator decisions, CLI commands, benchmark, and generated evidence remain
  unchanged.

### Test-first and implementation evidence

- Pre-implementation `uv run --locked pytest tests\durable_runtime
  tests\test_m14_contract_docs.py -q`: exit 2 with four intended collection
  errors for the missing `careloop.durable_runtime` package and SQLAlchemy.
- `uv lock --python 3.12`: exit 0; dependency graph expanded from 23 to 42
  locked packages. `uv sync --locked`: exit 0; 20 packages installed.
- First post-implementation durable-runtime focused suite: exit 0; 15 passed in
  1.60 seconds.
- Initial M14 preflight truthfully recorded six unformatted files, one Ruff
  line-length error, and 12 mypy errors in HTTP/Redis typing. Scoped formatting
  and explicit protocol/cast fixes corrected them without weakening behavior.
- Extended persistence/migration/recovery/architecture suite: first exit 1 with
  30 passes and one architecture failure because the test incorrectly treated
  M14's legal HTTPX outer dependency as a forbidden core dependency. The test
  was narrowed to the actual no-reverse-import invariant.
- Pre-documentation `uv run --locked pytest tests\test_m14_contract_docs.py -q`:
  exit 1; two intended failures because M14 normative text and delivery status
  were absent.
- Final focused M14/compatibility/architecture command: exit 0; 42 passed in
  1.10 seconds.

### Required final verification

- `uv run --locked alembic upgrade head --sql`: exit 0; PostgreSQL transactional
  offline SQL contains JSONB, compound event identity, outbox, idempotency,
  plugin profiles, index, version insert, and commit.
- `uv run --locked ruff format --check .`: exit 0; 107 files already formatted.
- `uv run --locked ruff check .`: exit 0; all checks passed.
- `uv run --locked mypy src`: exit 0; no issues in 57 source files.
- Final `uv run --locked pytest -q`: exit 0; 303 passed in 1.65 seconds.
- `uv run --locked careloop benchmark --manifest
  benchmarks\manifest.v1.json`: exit 0; 16 cases and the existing four
  raw/summary paths were written.
- `uv run --locked python tools\generate_milestone2_fixtures.py --check`: exit
  0 with no output; all generator-owned fixture bytes match.
- `uv lock --check`: exit 0; 42 packages resolved and synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0; generated
  evidence remains byte-identical.
- `git diff --exit-code -- benchmarks policies`: exit 0; frozen benchmark and
  executable policy inputs are unchanged.

### Environment-limited integration and residual risks

- Docker daemon is unavailable, and neither PostgreSQL nor Redis executable or
  service is installed. A live PostgreSQL/Redis integration suite could not be
  run. SQLite exercises repository behavior only; PostgreSQL DDL and Alembic
  offline SQL are verified separately and are not represented as a live pass.
- TLS, credential rotation, connection-pool sizing, database backup/restore,
  multi-instance load, Redis reconnect, and an actual ARQ worker process remain
  deployment validation for M16/M17.
- Provider adapters were verified with deterministic HTTP test clients and were
  not sent credentials or network requests to DeepSeek, vLLM, or Ollama.
- M14 storage and provider controls do not establish provider quality, model
  output safety, effective supervision, clinical validity, treatment effect,
  crisis detection, or real-world performance.

## Exact next milestone

Milestone 15 only: compose durable input-first routing, quarantined output
gates, bounded repair, and the simulated reviewer queue. Do not begin M16 Web,
OIDC, Docker Compose, participant API, or M17 cloud delivery until M15 passes.

## Milestone 15 supervised safety orchestration and review queue

### Frozen and implemented change boundary

- Added removable `careloop.supervision` contracts and composition. Existing
  input-first routing, complete draft quarantine, deterministic output gating,
  and the maximum of two repairs remain owned by M10/M8 behavior; M15 queues
  only the final held draft after those controls succeed.
- Added strict `ReviewQueueItemV1` pending/claimed/resolved lifecycle with exact
  session/request/draft/evidence identity, timezone-aware explicit enqueue and
  research-target times, `synthetic-reviewer:` identities, and monotonically
  increasing optimistic revisions.
- Added PostgreSQL `review_queue` metadata and Alembic revision
  `20260902_0002`. Claim races reject. `append_review_resolution` commits the
  existing typed M11 review event, outbox row, session projection, and resolved
  queue revision in one transaction before a participant projection exists.
- Approval retains the exact held draft; replacement remains explicit reviewer
  text; handoff/reject release no ordinary response. No M8–M14 state/event or
  public schema value changed.
- Added explicit-time `ReviewQueueAuditV1` raw counts and stable before/after
  research-target IDs. It contains no score, percentage, severity, clinical
  metric, or wall-clock input.
- Added `benchmarks/supervision/m15.supervision.v1.json`: eight fixed adult
  synthetic English/Chinese cases covering allow, input override, successful
  repair, and exhausted repair hold. Each case drives the real M15 composition
  in tests; it remains separate from evaluator gold and P1–P8 benchmark inputs.
- Added no dependency, CLI command, FastAPI/Next.js/OIDC/UI/SSE surface, Docker
  service, worker operation, credential, real reviewer, real-person data,
  clinical behavior, evaluator rule, policy edit, or generated result edit.

### Test-first and focused evidence

- Baseline `uv run --locked pytest -q`: exit 0; 303 passed in 1.81 seconds.
- Pre-implementation `uv run --locked pytest tests\supervision -q`: the first
  sandboxed run exited 2 before startup because the restricted process could
  not access the existing user-level uv cache. The approved rerun exited 2 with
  three intended collection errors for missing `careloop.supervision`.
- First queue/orchestration implementation focused run: exit 0; 5 passed in
  0.55 seconds.
- Pre-atomic-resolution `uv run --locked pytest
  tests\supervision\test_supervised_review.py -q`: exit 2 with the intended
  missing `QueuedSyntheticReviewCommand` import.
- First complete supervision run: exit 1 with six passes; the one failure was a
  test attempting schema-invalid claimed revision zero. The corrected legal
  stale revision case then produced 7 passes in 0.62 seconds.
- Pre-documentation M15 contract/architecture/migration command: exit 1; 16
  passed and two intended M15 normative-document failures remained. After the
  contract freeze, the expanded focused command exited 0; 25 passed in 1.30
  seconds.
- Initial preflight recorded 12 unformatted files and 16 Ruff findings limited
  to import order, line width, unused imports, and the Python 3.12 `UTC` alias;
  mypy already passed 62 source files. Scoped Ruff fixes changed only M15 files.
- Fixed bilingual corpus focused execution: exit 0; nine tests passed, including
  all eight manifest cases through input routing, draft/gate behavior, release
  isolation, and optional durable enqueue.

### Required final verification

- `uv run ruff format --check .`: exit 0; 118 files already formatted.
- `uv run ruff check .`: exit 0; all checks passed.
- `uv run mypy src`: exit 0; no issues in 62 source files.
- The first complete `uv run pytest -q` after implementation exited 1 with 311
  passes and two historical README assertions still freezing current status at
  M14. They were updated to retain M14 implementation facts while requiring the
  current M15/M16 status. The focused delivery regression then exited 0; eight
  passed.
- Final `uv run pytest -q`: exit 0; 321 passed in 2.07 seconds.
- `uv run alembic upgrade head --sql`: exit 0; PostgreSQL offline SQL includes
  the M14 schema plus M15 `review_queue`, JSONB payload, timezone-aware columns,
  unique identities, foreign key, revision, target index, and transaction.
- `uv run careloop benchmark --manifest benchmarks\manifest.v1.json`: exit 0;
  16 cases completed and the existing four raw/summary paths were regenerated.
- `uv run python tools\generate_milestone2_fixtures.py --check`: exit 0 with no
  output; generator-owned P1–P8 fixture bytes match.
- `uv lock --check`: exit 0; 42 packages resolved and synchronized.
- `git diff --exit-code -- artifacts\raw artifacts\summary`: exit 0; generated
  evidence is byte-identical.
- `git diff --exit-code -- pyproject.toml uv.lock policies
  benchmarks\manifest.v1.json benchmarks\trajectories benchmarks\gold
  benchmarks\failure_fixtures`: exit 0; dependencies, lock data, executable
  policies, and existing benchmark inputs are unchanged.
- `git diff --check`: exit 0 with only Windows LF-to-CRLF conversion warnings.

### Environment-limited integration and residual risks

- No live PostgreSQL or Redis service is installed in this environment. SQLite
  covers deterministic repository behavior and PostgreSQL offline SQL covers
  dialect DDL; neither is represented as a live concurrency, crash-recovery, or
  multi-instance pass.
- Queue enqueue follows the already committed fail-closed held event. A process
  crash between those writes releases no ordinary response but can leave a
  durable held session without its queue row; reconciliation/recovery ownership
  remains M16 operational work.
- There is no queue poller, actual ARQ process, authentication, assignment,
  staffing, notification, retry/dead-letter workflow, or reviewer correction
  workflow. The explicit target is descriptive research evidence, not a staffed
  SLA.
- A simulated approval or replacement does not establish model-output safety,
  effective human review, clinical appropriateness, treatment effectiveness,
  crisis detection, or real-world safety.

## Exact next milestone

Milestone 16 only: implement the frozen research-only FastAPI/Next.js/OIDC,
status-only SSE, report, and Docker Compose surface. Do not start M17 cloud
delivery until M16 passes its complete recorded gate.
