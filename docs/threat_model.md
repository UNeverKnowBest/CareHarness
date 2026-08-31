# Agent Runtime Threat Model

Status: **FROZEN for the synthetic Milestone 8 design**

## Assets and trust boundaries

Protected assets are quarantined drafts, released synthetic turns, policy and
prompt versions, plugin configuration, reviewer decisions, raw evaluation
artifacts, and provider credentials. Scenario text, role-play input, model
output, provider responses, plugin packages, and browser data are untrusted.
The project uses Synthetic data only and is not approved for real patient data.

## Threats and mandatory controls

| Threat | Boundary | Required control and acceptance evidence |
|---|---|---|
| Prompt injection | Scenario and role-play text attempts to alter system rules or enable plugins. | Treat text only as data; input routing precedes generation; configuration is never derived from model text. |
| Unsafe draft release | A model draft contains prohibited or crisis-flow content. | Quarantine every draft, run all required guards, release atomically, and expose no raw-token stream. |
| Unbounded repair | Rewriting repeatedly hides a persistent failure or consumes resources. | Enforce the contract constant of two rewrites, then hold for human review. |
| Provider failure | Timeout, malformed response, authentication error, or unavailable cloud service. | Record structured failure evidence, emit `RUNTIME_FAILURE`, and fail closed without a fallback reply. |
| Plugin supply chain | Unapproved, incompatible, or malicious plugin executes in the runtime. | Discover only allowlisted entry points, validate `PluginManifestV1`, pin versions, reject conflicts, and fail closed for critical kinds. |
| Sensitive data disclosure | Input, draft, prompt, secret, or report leaks through logs or provider calls. | Synthetic data only; redact operational logs; secrets never enter events; provider adapter sends only the declared request; no chain-of-thought is stored. |
| Audit tampering | A transition, draft decision, or review outcome is overwritten. | Use an append-only event ledger, immutable provenance, monotonic sequence, and superseding decisions rather than updates. |
| Role boundary bypass | Participant-facing code reads a quarantined draft or reviewer-only evidence. | Separate response projections and application queries; participant endpoints return released content only. |
| Cross-session confusion | Retry or concurrent submission associates output with the wrong turn. | Require session-scoped IDs, write idempotency keys, explicit causation IDs, and transactional state transition checks. |
| Replay nondeterminism | Clock, network, random provider result, or mutable plugin profile changes evidence. | Replay reads frozen artifacts only; store exact prompt/plugin/model identities; exclude runtime metadata from canonical identity. |
| False clinical interpretation | A reviewer mistakes system routing for diagnosis or validated safety assessment. | Use non-clinical vocabulary and persistent research-only limitations in UI and reports; do not expose scores or probabilities. |
| Resource guessing | Missing locale causes an invented emergency contact. | Select only allowlisted, versioned, jurisdiction-matched resources at explicit `as_of`; otherwise require review with no guessed contact. |

## Existing offline harness controls retained

| Threat | Required control |
|---|---|
| Artifact identity or reference tampering | Canonical-byte comparison, SHA-256 reconstruction, strict schemas, and aggregate reference validation reject the artifact. |
| Gold leakage | Evaluators cannot import gold; application orchestration records actual evaluation before loading gold. |
| Stale or handwritten summaries | Strict raw parsing and deterministic regeneration derive every count; CI checks generated artifact diffs. |
| Static audit injection | Untrusted artifact text is escaped and the page contains no script or remote asset. |
| Dependency drift | Python 3.12, the committed `uv.lock`, and locked verification preserve the offline evaluator environment. |

## Out-of-scope claims and residual risk

The controls demonstrate artifact and orchestration behavior, not real-world
safety, clinical validity, treatment benefit, diagnostic accuracy, or crisis
detection accuracy. Model and policy defects can remain after all gates pass.
Human review in the local demo is simulated and is not an emergency response
service. A later real-participant study requires a new threat model, ethics and
privacy approval, operational response ownership, and jurisdiction-specific
legal review.
