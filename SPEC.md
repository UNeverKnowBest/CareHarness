# CareLoop Harness Specification

Contract status: Day 1 public contract frozen
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

The owner froze one opaque token format for every initial version.
Version-specific compatibility beyond exact `v1` matching is outside Day 1.

## Public schema contract

All field names below use `snake_case`. JSON strings are UTF-8. Public models
reject unknown fields and unknown version values. The concrete implementation
must not add public fields that are not FROZEN here or separately approved.

### Common validation

#### FROZEN

- Every public Pydantic model uses `extra="forbid"`; extension fields are not
  preserved on Day 1.
- Identifier, reference, source, semantic label, jurisdiction, contact, and URL
  strings must not be empty or contain only whitespace.
- Tuple order is part of the wire contract and is preserved during round-trip.
- No public or internal model may add a risk score/level, probability,
  diagnosis, or clinical disposition field.

### `Turn`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `turn_id` | `str` | yes | non-empty identifier |
| `sequence` | `int` | yes | greater than or equal to zero |
| `role` | `str` enum | yes | exact value `user` or `assistant` |
| `text` | `str` | yes | synthetic turn content |

No system, tool, clinician, or other role value is accepted on Day 1.

### `ProcessMarker`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `marker_id` | `str` | yes | non-empty identifier |
| `turn_id` | `str` | yes | resolves within the owning trajectory |
| `marker_type` | `str` | yes | non-empty observable marker label |
| `value` | `str` | yes | non-empty observable marker value |
| `source_ids` | `tuple[str, ...]` | yes | non-empty source identifiers |
| `process_policy_version` | `str` | yes | exact supported value `v1` |

The schema records marker evidence only. It does not define a CBT/MI rule or
infer a mental state.

### `SafetyEvent`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `event_id` | `str` | yes | non-empty identifier |
| `triggering_turn_ids` | `tuple[str, ...]` | yes | non-empty references resolving within the owning trajectory |
| `action` | `SafetyAction` | yes | system action only |
| `requires_override` | `bool` | yes | whether normal flow must be suppressed |
| `normal_flow_suppressed` | `bool` | yes | must be true when `requires_override` is true |
| `source_ids` | `tuple[str, ...]` | yes | non-empty source identifiers |
| `resource_ids` | `tuple[str, ...]` | yes | may be empty; no resource is guessed |
| `crisis_policy_version` | `str` | yes | exact supported value `v1` |

This model records a typed system event. It is not a risk classification,
detector result, diagnosis, or clinical disposition.

### `Finding`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `finding_id` | `str` | yes | non-empty identifier |
| `rule_id` | `str` | yes | non-empty policy rule identifier |
| `outcome` | `str` enum | yes | exact value `present`, `absent`, or `uncertain` |
| `turn_ids` | `tuple[str, ...]` | yes | non-empty references resolving within the evaluated trajectory |
| `source_ids` | `tuple[str, ...]` | yes | non-empty source identifiers |
| `evaluator_version` | `str` | yes | exact supported value `v1` |

`Finding` is an evaluator output and is not embedded in an input trajectory. It
contains no severity copied from policy data and no free-form diagnostic field.

### `CrisisResource`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `resource_id` | `str` | yes | non-empty identifier |
| `name` | `str` | yes | non-empty display name |
| `jurisdiction` | `str` | yes | non-empty explicit jurisdiction |
| `contact` | `str` | yes | non-empty contact representation |
| `source_url` | `str` | yes | non-empty source link |
| `is_allowlisted` | `bool` | yes | must be true for a valid resource entry |
| `verified_on` | `date` | yes | explicit verification date |
| `expires_on` | `date` | yes | not earlier than `verified_on` |
| `resource_registry_version` | `str` | yes | exact supported value `v1` |

The schema stores a resource registry entry but performs no selection. Future
selection must match jurisdiction and validate dates against an explicit
manifest `as_of`; missing jurisdiction never guesses a resource.

### `Trajectory`

#### FROZEN

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `trajectory_schema_version` | `str` | yes | exact supported value `v1` |
| `trajectory_id` | `str` | yes | non-empty identifier |
| `turns` | `tuple[Turn, ...]` | yes | non-empty, ordered trajectory |
| `process_markers` | `tuple[ProcessMarker, ...]` | yes | embedded evidence; may be empty |
| `safety_events` | `tuple[SafetyEvent, ...]` | yes | embedded events; may be empty |

`Trajectory` owns aggregate validation for unique turn IDs, strictly increasing
turn sequences, and embedded marker/event turn references. It also exposes a
domain-level validation operation for a standalone `Finding`; that operation
must verify every `Finding.turn_ids` reference without embedding findings in the
trajectory wire representation.

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

### Aggregate nesting decision

#### FROZEN

- `ProcessMarker` and `SafetyEvent` are embedded in `Trajectory`.
- `Finding` remains a standalone evaluator output and is validated against a
  trajectory at the aggregate boundary.
- `EvaluationManifest`, `BenchmarkManifest`, `CrisisResource`, and
  `FinalAnswerView` remain standalone public models.
- Day 1 introduces no artifact envelope beyond these frozen models.

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
