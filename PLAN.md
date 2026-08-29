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
