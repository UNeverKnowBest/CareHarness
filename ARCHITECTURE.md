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

## Milestone 4 synthetic safety runtime boundary

### FROZEN

Milestone 4 adds this synthetic-only control-flow demonstration:

```text
validated user Turn + explicit jurisdiction/as_of
  -> SyntheticSafetySignalDetector
     -> override -> CrisisRouter -> ResourcePolicyRegistry -> suppressed event
     -> continue -> injected responder -> EthicalOutputPolicy
        -> allowed -> visible assistant Turn
        -> blocked/exception -> suppressed fail-closed event + human review
```

`careloop.safety` depends on domain, Pydantic, and the standard library. It does
not import application, CLI/UI, process internals, provider/network clients,
benchmarks, gold, tests, reporters, or wall-clock services. The responder is an
injected callable protocol; no adapter implementation or model call is added.

Registry loading is explicit local JSON I/O. Once registries are validated, the
detector, router, selector, output policy, and runtime are deterministic for
their explicit inputs. Resource decisions accept an `as_of: date`; no code path
reads `date.today()` or `datetime.now()`.

The runtime guarantees ordering by construction: detector before responder and
output policy after responder but before `visible_output`. Override results have
no evaluated or visible normal output. Blocked output is retained only as typed
audit evidence and never placed in `visible_output`.

All safety subsystem exceptions cross one typed fail-closed boundary. The
boundary returns a suppressed `SafetyEvent` and `HUMAN_REVIEW_REQUIRED`; it never
catches an exception and resumes ordinary flow. Resource selection failure after
an emergency action cannot guess a contact or call the responder.

Milestone 4 remains separate from the future `EvaluateTrajectory` and
`RunBenchmark` application use cases and adds no CLI command.

## Milestone 5 application and presentation boundary

### FROZEN

Milestone 5 completes the planned application boundary without adding another
business use case:

```text
EvaluateTrajectory
  canonical artifact -> FinalAnswerView -> FinalAnswerEvaluator
                     -> complete Trajectory -> TrajectoryEvaluator
                     -> immutable evidence ledger (no gold)

ReplayArtifact
  canonical artifact -> verified bytes/hash/domain object

RunBenchmark
  manifest case -> EvaluateTrajectory -> actual result
                -> only then load gold -> comparison -> raw JSONL
```

`careloop.evaluation` depends only on domain plus public process/safety
interfaces. It owns final-only, complete-trajectory, offline safety-artifact,
and comparison-free result models; it cannot import application, CLI,
presentation, benchmark files, gold, tests, adapters, network clients, or wall
clock services.

`careloop.application` composes validated registries, evaluators, local artifact
I/O, ordered benchmark execution, post-evaluation gold comparison, and raw
record writing. Gold loading exists only inside the benchmark use case and is
injectable so ordering is testable. `EvaluateTrajectory` and `ReplayArtifact`
have no gold dependency.

`careloop.presentation` receives only the application evaluation result and
renders escaped deterministic HTML. It has no policy loader, detector,
evaluator, gold, benchmark runner, model, or network dependency. The CLI is the
composition root and calls application services; it may pass their returned
view model to presentation rendering but contains no evaluation rules.

The audit surface is a generated local file, not a fourth application use case.
Removing `careloop.presentation` and all generated HTML leaves evaluate,
replay, benchmark, and every core test operational.

## Milestone 6 reporting and verification boundary

### FROZEN

Milestone 6 extends the existing `RunBenchmark` orchestration without adding a
fourth application use case:

```text
RunBenchmark
  -> write 16-case benchmark raw JSONL
  -> replay the same 16 local artifacts
  -> exercise four frozen invalid fixtures
  -> write verification raw JSONL
  -> pure raw parsers -> summary JSON + summary Markdown
```

`careloop.reporting` owns strict raw verification and summary models plus pure
derivation/rendering. It may depend on immutable domain/evaluation result types,
Pydantic, and the standard library. It does not import CLI, presentation,
process/safety evaluators, policy registries, benchmark gold loaders, provider
SDKs, network clients, tests, or wall-clock services.

Application orchestration owns local replay/failure execution and supplies only
raw records to reporting. Reporting never re-evaluates a trajectory, interprets
scenario text, selects a resource, or decides a gold outcome. CLI supplies paths
to `RunBenchmark`; it does not calculate metrics.

The existing benchmark raw remains the source for evaluation/gold comparison.
The separate verification raw prevents failure-fixture and replay evidence from
changing the 16-record manifest-order contract. Both raw files must exist before
summary derivation. Removing presentation or any hypothetical adapter leaves
benchmark, verification, and reporting operational.

## Milestone 8 agent-runtime contract boundary

### FROZEN

Milestone 8 adds `careloop.agent_runtime` as a pure inner contract layer:

```text
future Web/API/provider/database/plugin adapters
                    |
                    v
        future application orchestration
                    |
                    v
            careloop.agent_runtime
                    |
                    v
              careloop.domain
```

`careloop.agent_runtime` may import the standard library, Pydantic, and frozen
domain types. It never imports application, CLI, presentation, reporting,
evaluation, safety implementations, provider SDKs, network clients, database
libraries, Web frameworks, plugin packages, gold data, or tests.

