import { redirect } from "next/navigation";

import { backendFetch } from "@/lib/auth";

import { LookupsView } from "../_components/lookups-view";

async function getCurrentUser() {
  try {
    const res = await backendFetch("/api/auth/me/");
    if (!res.ok) return null;
    const data = (await res.json()) as { is_superuser?: boolean };
    return data.is_superuser ?? false;
  } catch {
    return false;
  }
}

export default async function LookupsPage() {
  // T40: superuser-only. Non-superuser (or unauthenticated) → dashboard.
  const isSuperuser = await getCurrentUser();
  if (!isSuperuser) {
    redirect("/dashboard/default");
  }

  return <LookupsView />;
}
