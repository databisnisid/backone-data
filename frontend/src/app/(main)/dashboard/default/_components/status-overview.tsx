"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { useStats } from "./stats";

export function StatusOverview() {
  const stats = useStats();

  if (!stats) {
    return (
      <Card className="@container/card">
        <CardHeader>
          <CardTitle>Ringkasan Situs</CardTitle>
          <CardDescription>Loading…</CardDescription>
        </CardHeader>
        <CardContent className="h-20 animate-pulse rounded-md bg-muted/50" />
      </Card>
    );
  }

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Ringkasan Situs</CardTitle>
        <CardDescription>Status jaringan saat ini</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground text-sm">Online</span>
            <span className="font-medium text-2xl tabular-nums text-emerald-600 dark:text-emerald-400">
              {stats.online_sites.toLocaleString("id-ID")}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground text-sm">Offline</span>
            <span className="font-medium text-2xl tabular-nums text-red-600 dark:text-red-400">
              {stats.offline_sites.toLocaleString("id-ID")}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <span className="text-muted-foreground text-sm">Tingkat ketersediaan</span>
          <Badge variant={stats.online_sites > 0 ? "default" : "secondary"} className="tabular-nums">
            {stats.total_sites ? `${Math.round((stats.online_sites / stats.total_sites) * 100)}%` : "-"}
          </Badge>
        </div>

        <div className="bg-muted flex h-3 w-full overflow-hidden rounded-full">
          <div
            className="bg-primary h-full transition-all"
            style={{
              width: stats.total_sites
                ? `${(stats.online_sites / stats.total_sites) * 100}%`
                : "0%",
            }}
          />
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-muted-foreground text-sm">Ringkasan per grup</span>
        </div>
        <div className="space-y-2">
          {(stats.group_aggregates ?? []).length > 0 ? (
            stats.group_aggregates?.map((g) => (
              <div
                key={g.network_group}
                className="flex items-center justify-between gap-2 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{g.network_group}</div>
                  <div className="text-muted-foreground text-xs">
                    {g.total_sites} situs · BAA {g.baa_sites} · Invoice {g.invoice_sites}
                  </div>
                </div>
                {g.dismantle_sites > 0 && (
                  <Badge variant="destructive" className="shrink-0 tabular-nums">
                    {g.dismantle_sites} dismantle
                  </Badge>
                )}
              </div>
            ))
          ) : (
            <p className="text-muted-foreground text-sm">Tidak ada grup jaringan.</p>
          )}
        </div>

        <p className="text-muted-foreground text-sm">
          {stats.online_sites.toLocaleString("id-ID")} dari{" "}
          {stats.total_sites.toLocaleString("id-ID")} situs aktif, {stats.manual_sites.toLocaleString("id-ID")}{" "}
          situs diinput manual.
        </p>
      </CardContent>
    </Card>
  );
}
