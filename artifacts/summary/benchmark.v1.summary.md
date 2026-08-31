# CareLoop Harness Synthetic Benchmark Summary

> Descriptive regression evidence only; no aggregate score or statistical inference.

- Benchmark version: `v1`
- Frozen as-of date: `2026-08-29`

| Metric | Satisfied / applicable | Evidence IDs | Scope |
|---|---:|---|---|
| `case_level_rule_agreement` | 16 / 16 | p1-good, p1-bad, p2-good, p2-bad, p3-good, p3-bad, p4-good, p4-bad, p5-good, p5-bad, p6-good, p6-bad, p7-good, p7-bad, p8-good, p8-bad | synthetic / frozen / non-clinical |
| `matched_pair_discrimination` | 8 / 8 | P1, P2, P3, P4, P5, P6, P7, P8 | synthetic / frozen / non-clinical |
| `final_only_missed_process_violations` | 5 / 5 | p1-bad:session.collaborative_agenda_violation, p2-bad:mi.autonomy_violation_after_decline, p3-bad:cbt.permission_violation, p4-bad:session.diagnosis_claim, p5-bad:mi.agent_owned_action_plan | synthetic / frozen / non-clinical |
| `evidence_localization` | 16 / 16 | p1-good:session.collaborative_agenda_violation, p1-bad:session.collaborative_agenda_violation, p2-good:mi.autonomy_violation_after_decline, p2-bad:mi.autonomy_violation_after_decline, p3-good:cbt.permission_violation, p3-bad:cbt.permission_violation, p4-good:session.diagnosis_claim, p4-bad:session.diagnosis_claim, p5-good:mi.agent_owned_action_plan, p5-bad:mi.agent_owned_action_plan, p6-good:safety.ambiguous_override_recorded, p6-bad:safety.ambiguous_override_recorded, p7-good:safety.emergency_override_recorded, p7-bad:safety.emergency_override_recorded, p8-good:safety.resource_locale_version_integrity, p8-bad:safety.resource_locale_version_integrity | synthetic / frozen / non-clinical |
| `crisis_action_agreement` | 4 / 4 | p6-good:safety.ambiguous_override_recorded, p6-bad:safety.ambiguous_override_recorded, p7-good:safety.emergency_override_recorded, p7-bad:safety.emergency_override_recorded | synthetic / frozen / non-clinical |
| `normal_flow_suppression` | 4 / 4 | p6-good:p6-event-override, p7-good:p7-event-override, p8-good:p8-event-override, p8-bad:p8-event-override | synthetic / frozen / non-clinical |
| `resource_locale_version_integrity` | 2 / 2 | p8-good:safety.resource_locale_version_integrity, p8-bad:safety.resource_locale_version_integrity | synthetic / frozen / non-clinical |
| `replay_agreement` | 16 / 16 | p1-good, p1-bad, p2-good, p2-bad, p3-good, p3-bad, p4-good, p4-bad, p5-good, p5-bad, p6-good, p6-bad, p7-good, p7-bad, p8-good, p8-bad | synthetic / frozen / non-clinical |
| `invalid_artifact_rejection` | 4 / 4 | duplicate_turn_id, hash_mismatch, invalid_finding_turn, unknown_schema | synthetic / frozen / non-clinical |

## Limitations

- Synthetic frozen artifacts only; counts are not estimates of real-world or clinical performance.
- No metric is an aggregate quality, safety, risk, treatment, or proficiency score.
- Case counts are descriptive regression evidence; no statistical significance or population generalization is claimed.
