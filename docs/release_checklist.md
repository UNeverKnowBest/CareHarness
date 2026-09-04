# Research Release Checklist

This release checklist closes the approved M1–M17 research harness. It is not a
production, clinical, regulatory, privacy, or emergency-readiness approval.

## Repository evidence

- [ ] Worktree changes are reviewed and limited to the approved milestone.
- [ ] Python 3.12 is used and `uv lock --check` passes.
- [ ] Ruff format/lint, mypy, and the complete pytest suite pass from the lock.
- [ ] The P1–P8 benchmark regenerates and its tracked artifacts are unchanged.
- [ ] The Milestone 2 fixture generator `--check` passes.
- [ ] The M17 evidence generator `--check` passes and its raw/Markdown files are
      generated rather than hand-edited.
- [ ] Web `npm ci`, typecheck, production build, and Playwright smoke pass when
      the locked browser/runtime are available.
- [ ] Compose parses; image/runtime claims are made only if the daemon and live
      services were actually exercised.

## Safety and audience

- [ ] Every scenario is adult synthetic role-play and contains no real-person or
      protected health information.
- [ ] The UI and reports state that this is not therapy, diagnosis, screening,
      crisis care, an emergency service, or a medical device.
- [ ] The simulated human-review queue is described as unstaffed and as
      contacting no clinician, emergency service, family, authority, or third
      party.
- [ ] No score, probability, diagnosis, `risk_cleared`, clinical-validity,
      treatment-effectiveness, crisis-detection, regulatory, or real-world
      safety claim appears in release materials.
- [ ] Challenge, held, override, and system-failure cases release zero ordinary
      responses to the participant projection.

## Cloud template (not a deployment approval)

- [ ] The project, region, cost owner, data-retention owner, rollback owner, and
      disposable research purpose are recorded.
- [ ] Terraform/gcloud versions, provider initialization, format, validate,
      plan, and policy scan results are recorded; unavailable checks are marked
      not run.
- [ ] State is remote, encrypted, access-controlled, versioned, and excluded
      from source control. No secret is supplied as an ordinary Terraform value.
- [ ] Images are digest-pinned and scanned. Cloud Run has no unintended public
      invoker; production disables local synthetic identity.
- [ ] OIDC issuer/audience/key rotation, least-privilege IAM, TLS, private
      connectivity, backups, PITR, retention purge, and audit logging are
      independently reviewed.
- [ ] Redis-loss and new-instance Cloud SQL restore exercises follow
      `docs/gcp_recovery_runbook.md`; no automatic production promotion occurs.

## Demonstration release

- [ ] The recording uses only fixed synthetic prompts, hides notifications and
      credentials, and does not show `.env`, Terraform state, tokens, or raw
      quarantined drafts.
- [ ] The opening and closing frames show the research-only/non-clinical limits.
- [ ] The demo shows one allowed case and one override/hold with no ordinary
      response, then links the behavior to raw evidence rather than claiming
      real-world performance.
- [ ] Exact commands, exits, important counts, warnings, and unrun environment
      checks are copied to `STATUS.md` before declaring the milestone complete.
