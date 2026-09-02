# Safety and Limitations

CareLoop Harness is an offline, deterministic evaluator for synthetic artifacts.
It is not therapy, diagnosis, suicide-risk assessment, crisis care, a medical
device, or evidence of real-world safety.

Milestones 3 and 4 evaluate only frozen observable process and synthetic safety
signals. Exact phrase matching is deliberately narrow and must not be used on
real conversations or described as understanding intent, mental state,
treatment quality, clinical proficiency, or real-world crisis detection.
Findings and actions describe artifact/control-flow behavior only.

The Milestone 4 `SyntheticSafetySignalDetector` recognizes only exact tags in
synthetic fixtures. It does not implement a clinical screening instrument,
machine-learning classifier, real-world safety detector, complete safety plan,
medication advice, automatic third-party contact, or risk score. Typed actions
say what the harness does; they do not classify a person.

Scenario text remains untrusted data. Evaluators inspect validated strings and
markers but never execute their contents. Policy and artifact inputs are local;
the evaluator has no model, provider, network, UI, gold-label, or wall-clock
dependency.

All resource records and contacts are synthetic and use `.invalid` provenance
URLs. Selection requires an explicit jurisdiction and `as_of` date, exact locale
match, allowlisting, source registration, version match, and active dates.
Missing or invalid resource evidence fails closed without guessing a contact.

The ethical output gate uses frozen exact phrases for role impersonation,
diagnosis, medication, coercion, invalidation, over-reassurance, dependency,
confidentiality, clinical overclaim, and crisis-flow continuation. This is a
deterministic regression surface, not a comprehensive content-safety system.

Milestone 5 adds offline observation of already-recorded synthetic safety events
and resource references. It does not rerun the runtime, broaden signal matching,
or validate real-world response quality. The final-only/trajectory comparison
and benchmark agreement are evidence-ledger results over 16 frozen cases, not
clinical, population, or statistical performance estimates.

The optional audit page is a deterministic local HTML file with escaped artifact
text, inline CSS, and no scripts or remote assets. It is read-only, performs no
upload or network request, and contains no editable chat or automated action.

Milestone 6 summaries are descriptive counts derived from 16 frozen synthetic
benchmark cases and four frozen invalid fixtures. They are regression evidence,
not measurements of a population, person, treatment, clinical process, or
real-world safety system. The harness reports no aggregate score, percentage,
confidence interval, statistical significance, suicide-detection accuracy,
clinical sensitivity/specificity, treatment success, or patient-safety
improvement.

Replay and invalid-fixture results prove only that the local deterministic
artifact contracts accept or reject the frozen inputs as specified. Mutation
proof shows that one existing P7 regression test detects a deliberately broken
control-flow branch; it does not validate real-world crisis handling.

Milestone 8 defines only a future synthetic agent-runtime contract and pure
state machine. `SafetyDisposition` values are system-routing states, not risk
levels, diagnoses, clinical dispositions, or statements about a person. The
model port has no concrete adapter and makes no request. Draft quarantine,
bounded rewrite, plugin failure modes, and human-review states are design and
control-flow properties; they do not prove that a future model output is safe.

The planned participant-shaped interface remains restricted to researchers
role-playing versioned synthetic personas. It is not approved for real patient
data or ordinary public use. Human review is a local demonstration workflow,
not a staffed clinical or emergency service.

Milestone 9 discovers only explicitly allowlisted local plugin manifests and
uses deterministic test adapters to verify the provider-neutral model boundary.
No plugin or provider is bundled or enabled, and no network call is made. A
successful result is still a quarantined draft, not participant-visible output;
provider, validation, or identity failure transitions the synthetic runtime to
`FAILED_CLOSED`. These controls do not establish that any future model output,
plugin, reviewer, or operational workflow is safe or clinically effective.

Milestone 10 composes the exact synthetic input router, quarantined model port,
and deterministic draft-gate decisions in one local application service. A
typed override suppresses ordinary generation, and a critical component failure
produces no released reply. The two-rewrite limit and in-memory event ledger are
control-flow evidence only. They do not validate model meaning, detect real
crises, provide staffed review, make synthetic resources real, or establish an
operationally safe participant system.

Milestone 11 resolves a synthetic pre-release review hold using explicit typed
decisions and append-only events. Approval or replacement is deterministic
control flow, not evidence that the content is safe, clinically appropriate, or
professionally reviewed. Handoff is only a closed local state; it does not
contact a person, clinician, emergency service, or external system. No reviewer
identity, staffing, notification, authentication, durable queue, or operational
response is implemented.

Milestone 12 assembles and evaluates only a detached synthetic session snapshot
whose turns already have submit, suppressed-override, or release evidence. It
reuses exact offline evaluator rules and produces no new detector, clinical
interpretation, benchmark comparison, or score. A successful close proves only
append-before-report and deterministic evaluation of that snapshot; it does not
establish session quality, model-output safety, clinical appropriateness,
effective review, or real-world safety. The transcript, ledger, idempotency, and
reports remain process-local and non-durable.

Milestone 13 freezes only a future full-stack research contract. The allowed
participant-shaped use remains adult synthetic role-play with no protected
health information. Its simulated review queue is not staffed clinical care or
an emergency service. `ReleaseDispositionV1` controls text release only and is
not a risk assessment. No model rewrite can establish that a person's risk has
cleared; after at most two repair attempts, unresolved output remains withheld
for simulated review. The future status-only SSE contract releases no raw model
token or quarantined draft. The evidence registry is entirely
`advisor_review_pending` and does not constitute an approved protocol.

Milestone 14 implements storage, notification, and model-provider adapters only.
It does not establish provider quality, output safety, effective supervision,
clinical appropriateness, treatment benefit, or crisis detection. Provider
responses remain quarantined and non-streaming. SQLite repository tests do not
prove PostgreSQL behavior; the PostgreSQL dialect and offline migration are
verified, while live PostgreSQL and Redis integration was unavailable in the
execution environment. Redis publication is at least once and consumers must
deduplicate from authoritative event identity.

Milestone 15 composes only adult synthetic role-play controls. Its queue is a
simulated human-review queue and is not staffed care; it contacts no clinician,
emergency service, family member, authority, or other third party. The explicit
review target is a descriptive research target, not a clinical or operational
SLA. Pending/claimed/resolved counts and before/after-target IDs describe stored
artifacts only. They do not measure a person's condition, reviewer quality, or
real-world responsiveness. Approval or replacement does not establish that a
draft is safe, that risk has cleared, or that the system is clinically
appropriate. Live PostgreSQL/Redis concurrency, an actual queue worker,
authentication, staffing, notification, and recovery operations remain
unverified and outside M15.
