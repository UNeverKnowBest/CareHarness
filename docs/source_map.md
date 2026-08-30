# Milestone 3 Process Source Map

Status: **FROZEN for Milestone 3**

This map records the local normative sources for the deterministic process
policy. It does not claim clinical validity, treatment effectiveness, or
proficiency against a clinical coding instrument.

| Source ID | Local source | Normative scope |
|---|---|---|
| `source-agents-process-invariants` | `AGENTS.md`, Process invariants | CBT is only a generic collaborative shell; MI may move backward and forward; Planning, support-only, refusal, and no-plan endings are optional/valid. |
| `source-guide-m3-process-evaluator` | `CareLoop_Codex_工程化实施指南_ZH.md`, §9 | Deterministic evaluator boundary, observable evidence, permission/autonomy/agenda/action ownership rule IDs, one agreed CBT skill path, stable findings, and positive/negative/uncertain tests. |
| `source-spec-professional-boundary` | `SPEC.md`, Product boundary | Findings describe observable artifact behavior and must not infer diagnosis, risk, or mental state. |

## Interpretation boundary

- The versioned policy registry is the executable behavior source. Gold files
  are comparison data and are not policy sources.
- Text signals are exact, case-insensitive phrases frozen for synthetic fixtures;
  they are not a general natural-language classifier.
- A diagnosis claim rule detects an observable prohibited phrase in synthetic
  assistant text. It does not diagnose a person or infer a condition.
- `present` means the named observable policy violation is present; `absent`
  requires a frozen counter-signal; `uncertain` means neither signal was found.
