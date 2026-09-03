import { RoleShell } from "../../../components/RoleShell";

const plugins = [
  ["model-provider.demo", "Model provider", "LOCKED"],
  ["input-safety.v1", "Input safety", "LOCKED"],
  ["output-guard.v1", "Output guard", "LOCKED"],
  ["resource-catalog.v1", "Resource catalog", "LOCKED"],
  ["display.timeline", "Timeline display", "OPTIONAL"],
];

export default async function AdminPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return (
    <RoleShell locale={locale} role="admin">
      <section className="workspace">
        <div className="page-heading"><p className="kicker">NEXT-SESSION PROFILE</p><h1>Capabilities stay bounded.</h1><p>Critical plugins are immutable. Optional changes create a new profile and never hot-swap an active session.</p></div>
        <div className="plugin-list">{plugins.map(([id, name, state]) => <article key={id}><div className="plugin-icon">{name[0]}</div><div><h2>{name}</h2><code>{id}</code></div><span className={state === "LOCKED" ? "pill" : "pill optional"}>{state}</span><button disabled={state === "LOCKED"}>{state === "LOCKED" ? "Required" : "Configure"}</button></article>)}</div>
      </section>
    </RoleShell>
  );
}
