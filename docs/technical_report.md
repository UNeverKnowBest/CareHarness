# Technical Report

## Purpose

CareLoop Harness demonstrates a reproducible offline evaluation chain for frozen
synthetic support-agent trajectories. Its contribution is typed/versioned
evidence, final-only versus complete-trajectory comparison, crisis-flow
suppression, locale/version resource integrity, deterministic replay, and
matched-pair regression benchmarking. It is non-clinical and makes no
real-world safety or treatment claim.

## Architecture and evidence flow

The runtime demonstration and offline evaluator are separate. Runtime safety
routing occurs before an injected responder and fails closed. Offline evaluation
loads canonical frozen artifacts, constructs a restricted `FinalAnswerView`,
runs final-only and trajectory-aware evaluators, then loads gold comparison data
only after actual findings exist.

`RunBenchmark` writes the ordered benchmark raw JSONL first. It then records
local replay identity and the expected rejection reason for each frozen invalid
fixture in a separate verification JSONL. The reporting package parses those raw
files strictly and derives summary JSON and Markdown without loading policies,
evaluators, or gold files.

## Result evidence

Generated result counts are not copied into this document. The authoritative
descriptive table is regenerated at
`artifacts/summary/benchmark.v1.summary.md`; its canonical machine-readable form
is `artifacts/summary/benchmark.v1.summary.json`. Their inputs are
`artifacts/raw/benchmark.v1.jsonl` and
`artifacts/raw/verification.v1.jsonl`.

The table contains only the nine metrics allowed by `SPEC.md`, expressed as
satisfied and applicable evidence counts with concrete IDs. It has no combined
score, percentage, ranking, confidence interval, significance statement, or
population estimate.

Milestone 17 adds a separate integration evidence chain. Sixteen new adult
synthetic cases form eight ordered English/Chinese control/challenge stimulus
pairs. Actual runtime observations complete before the separate M17 expectation
file is loaded. The canonical raw evidence is
`artifacts/raw/m17.final-evaluation.v1.json`; the human-readable report at
`artifacts/summary/m17.final-evaluation.v1.md` is derived from that raw model by
the M17 generator. These files neither replace nor modify the original P1–P8
benchmark evidence.

The GCP Terraform directory is delivery architecture evidence only. It defaults
service deployment off and describes restricted Cloud Run, authoritative
regional private Cloud SQL, ephemeral private Memorystore, Secret Manager, and
separate service accounts. No live cloud validation occurred; see the recovery
runbook and release checklist for prerequisites and stop conditions.

## Reproducibility and mutation evidence

The locked verification sequence is documented in the README and automated in
`.github/workflows/verify.yml`. Raw-to-summary recomputation is covered by a
byte-equality regression test. The temporary P7 mutation proof and exact command
results are recorded in `STATUS.md`; the deliberately broken code is never
committed.

## Limitations

All trajectories, signals, resources, and contacts are frozen synthetic
fixtures. Exact phrase/tag behavior is not language understanding. Agreement and
discrimination counts describe this regression corpus only. See
`docs/safety_and_limitations.md` and `docs/threat_model.md` for the complete
interpretation and threat boundaries.
