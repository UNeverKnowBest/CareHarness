import { ParticipantConsole } from "../../../components/ParticipantConsole";
import { RoleShell } from "../../../components/RoleShell";

export default async function ParticipantPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <RoleShell locale={locale} role="participant"><ParticipantConsole locale={locale} /></RoleShell>;
}
