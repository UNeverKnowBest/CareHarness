export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!new Set(["en", "zh-CN"]).has(locale)) return null;
  return children;
}
