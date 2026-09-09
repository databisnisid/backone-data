"use client";

import * as React from "react";

import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import type { Page, SiteRow } from "../../sites/_components/data";

async function fetchQuota(kind: "dpi" | "starlink") {
  const res = await fetch(`/api/backend/quota/${kind}`);
  const body = (await res.json()) as Page<SiteRow> | { detail?: string };
  if (!res.ok) throw new Error((body as { detail?: string }).detail ?? "Fetch failed");
  return (body as Page<SiteRow>).results;
}

function QuotaTable({ rows }: { rows: SiteRow[] }) {
  if (!rows.length) {
    return <div className="text-muted-foreground p-4 text-sm">Tidak ada data.</div>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Site</TableHead>
          <TableHead>Service</TableHead>
          <TableHead>Quota String</TableHead>
          <TableHead>Network</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r) => (
          <TableRow key={r.id}>
            <TableCell>
              <div className="font-medium">{r.name ?? r.member_id}</div>
              <div className="text-muted-foreground text-xs">{r.member_id}</div>
            </TableCell>
            <TableCell>{r.service_line ?? "-"}</TableCell>
            <TableCell>
              <code className="text-xs">{r.quota_string ?? "-"}</code>
            </TableCell>
            <TableCell>{r.network_name ?? r.network_group ?? "-"}</TableCell>
            <TableCell>
              <Badge variant={r.is_online ? "default" : "secondary"}>{r.is_online ? "Online" : "Offline"}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function QuotaView() {
  const [dpi, setDpi] = React.useState<SiteRow[]>([]);
  const [starlink, setStarlink] = React.useState<SiteRow[]>([]);
  const [tab, setTab] = React.useState("dpi");

  React.useEffect(() => {
    void fetchQuota("dpi")
      .then(setDpi)
      .catch((e) => toast.error(e.message));
    void fetchQuota("starlink")
      .then(setStarlink)
      .catch((e) => toast.error(e.message));
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quota</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="dpi">Siab GSM (DPI)</TabsTrigger>
            <TabsTrigger value="starlink">Starlink</TabsTrigger>
          </TabsList>
          <TabsContent value="dpi">
            <QuotaTable rows={dpi} />
          </TabsContent>
          <TabsContent value="starlink">
            <QuotaTable rows={starlink} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
