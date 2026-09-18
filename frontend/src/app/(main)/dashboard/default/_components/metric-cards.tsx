"use client";

import { useState } from "react";

import { ChevronDown, Globe, HardDrive, Wifi, WifiOff } from "lucide-react";
import { useRouter } from "next/navigation";
import { Cell, Pie, PieChart } from "recharts";


import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

import { type Stats, useStats } from "./stats";

export function MetricCards() {
  const stats = useStats();

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

// C60: 10 rows on load; the rest hide behind the trigger below.
const TOP_NETWORKS_VISIBLE = 10;

export function TopNetworks() {
  const stats = useStats();
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const nets = stats?.top_networks ?? [];
  const hidden = nets.slice(TOP_NETWORKS_VISIBLE);

  const row = (n: Stats["top_networks"][number]) => {
    // V63: bars are shares of the TOTAL site count, so a sub-1% network would
    // paint a zero-width bar and read "(0%)" — 7 of prod's 21 rows do. Keep the
    // label honest and floor only the bar.
    const exact = stats?.total_sites ? (n.sites / stats.total_sites) * 100 : 0;
    const rounded = Math.round(exact);
    const label = rounded === 0 && exact > 0 ? "<1" : String(rounded);
    return (
      <button
        key={n.id}
        type="button"
        onClick={() => router.push(`/sites?network=${n.id}`)}
        className="block w-full space-y-1 text-left"
      >
        <div className="flex items-center justify-between gap-2 text-sm">
          <span className="truncate font-medium hover:underline">{n.name}</span>
          <span className="text-muted-foreground shrink-0 tabular-nums">
            {n.sites.toLocaleString("id-ID")} ({label}%)
          </span>
        </div>
        <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
          <div
            className="bg-primary h-full rounded-full"
            style={{ width: `${label === "<1" ? 1 : rounded}%` }}
          />
        </div>
      </button>
    );
  };

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
        {stats && (
          // C60: the trigger count comes from the array, never a literal — an
          // org-scoped viewer sees fewer than the superuser's 21.
          <Collapsible open={open} onOpenChange={setOpen} className="space-y-3">
            {nets.slice(0, TOP_NETWORKS_VISIBLE).map(row)}
            {hidden.length > 0 && (
              <>
                <CollapsibleContent className="space-y-3">
                  {hidden.map(row)}
                </CollapsibleContent>
                <CollapsibleTrigger className="text-muted-foreground hover:text-foreground flex w-full items-center justify-center gap-1 text-sm font-medium">
                  {open
                    ? "Tampilkan lebih sedikit"
                    : `${hidden.length} jaringan lainnya`}
                  <ChevronDown
                    aria-hidden
                    className={`size-4 transition-transform ${open ? "rotate-180" : ""}`}
                  />
                </CollapsibleTrigger>
              </>
            )}
          </Collapsible>
        )}
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
  const stats = useStats();

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

// C58: package names are not sensitive (External already reads every one of
// them per-row in the grid's `layanan` column), so unlike the provider panel
// this card is NOT behind the C43/C49 internal-only gate.
export function SdwanBreakdown() {
  const router = useRouter();
  const stats = useStats();

  const rows = stats?.sdwan_breakdown ?? [];
  // V61: every site carries exactly one package (single-valued FK, NULLs
  // backfilled by C59), so the slices partition the active set exactly.
  const total = rows.reduce((sum, r) => sum + r.count, 0);
  const data = rows.map((r, i) => ({
    ...r,
    fill: `var(--chart-${(i % 5) + 1})`,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Paket SDWAN</CardTitle>
        <CardDescription>Paket layanan per titik aktif</CardDescription>
      </CardHeader>
      <CardContent>
        {!stats && <p className="text-muted-foreground text-sm">Loading…</p>}
        {stats && rows.length === 0 && (
          <p className="text-muted-foreground text-sm">Tidak ada data paket.</p>
        )}
        {rows.length > 0 && (
          <>
            <ChartContainer
              config={{}}
              className="mx-auto aspect-square max-h-56 w-full"
            >
              <PieChart>
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      nameKey="package"
                      hideLabel
                      formatter={(value, name) => (
                        <span className="flex w-full items-center justify-between gap-4">
                          <span className="truncate">{name}</span>
                          <span className="text-muted-foreground tabular-nums">
                            {Number(value).toLocaleString("id-ID")} (
                            {share(Number(value), total).toLocaleString("id-ID", {
                              maximumFractionDigits: 1,
                            })}
                            %)
                          </span>
                        </span>
                      )}
                    />
                  }
                />
                {/* C58: minAngle keeps a sub-1% package a visible wedge; the
                    legend and tooltip print the true count and share so the
                    inflation is disclosed rather than hidden. */}
                <Pie
                  data={data}
                  dataKey="count"
                  nameKey="package"
                  minAngle={4}
                  onClick={(_, index) => {
                    const name = data[index]?.package;
                    if (name) {
                      router.push(
                        `/sites?sdwan=${encodeURIComponent(name)}&status=active`,
                      );
                    }
                  }}
                >
                  {data.map((d) => (
                    <Cell key={d.package} fill={d.fill} className="cursor-pointer" />
                  ))}
                </Pie>
              </PieChart>
            </ChartContainer>
            <ul className="mt-2 space-y-1">
              {data.map((d) => (
                <li key={d.package}>
                  <button
                    type="button"
                    onClick={() =>
                      router.push(
                        `/sites?sdwan=${encodeURIComponent(d.package)}&status=active`,
                      )
                    }
                    className="flex w-full items-center justify-between gap-2 text-left text-sm hover:underline"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <span
                        aria-hidden
                        className="size-2.5 shrink-0 rounded-xs"
                        style={{ background: d.fill }}
                      />
                      <span className="truncate font-medium">{d.package}</span>
                    </span>
                    <span className="text-muted-foreground shrink-0 tabular-nums">
                      {d.count.toLocaleString("id-ID")} (
                      {share(d.count, total).toLocaleString("id-ID", {
                        maximumFractionDigits: 1,
                      })}
                      %)
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
        {stats && rows.length > 0 && (
          <Badge variant="secondary" className="mt-2">
            {total.toLocaleString("id-ID")} titik berpaket
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}

function share(count: number, total: number): number {
  return total ? (count / total) * 100 : 0;
}