# CareLoop Harness Architecture

Contract status: temporary Day 1 architecture contract

## Status vocabulary and authority

The `FROZEN`, `ASSUMPTION`, and `TBD` labels have the meanings defined in
`SPEC.md`. `AGENTS.md` remains the highest-level engineering boundary. The
original source specification is unavailable; this document therefore records
only architecture stated by the approved engineering guide and preflight.

## System split

### FROZEN — synthetic runtime demonstration

```text
SyntheticScenario
  -> input safety router
     -> override: typed crisis action -> versioned trajectory
     -> continue: scripted adapter -> output policy -> versioned trajectory
```

This path exists only to demonstrate that synthetic safety routing precedes
normal response generation, override suppresses the normal flow, and output
policy executes before output becomes visible. Safety subsystem failure fails
closed and requires human review.

### FROZEN — offline evaluation core

```text
FrozenTrajectory
  -> schema/reference/version validation
  -> FinalAnswerView -> FinalAnswerEvaluator
  -> complete ordered trajectory -> TrajectoryEvaluator
  -> raw actual result
  -> load gold after evaluation
  -> comparison record -> raw artifact -> derived report
```

The offline path is the core product. It accepts frozen trajectories directly
and does not depend on the runtime path to generate them. Replay and benchmark
must remain operational if adapters and UI are removed.

### FROZEN — separation rules

- Runtime and offline evaluation share versioned domain contracts, not control
  flow.
- `FinalAnswerEvaluator` receives only `FinalAnswerView`.
- `TrajectoryEvaluator` receives the complete ordered trajectory and never gold.
- Benchmark loads gold only after obtaining actual evaluator output.
- Replay never calls an agent, model, network, or wall clock.
- Reports and summaries derive from raw artifacts and contain no evaluator logic.

Runtime, evaluation, replay, benchmark, and reporting behavior are outside Day 1
implementation even though their boundaries are frozen here.

## Module dependency direction

### FROZEN

```text
CLI / optional read-only audit UI
                 |
                 v
          application services
            |             |
            v             v
 domain <- process     evaluation
    ^         |          |  |
    |         +----------+  |
    +------ safety <--------+

infrastructure/adapters implement ports selected by application;
core modules never depend on infrastructure/adapters.
```

Normative dependency rules:

```text
domain        -> standard library + Pydantic only
process       -> domain
safety        -> domain
evaluation    -> domain + public process/safety interfaces
application   -> core modules + declared ports
infrastructure/adapters -> core port/domain interfaces
CLI/UI        -> application only
```

The diagram shows allowed knowledge, not a requirement that Day 1 create every
package.

### FROZEN — forbidden imports and rule placement

- Domain, process, safety, and evaluation do not import CLI, UI, Streamlit,
  provider SDKs, network clients, tests, gold labels, or benchmark loaders.
- Evaluators do not import gold or benchmark labels.
- UI does not call detectors or duplicate policy/evaluator rules.
- Report code does not implement evaluator decisions.
- Safety routing does not require a model response before it runs.
- Scenario text crosses parsing/validation boundaries only as untrusted data.

## Application use cases

### FROZEN — future public application boundary

Only three application use cases are planned:

1. `EvaluateTrajectory`: validate one frozen trajectory, construct a
   `FinalAnswerView`, run final-only and trajectory-aware evaluation, and return a
   raw result without loading gold.
2. `ReplayArtifact`: reconstruct and verify a frozen artifact deterministically,
   with zero adapter/model/network/wall-clock calls.
3. `RunBenchmark`: evaluate cases in manifest order, load gold only after actual
   results exist, write raw JSONL, and invoke pure report derivation.

Report generation is an internal pure derivation step of `RunBenchmark`, not a
fourth business use case. None of these use cases is implemented on Day 1.

## Day 1 package boundary

### FROZEN

Day 1 may create only the minimal package/configuration needed for:

- `src/careloop/domain/` versioned models and validation errors;
- package version exposure;
- a CLI entry point limited to help/version;
- domain-focused tests and architecture tests needed to protect dependency
  direction.

It must not create placeholder evaluator, safety detector, benchmark, replay,
adapter, reporter, UI, or infrastructure implementations.

### ASSUMPTION

Domain validation that needs the owning trajectory (for finding/event turn
references) is invoked at the trajectory aggregate boundary rather than by a
model performing file I/O. This follows the requirement that core models remain
deterministic and infrastructure-free.

The internal Day 1 file split defaults to small domain-focused modules under
`src/careloop/domain/`. It is not part of the public API and may be chosen during
implementation without changing the dependency direction in this document.

### TBD — blocks relevant Day 1 implementation

- Whether `ProcessMarker`, `SafetyEvent`, and `Finding` are embedded in
  `Trajectory` or belong to a versioned artifact envelope. This changes the
  public schema and requires owner confirmation.
- Whether schema models reject all unknown JSON fields or preserve extension
  fields. This changes compatibility semantics and requires owner confirmation.

## Persistence and external systems

### FROZEN

- Frozen JSON files are the intended boundary; no database is introduced.
- No network, model API, microservice, message queue, Docker/Kubernetes, or cloud
  deployment is part of the architecture.
- CLI is the primary interaction boundary. Any later UI is optional, read-only,
  and removable.
