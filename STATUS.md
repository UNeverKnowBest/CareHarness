# CareLoop Harness Status

Current phase: Contract Bootstrap  
Next milestone: Day 1 — repository scaffold and versioned domain schema  
Implementation status: BLOCKED pending public wire-schema decisions

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

## Assumptions

- A uniform opaque `v1` token is used for all initial version selectors.
- Aggregate-level validation will check cross-object turn references without file
  I/O in domain models.
- Canonical JSON uses UTF-8, sorted keys, and stable compact separators, but hash
  and replay work remain outside Day 1.
- The benchmark target remains 8 matched pairs/16 trajectories plus four failure
  fixtures; this does not authorize creating fixtures on Day 1.

## Known blockers and TBDs

### TBD — owner confirmation required before Day 1 implementation

- Exact fields and allowed role values for `Turn`.
- Exact top-level fields and nesting for `Trajectory`.
- Exact public wire fields for `ProcessMarker`, `SafetyEvent`, `Finding`, and
  `CrisisResource`.
- Whether markers, events, and findings are embedded in a trajectory or stored in
  a separate artifact envelope.
- Whether public Pydantic models reject unknown JSON fields or preserve extension
  fields.

### TBD — required later, not a Day 1 blocker

- Exact benchmark case IDs, gold-label schema, rule IDs, and pair definitions.
- Canonical date/non-ASCII/newline serialization and hash algorithm before replay
  fixtures are frozen.

## Day 1 acceptance criteria

### FROZEN

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

## Next exact action

Owner reviews and resolves the Day 1-blocking schema and compatibility TBDs. Do
not create `pyproject.toml`, `src/`, or `tests/` until those decisions are
recorded in `SPEC.md` and `ARCHITECTURE.md`.
