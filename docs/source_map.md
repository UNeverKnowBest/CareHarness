# CareLoop Harness Source Map

Status: **FROZEN through Milestone 4**

This map records the local normative sources for the deterministic process
policy. It does not claim clinical validity, treatment effectiveness, or
proficiency against a clinical coding instrument.

| Source ID | Local source | Normative scope |
|---|---|---|
| `source-agents-process-invariants` | `AGENTS.md`, Process invariants | CBT is only a generic collaborative shell; MI may move backward and forward; Planning, support-only, refusal, and no-plan endings are optional/valid. |
| `source-guide-m3-process-evaluator` | `CareLoop_Codex_工程化实施指南_ZH.md`, §9 | Deterministic evaluator boundary, observable evidence, permission/autonomy/agenda/action ownership rule IDs, one agreed CBT skill path, stable findings, and positive/negative/uncertain tests. |
| `source-spec-professional-boundary` | `SPEC.md`, Product boundary | Findings describe observable artifact behavior and must not infer diagnosis, risk, or mental state. |
| `source-agents-crisis-invariants` | `AGENTS.md`, Crisis invariants | Safety routing precedes normal flow; override suppresses normal flow; failures fail closed; resources are explicit and jurisdiction/date matched. |
| `source-guide-m4-safety` | `CareLoop_Codex_工程化实施指南_ZH.md`, §10 | Frozen synthetic signal categories, typed actions, fail-closed behavior, resource integrity, ethical output categories, and P6–P8 test gates. |
| `source-professional-boundary` | `SPEC.md`, Product boundary | No diagnosis, medication advice, clinical claims, risk classification, or real-world detector claim. |

## Interpretation boundary

- The versioned policy registry is the executable behavior source. Gold files
  are comparison data and are not policy sources.
- Text signals are exact, case-insensitive phrases frozen for synthetic fixtures;
  they are not a general natural-language classifier.
- A diagnosis claim rule detects an observable prohibited phrase in synthetic
  assistant text. It does not diagnose a person or infer a condition.
- `present` means the named observable policy violation is present; `absent`
  requires a frozen counter-signal; `uncertain` means neither signal was found.

## Milestone 4 safety interpretation boundary

- Crisis signal phrases are exact synthetic fixture tags. Matching them proves
  deterministic control flow only; it is not a real-world detector evaluation.
- Historical, third-party, quoted, and ambiguous tags map to a typed clarify
  action. Current-plan, current-preparation, and already-acted tags map to the
  typed emergency-help system action. These are action fixtures, not risk levels.
- Resource records use `.invalid` provenance URLs and synthetic contacts so the
  harness cannot be mistaken for a real hotline directory.
- Ethical rules inspect generated assistant output before release. They describe
  observable output-policy violations without inferring user state.
