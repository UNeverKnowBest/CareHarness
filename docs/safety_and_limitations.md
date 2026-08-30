# Safety and Limitations

CareLoop Harness is an offline, deterministic evaluator for synthetic artifacts.
It is not therapy, diagnosis, suicide-risk assessment, crisis care, a medical
device, or evidence of real-world safety.

Milestone 3 evaluates only frozen observable process signals. Exact phrase
matching is deliberately narrow and must not be used on real conversations or
described as understanding intent, mental state, treatment quality, or clinical
proficiency. Findings describe artifact behavior only.

The process evaluator does not implement a safety detector, crisis router,
resource selection, medication advice, a clinical screening instrument, a
complete safety plan, automatic third-party contact, or a risk score. Those
capabilities are not implied by typed safety evidence already present in domain
fixtures.

Scenario text remains untrusted data. Evaluators inspect validated strings and
markers but never execute their contents. Policy and artifact inputs are local;
the evaluator has no model, provider, network, UI, gold-label, or wall-clock
dependency.
