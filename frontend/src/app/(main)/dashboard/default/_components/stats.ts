"use client";

import * as React from "react";

import { useRouter, useSearchParams } from "next/navigation";

import { toast } from "sonner";

export type Stats = {
  total_sites: number;
  online_sites: number;
  offline_sites: number;
  manual_sites: number;
  // C60/V63: every network holding >=1 site (never a zero-site one), each
  // carrying its id so a row can drill into /sites?network=<id>.
  top_networks: Array<{ id: number; name: string; sites: number }>;
  // T57/C51: provider rows are DISTINCT-site counts; "Tanpa Link" is the
  // full-role-set complement, so it partitions `total_sites` exactly.
  provider_breakdown: Array<{ provider: string; count: number }>;
  // C58/V61: distinct-site counts per SDWAN package over the ACTIVE scope, so
  // the slices partition `online_sites` exactly.
  sdwan_breakdown: Array<{ package: string; count: number }>;
  // C65/V69: one row per group the VIEWER's org owns, never narrowed by the
  // selection — this array feeds the picker itself (T69).
  group_aggregates?: Array<{
    network_group: string;
    total_sites: number;
    baa_sites: number;
    invoice_sites: number;
    dismantle_sites: number;
  }>;
};

// C65/V70: the URL is the single source — every card and the picker read the
// same `?group=` list, so no two components can disagree.
export function useSelectedGroups(): string[] {
  const params = useSearchParams();
  const key = params.getAll("group").join("\u0000");
  return React.useMemo(() => (key ? key.split("\u0000") : []), [key]);
}

export function useGroupCommit() {
  const router = useRouter();
  const params = useSearchParams();

  return React.useCallback(
    (next: string[]) => {
      const sp = new URLSearchParams(params.toString());
      sp.delete("group");
      for (const g of next) sp.append("group", g);
      // V70: replace, not push — toggling a checkbox is not a navigation step.
      router.replace(sp.size ? `?${sp.toString()}` : "?", { scroll: false });
    },
    [router, params],
  );
}

// T69: keyed by URL, so the five consumers mounting together still share one
// request, and a selection change can never be served the previous payload.
const inflight = new Map<string, Promise<Stats>>();

function fetchStats(groups: string[]): Promise<Stats> {
  const q = new URLSearchParams();
  for (const g of groups) q.append("group", g);
  const url = `/api/backend/members/sites/stats${q.size ? `?${q.toString()}` : ""}`;
  let pending = inflight.get(url);
  if (!pending) {
    pending = fetch(url, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error("Gagal memuat statistik situs.");
        return (await res.json()) as Stats;
      })
      .finally(() => {
        inflight.delete(url);
      });
    inflight.set(url, pending);
  }
  return pending;
}

export function useStats(): Stats | null {
  const groups = useSelectedGroups();
  const key = groups.join("\u0000");
  const [stats, setStats] = React.useState<Stats | null>(null);

  React.useEffect(() => {
    let live = true;
    setStats(null);
    void fetchStats(key ? key.split("\u0000") : [])
      .then((s) => {
        if (live) setStats(s);
      })
      .catch((e) => toast.error((e as Error).message));
    return () => {
      live = false;
    };
  }, [key]);

  return stats;
}
