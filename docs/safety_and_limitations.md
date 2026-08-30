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
