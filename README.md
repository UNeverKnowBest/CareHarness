# CareLoop Harness

Project status: Milestone 16 complete. M16 adds a removable FastAPI/Next.js
research demonstration, OIDC and development-only synthetic identity adapters,
status-only SSE, versioned reports, and a local Docker Compose topology. The
frozen v1 offline evaluator and M12 library-level synthetic session flow remain
reproducible and independently operational.

CareLoop Harness is an **offline-first**, **deterministic** evaluation harness
for **synthetic** support-agent trajectories. It is deliberately
**non-clinical**: it is not therapy and not a medical device. It does not
provide diagnosis, suicide-risk assessment, or crisis care.

The project evaluates observable artifact and control-flow behavior. It does not
process real user data, call a model or network service, infer mental state,
produce a risk score, or claim clinical or real-world safety performance.

Its evidence chain is:

```text
frozen trajectory -> final-only + trajectory evaluation -> raw JSONL
                  -> deterministic replay/failure verification
                  -> derived JSON and Markdown summaries
```

## Interaction model

The offline CLI remains the primary reproducible evaluation surface and starts
no server. M16 additionally provides an explicitly local research Web/API demo
for adult synthetic role-play only; it accepts no protected health information
and is not a hosted, clinical, crisis, or emergency service.

M14 adds a
PostgreSQL/Alembic adapter, Redis transactional-outbox publisher, ARQ-compatible
worker function, immutable plugin profiles, and explicit DeepSeek, vLLM, and
Ollama model adapters. None is enabled by the CLI or supplied credentials by
default. `RunSyntheticTurn` remains library-only and releases a complete
synthetic turn only after routing, quarantined drafting, gate approval, and
event append all succeed.

M14 itself added no Web application or participant API; that historical scope
remains unchanged even though M16 now supplies a removable outer surface.

M15 adds `SupervisedSyntheticTurn` and `ResolveQueuedSyntheticReview` as
library-only composition. Exhausted repairs retain the final complete draft in
the reviewer-only SQL queue; claim and decision use optimistic revisions. A
typed review event, outbox record, session projection, and resolved queue row
commit together before a participant projection can be returned. The queue is
simulated research infrastructure, is not staffed care, and contacts nobody.

The M12 in-memory trajectory evaluation and append-only in-memory ledger remain
available for deterministic tests. No installed plugin is enabled by default;
M14 profiles describe only explicit preinstalled adapter selections.

`careloop evaluate` can optionally generate read-only static HTML for local
audit. That HTML is a file opened by the user: it has no server, JavaScript,
remote assets, editable controls, model calls, uploads, or network dependency.
Deleting the presentation package and generated HTML does not affect evaluation,
replay, benchmark execution, or reporting.

`ResolveSyntheticReview` remains the in-memory library boundary. M15's durable
wrapper maps the same four typed decisions to existing transitions; neither is
a staffed service, participant endpoint, or claim that approved model text is
safe.

`CloseSyntheticSession` is library-only as well. It validates a detached
synthetic session snapshot against submit, override, and release evidence,
evaluates a canonical in-memory trajectory with the existing offline
evaluators, and releases a report only after the close event is appended. It
adds no CLI command, file writer, server, durable session store, or participant
workflow.

M16 implements the frozen `/api/v1` participant, review, report, and plugin
surface behind strict roles. Participant SSE contains public status and only a
complete already gated answer. The Next.js application has English and Chinese
participant, simulated reviewer, and admin routes. The simulated review queue is
not staffed care and contacts no clinicians, emergency services, family,
authorities, or other third parties.

The next milestone is M17: final evaluation, cloud-template validation, and
delivery work. M16 does not authorize real-user data, clinical claims, provider
credentials, or a cloud deployment.

## Local research Web demonstration

The Compose topology uses fixed development credentials and an explicit local
synthetic identity adapter; that adapter refuses production mode. With Docker
and the required images available, start the five local services with:

```text
docker compose up --build
```

Then open `http://localhost:3000/en/participant` or
`http://localhost:3000/zh-CN/participant`. API readiness is exposed at
`http://localhost:8000/health/ready`. Do not enter real-person or protected
health information. Stopping/removing the Compose topology does not affect the
offline evaluator; the named PostgreSQL development volume persists until the
operator explicitly removes it.

## Reproduce from the lockfile

Python 3.12 and `uv` are required. No API key, model provider, database, browser,
or network service is needed at runtime. For a clean reproduction, use a fresh
checkout without an existing virtual environment and run:

```text
uv sync --locked
uv run --locked python --version
uv run --locked careloop --version
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src
uv run --locked pytest -q
uv run --locked careloop benchmark --manifest benchmarks/manifest.v1.json
uv run --locked python tools/generate_milestone2_fixtures.py --check
git diff --exit-code -- artifacts/raw artifacts/summary
cd web
npm ci
npm run typecheck
npm run build
npm run test:e2e
```

A successful run proves only deterministic behavior for the frozen synthetic
fixtures in this repository. It is not evidence of clinical validity,
real-world safety, treatment effectiveness, or population performance.

## CLI commands

Inspect the exact arguments with `uv run --locked careloop <command> --help`.
The supported business commands are:

- `evaluate`: evaluate one canonical synthetic trajectory and write a raw
  evidence ledger plus optional local static audit HTML.
- `replay`: reconstruct and verify one local frozen artifact without a model,
  network, adapter, or wall clock.
- `benchmark`: evaluate the ordered corpus, load gold only after actual
  evaluation, verify replay/failure fixtures, and derive summaries.

Help and package version are available through:

```text
uv run --locked careloop --help
uv run --locked careloop --version
```

## Generated artifacts

The benchmark command is the only supported way to regenerate result artifacts:

- `artifacts/raw/benchmark.v1.jsonl`: 16 manifest-ordered evaluation/comparison
  records;
- `artifacts/raw/verification.v1.jsonl`: replay agreement plus frozen invalid
  artifact rejection evidence;
- `artifacts/summary/benchmark.v1.summary.json`: canonical derived summary;
- `artifacts/summary/benchmark.v1.summary.md`: deterministic human-readable
  summary;
- `artifacts/audit/*.html`: optional local read-only audit pages produced by
  `evaluate`.

Generated counts and artifact bytes must never be edited manually. Change raw
inputs or implementation through an explicitly versioned milestone, regenerate
through the CLI/generator, and review the resulting diff.

## Maintenance contract

Every future change must preserve the boundaries in `AGENTS.md`, use synthetic
data only, add a failing test before behavior, keep public schemas and frozen
fixtures unchanged unless explicitly versioned, and pass the complete locked
verification sequence above. Evaluator decisions run before gold is loaded;
replay and reporting remain offline and deterministic.

Normative behavior and evidence are documented in:

- [`SPEC.md`](SPEC.md): schemas, evaluator/report contracts, and prohibited
  claims;
- [`ARCHITECTURE.md`](ARCHITECTURE.md): dependency direction and removable
  presentation boundary;
- [`docs/technical_report.md`](docs/technical_report.md): evidence chain without
  copied result counts;
- [`docs/threat_model.md`](docs/threat_model.md): trust boundaries and failure
  controls;
- [`docs/safety_and_limitations.md`](docs/safety_and_limitations.md): mandatory
  interpretation limits;
- [`STATUS.md`](STATUS.md): exact milestone commands, exit statuses, counts, and
  unresolved risks.

README statements are navigation and operating guidance, not independent proof.
Use the versioned raw artifacts, generated summaries, tests, and recorded command
results for verification.
