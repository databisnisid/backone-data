import { backendFetch } from "@/lib/auth";

import { NetworksView } from "./_components/networks-view";

async function getIsSuperuser() {
  try {
    const res = await backendFetch("/api/auth/me/");
    if (!res.ok) return false;
    const data = (await res.json()) as { is_superuser?: boolean };
    return data.is_superuser ?? false;
  } catch {
    return false;
  }
}

export default async function NetworksPage() {
  // V33: group management is superuser-only. Reads stay available to any authed user;
  // the flag only controls the group-edit controls the client renders.
  const isSuperuser = await getIsSuperuser();

  return <NetworksView isSuperuser={isSuperuser} />;
}
