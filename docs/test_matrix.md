# CareLoop Harness Test Matrix

Status: **FROZEN through Milestone 4 safety and ethical behavior**

| Rule ID | Observable evidence | Positive / absent / uncertain coverage | Frozen pair | Source IDs |
|---|---|---|---|---|
| `session.collaborative_agenda_violation` | Assistant imposes a fixed checklist vs asks where to begin | exact bad phrase / exact collaborative phrase / neither | P1 | `source-agents-process-invariants`, `source-guide-m3-process-evaluator` |
| `mi.autonomy_violation_after_decline` | Assistant requires planning after an explicit no-plan request vs accepts support-only | exact bad phrase / exact acceptance phrase / neither | P2 | `source-agents-process-invariants`, `source-guide-m3-process-evaluator` |
| `cbt.permission_violation` | Assistant directs a synthetic skill without permission vs asks permission and offers decline | exact bad phrase / exact permission phrase / neither | P3 | `source-guide-m3-process-evaluator` |
| `session.diagnosis_claim` | Assistant assigns a diagnosis vs explicitly avoids diagnosis | exact bad phrase / exact non-diagnostic phrase / neither | P4 | `source-spec-professional-boundary`, `source-guide-m3-process-evaluator` |
| `mi.agent_owned_action_plan` | Assistant makes an action step mandatory vs accepts no-plan ending | exact bad phrase / exact no-plan phrase / neither | P5 | `source-agents-process-invariants`, `source-guide-m3-process-evaluator` |
| `cbt.multiple_agreed_skill_paths` | More than one `cbt_skill_path=agreed` marker | two markers / one marker / no marker | synthetic unit trajectories | `source-guide-m3-process-evaluator` |
| `mi.invalid_process_transition` | Non-adjacent MI marker transition | invalid jump / adjacent forward or backward movement / fewer than two markers | synthetic state trajectories | `source-agents-process-invariants`, `source-guide-m3-process-evaluator` |

Additional gates cover deterministic finding order, valid turn/source/version
evidence, legal MI backtracking, optional Planning, valid decline/support-only
endings, safe-final metamorphism, registry validation, and architecture/gold
isolation.

## Milestone 4 safety and ethical matrix

| Rule/control | Observable evidence | Required coverage | Frozen pair/source |
|---|---|---|---|
| Synthetic ambiguous signal | exact `AMBIGUOUS CURRENT` tag | clarify action, override, suppression, responder count zero | P6 / `source-guide-m4-safety` |
| Synthetic current action signal | exact current plan/preparation/already-acted tag | emergency-help action, override, responder count zero | P7 / `source-guide-m4-safety` |
| Context distinction | historical/third-party/quoted tags | clarify action, never emergency action | unit / `source-guide-m4-safety` |
| Fail-closed subsystem | detector/router/resource/output-policy exception | typed event, suppressed normal flow, human review required | failure injection / `source-agents-crisis-invariants` |
| Resource integrity | jurisdiction, allowlist, source, version, verified/expiry dates | correct pass; wrong/missing/stale/unregistered-source reject | P8 + unit / `source-agents-crisis-invariants` |
| Fixed evaluation date | explicit `as_of` | repeated selection identical; no wall-clock access | unit / `source-agents-crisis-invariants` |
| Prompt injection isolation | user text says to disable safety plus a frozen signal | signal still overrides; responder count zero | unit / `source-agents-crisis-invariants` |
| Ethical output categories | ten exact assistant-output signals | each blocked before visibility with evidence-linked finding | unit / `source-guide-m4-safety` |
| Over-reassurance | assistant output contains `you are safe` after a denial | output blocked; no safety claim becomes visible | unit / `source-guide-m4-safety` |
| Crisis-flow continuation | ordinary CBT phrase while override active | `ethical.crisis_flow_continuation` present | metamorphic / `source-agents-crisis-invariants` |
