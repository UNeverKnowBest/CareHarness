# CareLoop Harness Status

Current phase: Day 1 complete
Next milestone: not defined in the current approved plan
Implementation status: COMPLETE for D1.0 through D1.5

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
