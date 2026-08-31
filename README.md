# CareLoop Harness

CareLoop Harness is an **offline-first**, **deterministic** evaluation harness
for **synthetic** support-agent trajectories. It is deliberately
**non-clinical**: it is not therapy and not a medical device. It does not
provide diagnosis, suicide-risk assessment, or crisis care.

The project evaluates observable artifact and control-flow behavior. It does not
process real user data, call a model or network service, infer mental state,
produce a risk score, or claim clinical or real-world safety performance.

Its core evidence chain is:

```text
frozen trajectory -> final-only + trajectory evaluation -> raw JSONL
                  -> deterministic replay/failure verification
                  -> derived JSON and Markdown summaries
```

## Reproduce locally

Python 3.12 and `uv` are required. No API key, model provider, database, or
browser is needed.

```text
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run careloop benchmark --manifest benchmarks/manifest.v1.json
```

The benchmark command regenerates the canonical
[`benchmark.v1.jsonl`](artifacts/raw/benchmark.v1.jsonl), verification raw
evidence, and the derived
[`benchmark.v1.summary.md`](artifacts/summary/benchmark.v1.summary.md). Summary
counts are generated from raw artifacts and must never be edited manually.

## Commands

- `careloop evaluate`: evaluate one canonical synthetic trajectory and write a
  raw evidence ledger plus optional static audit HTML.
- `careloop replay`: reconstruct and verify one local frozen artifact without a
  model, network, adapter, or wall clock.
- `careloop benchmark`: evaluate the ordered corpus, compare only after actual
  evaluation, verify replay/failure fixtures, and derive summaries.

See [`SPEC.md`](SPEC.md) for behavior, [`ARCHITECTURE.md`](ARCHITECTURE.md) for
dependency boundaries, [`docs/technical_report.md`](docs/technical_report.md)
for the evidence chain, and
[`docs/safety_and_limitations.md`](docs/safety_and_limitations.md) before
interpreting any generated result.
