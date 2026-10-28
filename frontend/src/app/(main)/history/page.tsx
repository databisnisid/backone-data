import { redirect } from "next/navigation";

import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import { HistoryView } from "./_components/history-view";

export default async function HistoryPage() {
  // C79/V81: internal-only — External / External Network have no page (403 upstream).
  const { isSuperuser, groups } = await getMeAccess();
  if (!isSuperuser && isExternalNavHidden(groups)) {
    redirect("/dashboard/default");
  }

  return <HistoryView />;
}
