import { redirect } from "next/navigation";

import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import { NetworksView } from "./_components/networks-view";

export default async function NetworksPage() {
  // V33: group management is superuser-only. Reads stay available to any authed user;
  // the flag only controls the group-edit controls the client renders.
  // T49/V51: External / External Network have no Networks page.
  const { isSuperuser, groups } = await getMeAccess();
  if (!isSuperuser && isExternalNavHidden(groups)) {
    redirect("/dashboard/default");
  }

  return <NetworksView isSuperuser={isSuperuser} />;
}