The state machine is an explicit transition table. A model draft can reach
`RESPONSE_RELEASED` only from `CHECKING_DRAFT` or from an explicit review
decision. `RUNTIME_FAILURE` moves any nonterminal state to `FAILED_CLOSED`.
Closed and failed-closed sessions cannot be reopened. The rewrite-count
constraint lives in the versioned draft-gate contract, not in UI or adapter
code.

The asynchronous `ModelPort` is dependency inversion only. Concrete cloud or
local providers belong to removable outer adapters added by a later milestone.
The existing offline evaluator and replay paths do not import or call the port.

The planned HTTP surface calls future application services only. Participant
queries project released turns; reviewer queries may project quarantined drafts
and evidence. SSE is status-only. Persistence uses an authoritative append-only
event ledger plus replaceable projections; database timestamps never become
replay identity. The logical table and endpoint contracts are frozen in
`docs/agent_runtime_contract.md`, while actual Web and persistence technology is
deferred.

## Milestone 9 plugin and model-runtime boundary

### FROZEN

Milestone 9 adds two removable paths without composing a live session:

```text
local importlib metadata + PluginAllowlistV1
  -> pre-load group/name/value match
  -> PluginManifestV1 validation + exact identity/version
  -> dependency-before-dependant catalog

ModelRequest + injected ModelPort + exact provider manifest/model name
  -> provider call
  -> revalidated quarantined ModelDraft + DRAFT_GENERATED
  -> any provider/draft/correlation failure -> RUNTIME_FAILURE -> FAILED_CLOSED
```

`careloop.plugin_runtime` is an outer, removable local-discovery adapter. It may
depend on the standard library, Pydantic, and `careloop.agent_runtime` contracts.
It cannot import application, CLI, presentation, reporting, evaluation, safety
implementations, benchmark/gold data, network clients, provider SDKs, or tests.
The inner `careloop.agent_runtime` package cannot import `plugin_runtime`.

`ProviderNeutralModelRuntime` remains inside the provider-neutral runtime core.
It depends only on the existing port, runtime contracts, and state machine. It
returns either a quarantined draft or a typed failed-closed result; it does not
construct a visible `Turn`, run policy gates, choose a resource, retry, fall
back to another provider, or write persistence.

The only adapter used by M9 verification is a deterministic test adapter. No
plugin package is registered in project metadata, no default allowlist is
shipped, and the existing evaluator/replay/benchmark paths do not import or call
either M9 path.

## Milestone 10 application orchestration and storage boundary

### FROZEN

```text
SyntheticTurnCommand
  -> existing synthetic input pre-route
     -> override: no model call, no ordinary release
     -> failure: append RUNTIME_FAILURE, fail closed
     -> support: SUBMIT_TURN
        -> ProviderNeutralModelRuntime -> quarantined draft
        -> injected draft gate
           -> rewrite (maximum two) -> model runtime
           -> review hold -> no release
           -> allow -> persist DRAFT_APPROVED -> construct released Turn

all lifecycle transitions -> RuntimeEventLedgerPort
                         -> InMemoryRuntimeEventLedger
```

`careloop.application.synthetic_turn` owns `RunSyntheticTurn`, strict command
and result projections, idempotent command handling, and composition. It may
depend on domain, public agent-runtime contracts/ports, and public synthetic
safety interfaces. It contains no detector phrase, output-policy rule, resource
record, provider implementation, persistence technology, CLI, UI, gold,
benchmark, report, network, or wall-clock logic.

`careloop.runtime_storage` is a removable outer in-memory adapter implementing
`RuntimeEventLedgerPort`. It depends inward on agent-runtime contracts only and
cannot import application, safety, evaluation, reporting, presentation, CLI,
provider/plugin implementations, benchmark/gold data, or network/database code.
Removing both M10 packages leaves the original three offline use cases and all
frozen evidence paths operational.

Participant and research-review projections are separate types. The participant
projection can contain an atomically released turn and typed synthetic override
evidence, but never a model draft, draft-gate result, internal runtime event, or
failure detail. The research-review projection may contain quarantined drafts
and ordered evidence but is not a participant response.

## Milestone 11 synthetic review-resolution boundary

### FROZEN

```text
SyntheticReviewCommand + AWAITING_HUMAN_REVIEW ledger state
  -> verify last DRAFT_HELD_FOR_REVIEW identity
  -> map existing ReviewDecision to existing REVIEW_* event
  -> append decision event
     -> approve/replace: construct participant released Turn
     -> handoff/reject: CLOSED with no released Turn
  -> append failure: RUNTIME_FAILURE or typed ledger-unavailable error
```

`careloop.application.synthetic_review` owns strict reviewer command/result
models, an immutable authoritative held-draft snapshot, held-event correlation,
deterministic event construction, participant versus research-review projection
isolation, and process-local idempotency. It
may depend on domain, public agent-runtime contracts, and
`RuntimeEventLedgerPort`. It cannot import safety/process/evaluation/reporting
rules, plugin/provider implementations, CLI/UI, benchmark/gold data, network,
database, clock, or randomness.

M11 reuses the removable M10 ledger without extending its storage API. A review
decision is evidenced by the existing append-only `RuntimeEvent`; M11 adds no
mutable review table or projection store. The participant projection is formed
only after that event append succeeds. Removing M10/M11 runtime orchestration
leaves the original offline evaluate, replay, benchmark, reporting, fixtures,
and generated evidence paths operational.
