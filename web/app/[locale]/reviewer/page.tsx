import { RoleShell } from "../../../components/RoleShell";

export default async function ReviewerPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return (
    <RoleShell locale={locale} role="reviewer">
      <section className="workspace">
        <div className="page-heading"><p className="kicker">SIMULATED REVIEW · REVISION CONTROLLED</p><h1>Evidence before action.</h1><p>Claim pending synthetic drafts, inspect linked findings, and append one auditable decision.</p></div>
        <div className="review-grid">
          <article className="metric"><span>Pending</span><strong>2</strong><small>descriptive count</small></article>
          <article className="metric"><span>Claimed</span><strong>1</strong><small>descriptive count</small></article>
          <article className="metric"><span>Resolved</span><strong>8</strong><small>descriptive count</small></article>
          <article className="queue-card"><div><span className="pill">PENDING · REV 0</span><h2>zh-safe-repair-02</h2><p>Final complete response remains quarantined.</p></div><button>Claim simulated review</button></article>
          <article className="queue-card"><div><span className="pill amber">TARGET PASSED</span><h2>en-output-hold-04</h2><p>Two bounded repair attempts are recorded.</p></div><button>Inspect evidence</button></article>
        </div>
      </section>
    </RoleShell>
  );
}
