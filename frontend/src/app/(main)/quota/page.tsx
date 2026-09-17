import { redirect } from "next/navigation";

import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import { QuotaView } from "./_components/quota-view";

export default async function QuotaPage() {
  // T49/V51: External / External Network have no Quota page.
  const { isSuperuser, groups } = await getMeAccess();
  if (!isSuperuser && isExternalNavHidden(groups)) {
    redirect("/dashboard/default");
  }

  return <QuotaView />;
}
