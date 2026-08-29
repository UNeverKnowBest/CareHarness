# CareLoop Harness Specification

Contract status: temporary Day 1 contract bootstrap  
Authority: `AGENTS.md`, `CareLoop_Codex_工程化实施指南_ZH.md`, and the approved
implementation preflight defaults  
Original source specification: unavailable in this worktree

## Status vocabulary

- **FROZEN**: approved for Day 1 and must not change without an explicit schema,
  safety, benchmark, or architecture decision.
- **ASSUMPTION**: conservative interpretation used to make the temporary contract
  coherent; it is not evidence of an implemented capability.
- **TBD**: intentionally undecided because the available guide does not define it.
  A TBD that affects a public model blocks implementation of that model.

## Product boundary

### FROZEN

- CareLoop Harness is an offline-first, deterministic evaluation harness for
  synthetic support-agent trajectories.
- It is non-clinical and is not therapy, diagnosis, suicide-risk assessment,
  crisis care, a medical device, or evidence of real-world safety.
- Findings describe observable artifact behavior, not inferred mental states.
- CBT is limited to a generic collaborative CBT-informed session shell.
- MI processes may move backward and forward; Planning is optional. Refusal,
  support-only endings, and no-plan endings are valid.
- No public or internal schema may contain `risk_score`, `risk_level`, suicide
  probability, `diagnosis`, or `clinical_disposition`.
- The system must not implement clinical screening instruments, a complete safety
  plan, medication advice, automatic third-party contact, or a real-world crisis
  detector.
- Scenario text is untrusted synthetic data and is never executed as instructions.

## Day 1 scope

### FROZEN

Day 1 is limited to a Python 3.12 `uv` src-layout package, versioned domain
schemas, schema/reference validation, domain round-trip tests, and a CLI that
exposes only help and version. Day 1 does not implement evaluators, process
rules, safety detection/routing, resources, replay, benchmark execution, report
generation, a model adapter, or UI.

The planned domain model names are:

- `Turn`
- `Trajectory`
- `ProcessMarker`
- `SafetyEvent`
- `Finding`
- `EvaluationManifest`
- `BenchmarkManifest`
- `CrisisResource`
- `FinalAnswerView`
- `SafetyAction`

## Version contract

### FROZEN

The temporary Day 1 version token is the exact string `v1`. Unknown schema or
policy versions fail visibly; they are never silently accepted, coerced, or
downgraded.

The following public version fields are required where shown:

| Contract | Field | Day 1 value |
|---|---|---|
| trajectory schema | `trajectory_schema_version` | `v1` |
| process policy | `process_policy_version` | `v1` |
| ethical policy | `ethical_policy_version` | `v1` |
| crisis policy | `crisis_policy_version` | `v1` |
| resource registry | `resource_registry_version` | `v1` |
| evaluator | `evaluator_version` | `v1` |
| benchmark | `benchmark_version` | `v1` |

### ASSUMPTION

Using one opaque token format for every initial version is the smallest
interpretation consistent with the guide's `*.v1.json` naming. Version-specific
compatibility beyond exact `v1` matching is outside Day 1.

## Public schema contract

All field names below use `snake_case`. JSON strings are UTF-8. Public models
reject unknown version values. The concrete implementation must not add public
fields that are not FROZEN here or separately approved.

### `SafetyAction`

#### FROZEN

This enum describes system actions, never clinical risk levels. Its exact values
are:

```text
continue_support
pause_and_clarify_now
connect_human_help_now
seek_emergency_help_now
```

No implicit fallback or additional enum value is permitted in Day 1.

### `FinalAnswerView`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `text` | `str` | yes | final assistant text only |
| `turn_id` | `str` | yes | non-empty reference to that assistant turn |

It contains no history, marker, safety event, gold label, or trajectory object.

### `BenchmarkManifest`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `benchmark_version` | `str` | yes | exact supported value `v1` |
| `as_of` | `date` | yes | explicit evaluation date; never wall clock |
| `case_ids` | `tuple[str, ...]` | yes | non-empty IDs; order is significant and stable |
| `resource_registry_version` | `str` | yes | exact supported value `v1` |

