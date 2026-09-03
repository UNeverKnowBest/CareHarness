import Link from "next/link";
import { localeCopy } from "../lib/copy";

export function RoleShell({
  locale,
  role,
  children,
}: {
  locale: string;
  role: "participant" | "reviewer" | "admin";
  children: React.ReactNode;
}) {
  const text = localeCopy(locale);
  return (
    <main>
      <header className="topbar">
        <Link className="brand" href={`/${locale}/participant`}>
          <span className="brand-mark">CL</span>
          <span>CareLoop <small>Research Console</small></span>
        </Link>
        <nav aria-label="Research roles">
          {(["participant", "reviewer", "admin"] as const).map((item) => (
            <Link className={item === role ? "active" : ""} href={`/${locale}/${item}`} key={item}>
              {text[item]}
            </Link>
          ))}
        </nav>
        <Link className="locale" href={`/${locale === "zh-CN" ? "en" : "zh-CN"}/${role}`}>
          {locale === "zh-CN" ? "EN" : "中文"}
        </Link>
      </header>
      <section className="boundary" aria-label="Research limitation">
        <strong>{text.boundary}</strong><span>{text.notice}</span>
      </section>
      {children}
    </main>
  );
}
