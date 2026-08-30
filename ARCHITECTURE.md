# CareLoop Harness Architecture

Contract status: Day 1 architecture contract frozen

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

### FROZEN — aggregate validation placement

Domain validation that needs the owning trajectory is invoked at the trajectory
aggregate boundary rather than by a model performing file I/O. `Trajectory`
validates its embedded process-marker and safety-event references and validates
standalone findings through a domain-level operation. This keeps the core
deterministic and infrastructure-free.

`ProcessMarker` and `SafetyEvent` are embedded in `Trajectory`. `Finding` is not
embedded because it is evaluator output rather than input trajectory evidence.
No additional artifact-envelope model is introduced on Day 1.

Every public Pydantic model rejects unknown fields. Unknown schema and policy
versions also fail validation rather than being preserved, coerced, or
downgraded.

### ASSUMPTION — internal file organization

The internal Day 1 file split defaults to small domain-focused modules under
`src/careloop/domain/`. It is not part of the public API and may be chosen during
implementation without changing the dependency direction in this document.

## Persistence and external systems

### FROZEN

- Frozen JSON files are the intended boundary; no database is introduced.
- No network, model API, microservice, message queue, Docker/Kubernetes, or cloud
  deployment is part of the architecture.
- CLI is the primary interaction boundary. Any later UI is optional, read-only,
  and removable.

## Milestone 2 artifact and replay boundary

### FROZEN

Milestone 2 adds only this implemented offline path:

```text
canonical frozen trajectory file
  -> artifact schema + canonical-byte validation
  -> unchanged Trajectory aggregate validation
  -> SHA-256 reconstruction and comparison
  -> ReplayResult(canonical bytes, hash, domain object)
```

`careloop.artifacts` depends on the standard library, Pydantic, and `domain`.
`careloop.application.replay` depends on `artifacts` and `domain`. Neither module
has an adapter, model, network, CLI, evaluator, reporter, wall-clock, or gold
dependency. The replay function accepts only a local artifact path, making an
adapter call impossible at the API boundary.

Trajectory and gold persistence are intentionally asymmetric:

```text
benchmarks/trajectories/*.json -> production artifact loader may read
benchmarks/gold/*.json         -> test/benchmark data only; production cannot import
```

Milestone 2 does not implement the future `EvaluateTrajectory` or `RunBenchmark`
use cases. It implements only `ReplayArtifact`; the existing CLI remains limited
to help and version. The internal artifact envelope is not nested into or added
to any Day 1 public domain model.

## Milestone 3 process evaluation boundary

### FROZEN

Milestone 3 adds a process-only deterministic path:

```text
validated process.v1 registry + complete ordered Trajectory
  -> session-shell / CBT-informed / MI-inspired rule execution
  -> stable tuple[Finding, ...]
```

`careloop.process.registry` may read and validate explicitly supplied local JSON.
The evaluator classes themselves perform no file I/O and accept only a validated
`ProcessPolicyRegistry` and `Trajectory`. `careloop.process` depends on domain,
Pydantic, and the standard library; it has no application, CLI/UI, provider,
network, benchmark, gold, safety-runtime, reporter, or wall-clock dependency.

The three specialized evaluators filter one shared ordered registry by their
declared evaluator name. `ProcessTrajectoryEvaluator` executes the complete
registry in registry order. Shared generic execution converts only frozen text
signals and typed process markers into evidence-linked findings; rule facts stay
in policy JSON rather than presentation or report code.

Milestone 3 does not implement the future `EvaluateTrajectory` application use
case or `FinalAnswerEvaluator`. It therefore cannot load artifacts or gold by
itself and does not add a CLI command.