Duplicate `case_ids` are invalid. Gold labels are not part of this model.

### `EvaluationManifest`

#### FROZEN

The model carries exactly these required version selectors:

| Field | Type | Day 1 value |
|---|---|---|
| `trajectory_schema_version` | `str` | `v1` |
| `process_policy_version` | `str` | `v1` |
| `ethical_policy_version` | `str` | `v1` |
| `crisis_policy_version` | `str` | `v1` |
| `resource_registry_version` | `str` | `v1` |
| `evaluator_version` | `str` | `v1` |

### Cross-model invariants

#### FROZEN

- `Turn.turn_id` is non-empty and unique within a trajectory.
- `Turn.sequence` is strictly increasing in trajectory order.
- A trajectory contains at least one turn.
- `Finding.turn_ids` is non-empty and every value resolves to a turn in the
  evaluated trajectory.
- `SafetyEvent.triggering_turn_ids` is non-empty and every value resolves to a
  turn in the owning trajectory.
- A safety event that requires override must have
  `normal_flow_suppressed=true`.
- `CrisisResource` has explicit verified and expiry dates; expiry cannot precede
  verification.
- A resource is allowlisted, jurisdiction-matched, source-linked, versioned, and
  checked against an explicit manifest `as_of` date.
- Missing jurisdiction never selects or guesses a hotline/resource.
- Every `Finding` identifies a rule, source, turn evidence, and evaluator
  version.
- `present`, `absent`, and `uncertain` remain distinct finding outcomes when
  process evaluation is introduced after Day 1.

### Wire fields not defined by the available guide

#### TBD — blocks Day 1 domain implementation

The original guide names the models and invariants but does not define the exact
wire fields for:

- `Turn`: exact `role` representation and allowed role values.
- `Trajectory`: exact top-level identity field and whether markers/events are
  embedded or stored beside the trajectory.
- `ProcessMarker`: identifier, marker kind/value, source, and version field names.
- `SafetyEvent`: event identifier, `requires_override` representation, policy and
  source field names, and resource references.
- `Finding`: finding identifier, exact rule/source field names, outcome field,
  message field, and whether severity is copied from policy data.
- `CrisisResource`: exact jurisdiction, contact, source, allowlist, verified, and
  expiry field names.

These fields must be confirmed before tests or implementation freeze a JSON
shape. They must not be invented during Day 1 coding.

## Canonical JSON boundary

### FROZEN

- Canonical content is UTF-8 JSON with sorted object keys and stable compact
  separators.
- Any stored hash field is excluded when its own canonical hash is calculated.
- Runtime/report timestamps do not participate in canonical hashes or gold
  decisions.
- Day 1 implements only validated model round-trip. Canonical hashing and replay
  remain outside Day 1.

### TBD

- Non-ASCII escaping policy, newline convention, date serialization details, and
  the future hash algorithm are not defined by the available guide. They do not
  block Day 1 round-trip but must be frozen before replay fixtures are created.

## Benchmark boundary

### FROZEN

- Initial benchmark and evaluator versions are `v1`.
- The target corpus is eight matched pairs (16 trajectories) plus four artifact
  failure fixtures.
- If the seven-day cut line is required, the minimum is six pairs (12
  trajectories), retaining P2, P3, P5, P6, P7, and P8.
- Gold labels describe only frozen observable behavior and system actions; they
  never encode clinical risk categories or probabilities.
- Evaluators run before gold labels are loaded for comparison.

### TBD — does not affect Contract Bootstrap; blocks fixture creation

- Exact case IDs, pair definitions, gold label wire schema, and policy rule IDs.

## Dependency contract

### FROZEN

- Python 3.12 and `uv`.
- Runtime dependencies: Pydantic v2 and Typer only.
- Development dependencies: pytest, Ruff, and mypy only.
- No Streamlit or property-testing framework is added by default.
- No model/provider SDK, network client, database, service framework, container,
  message queue, or cloud dependency is allowed.

