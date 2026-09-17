"use client";

import { useState } from "react";

import { Globe, HardDrive, Wifi, WifiOff } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Stats = {
  total_sites: number;
  online_sites: number;
  offline_sites: number;
  manual_sites: number;
  top_networks: Array<{ name: string; sites: number }>;
  // T57/C51: provider rows are DISTINCT-site counts; "Tanpa Link" is the
  // full-role-set complement, so it partitions `total_sites` exactly.
  provider_breakdown: Array<{ provider: string; count: number }>;
};

let statsPromise: Promise<Stats> | null = null;

function fetchStats(): Promise<Stats> {
  statsPromise ??= fetch("/api/backend/members/sites/stats", { cache: "no-store" })
    .then(async (res) => {
      if (!res.ok) throw new Error("Gagal memuat statistik situs.");
      return (await res.json()) as Stats;
    })
    .finally(() => {
      statsPromise = null;
    });
  return statsPromise;
}

export function MetricCards() {
  const [stats, setStats] = useState<Stats | null>(null);

  useState(() => {
    void fetchStats()
      .then(setStats)
      .catch((e) => toast.error((e as Error).message));
  });

  if (!stats) {
    return (
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="bg-muted size-7 animate-pulse rounded-lg" />
              <div className="bg-muted h-4 w-24 animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="bg-muted h-8 w-20 animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      icon: Globe,
      label: "Total Situs",
      value: stats.total_sites.toLocaleString("id-ID"),
      hint: "Semua situs terdaftar",
    },
    {
      icon: Wifi,
      label: "Online",
      value: stats.online_sites.toLocaleString("id-ID"),
      hint: "Situs aktif saat ini",
    },
    {
      icon: WifiOff,
      label: "Offline",
      value: stats.offline_sites.toLocaleString("id-ID"),
      hint: "Situs tidak aktif",
    },
    {
      icon: HardDrive,
      label: "Manual",
      value: stats.manual_sites.toLocaleString("id-ID"),
      hint: "Situs input manual",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 *:data-[slot=card]:bg-linear-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs xl:grid-cols-4 dark:*:data-[slot=card]:bg-card">
      {cards.map(({ icon: Icon, label, value, hint }) => (
        <Card key={label}>
          <CardHeader>
            <CardTitle>
              <div className="flex size-7 items-center justify-center rounded-lg border bg-muted text-muted-foreground">
                <Icon className="size-4" />
              </div>
            </CardTitle>
            <CardDescription>{label}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <div className="font-medium text-3xl tabular-nums leading-none tracking-tight">{value}</div>
            </div>
            <p className="text-muted-foreground text-sm">{hint}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function TopNetworks() {
  const [stats, setStats] = useState<Stats | null>(null);

  useState(() => {
    void fetchStats()
      .then(setStats)
      .catch((e) => toast.error((e as Error).message));
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Networks</CardTitle>
        <CardDescription>Jaringan dengan situs terbanyak</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!stats && <p className="text-muted-foreground text-sm">Loading…</p>}
        {stats?.top_networks.length === 0 && (
          <p className="text-muted-foreground text-sm">Tidak ada data jaringan.</p>
        )}
        {stats?.top_networks.map((n) => {
          const pct = stats.total_sites ? Math.round((n.sites / stats.total_sites) * 100) : 0;
          return (
            <div key={n.name} className="space-y-1">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate font-medium">{n.name}</span>
                <span className="text-muted-foreground tabular-nums">
                  {n.sites.toLocaleString("id-ID")} ({pct}%)
                </span>
              </div>
              <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
                <div className="bg-primary h-full rounded-full" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
        {stats && (
          <Badge variant="secondary" className="mt-2">
            {stats.total_sites.toLocaleString("id-ID")} situs total
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}

export function ProviderBreakdown() {
  const [stats, setStats] = useState<Stats | null>(null);

  useState(() => {
    void fetchStats()
      .then(setStats)
      .catch((e) => toast.error((e as Error).message));
  });

  // C46: bars scale to the summed displayed rows, so they total 100% and the
  // small real providers stay legible next to the dominant "Tanpa Link" row.
  const rows = stats?.provider_breakdown ?? [];
  const shown = rows.reduce((sum, r) => sum + r.count, 0);
  // T57/V59: Tanpa Link complements the full role set, so this is the DISTINCT
  // site count — summing the provider rows would double-count a site holding
  // two providers (site 3705 read "2 titik berprovider" for one site).
  const noLink = rows.find((r) => r.provider === "Tanpa Link")?.count ?? 0;
  const totalLinks = stats ? stats.total_sites - noLink : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Provider</CardTitle>
        <CardDescription>Provider yang dipakai dan jumlah titik</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!stats && <p className="text-muted-foreground text-sm">Loading…</p>}
        {stats && rows.length === 0 && (
          <p className="text-muted-foreground text-sm">Tidak ada data provider.</p>
        )}
        {/* Server already orders providers desc and pins "Tanpa Link" last (C47). */}
        {rows.map((p) => {
          const share = shown ? (p.count / shown) * 100 : 0;
          // C46: one decimal, so a small real provider never rounds to a bare
          // "0%" (which reads as absent), and a nonzero bar keeps a floor of 1%
          // so it stays visible beside the dominant "Tanpa Link" row.
          const pct = share > 0 && share < 0.1 ? 0.1 : share;
          const barWidth = p.count > 0 ? Math.max(share, 1) : 0;
          return (
            <div key={p.provider} className="space-y-1">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate font-medium">{p.provider}</span>
                <span className="text-muted-foreground tabular-nums">
                  {p.count.toLocaleString("id-ID")} ({pct.toLocaleString("id-ID", { maximumFractionDigits: 1 })}%)
                </span>
              </div>
              <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
                <div className="bg-primary h-full rounded-full" style={{ width: `${barWidth}%` }} />
              </div>
            </div>
          );
        })}
        {stats && rows.length > 0 && (
          <Badge variant="secondary" className="mt-2">
            {totalLinks.toLocaleString("id-ID")} titik berprovider
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}