import { redirect } from "next/navigation";

import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import { OrganizationsView } from "../networks/_components/networks-view";

export default async function OrganizationsPage() {
  // T49/V51: External / External Network have no Pengaturan page.
  const { isSuperuser, groups } = await getMeAccess();
  if (!isSuperuser && isExternalNavHidden(groups)) {
    redirect("/dashboard/default");
  }

  return <OrganizationsView />;
}
