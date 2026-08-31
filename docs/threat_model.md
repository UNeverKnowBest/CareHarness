# Threat Model

## Scope and assets

CareLoop Harness operates only on local frozen synthetic artifacts. Protected
assets are canonical artifact identity, version selectors, evidence references,
evaluation-before-gold ordering, crisis-flow suppression, resource provenance,
and deterministic generated reports.

## Trust boundaries and threats

| Boundary | Threat | Control |
|---|---|---|
| Scenario text | Untrusted text attempts to act as instructions | Text remains validated data; no model, shell, template execution, or network call interprets it |
| Artifact loading | Hash, schema, encoding, identity, or reference tampering | Strict Pydantic schemas, canonical-byte comparison, SHA-256 reconstruction, and aggregate reference checks reject the artifact |
| Evaluation | Gold leakage changes evaluator output | Evaluators cannot import gold; application records actual output before invoking the gold loader |
| Safety runtime | Detector/router/resource/output-policy failure resumes normal flow | One typed fail-closed boundary suppresses normal output and requires human review |
| Resource evidence | Missing, wrong, stale, or unregistered locale data selects a contact | Exact synthetic jurisdiction, source, version, allowlist, and explicit `as_of` checks; no guessed resource |
| Reporting | Handwritten or stale numbers diverge from raw evidence | Strict canonical raw parsing and deterministic raw-to-summary regeneration; CI checks the generated diff |
| Presentation | Artifact text injects active browser content | Static audit escapes untrusted text and permits no script or remote asset |
| Supply chain | Dependency drift changes execution | Python 3.12, committed uv lockfile, locked CI synchronization, and no provider/network runtime dependency |

## Failure posture

Invalid local data fails visibly. Safety subsystem exceptions fail closed rather
than continuing ordinary response flow. Reporting rejects malformed,
noncanonical, incomplete, or reordered raw evidence. A correctly formed
behavior mismatch remains visible as unsatisfied evidence rather than being
discarded as a parsing error.

## Explicit non-goals

This threat model does not claim protection for real patient data, production
multi-user deployment, clinical decision-making, real-world crisis detection,
regulatory compliance, or internet-facing services; none are implemented.
