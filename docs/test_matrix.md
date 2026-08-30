# CareLoop Harness Test Matrix

Status: **FROZEN for Milestone 3 process behavior**

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
