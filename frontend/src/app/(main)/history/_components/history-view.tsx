"use client";

import * as React from "react";

import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { fetchHistory, type ChangeLogRow } from "../../sites/_components/api";

export function HistoryView() {
  const [rows, setRows] = React.useState<ChangeLogRow[]>([]);
  const [page, setPage] = React.useState(1);
  const [count, setCount] = React.useState(0);
  const [user, setUser] = React.useState("");
  const [action, setAction] = React.useState("all");
  const [from, setFrom] = React.useState("");
  const [to, setTo] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    setLoading(true);
    fetchHistory({
      page,
      user: user || undefined,
      action: action === "all" ? undefined : action,
      dateFrom: from || undefined,
      dateTo: to || undefined,
    })
      .then((p) => {
        setRows(p.results);
        setCount(p.count);
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [page, user, action, from, to]);

  const pages = Math.max(1, Math.ceil(count / 100));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Riwayat Perubahan</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end gap-2">
          <Input placeholder="Username" value={user} onChange={(e) => { setPage(1); setUser(e.target.value); }} className="w-40" />
          <Select value={action} onValueChange={(v) => { setPage(1); setAction(v); }}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Aksi" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua aksi</SelectItem>
              <SelectItem value="create">create</SelectItem>
              <SelectItem value="update">update</SelectItem>
              <SelectItem value="delete">delete</SelectItem>
              <SelectItem value="import">import</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" value={from} onChange={(e) => { setPage(1); setFrom(e.target.value); }} className="w-40" />
          <Input type="date" value={to} onChange={(e) => { setPage(1); setTo(e.target.value); }} className="w-40" />
        </div>

        {loading ? (
          <div className="text-muted-foreground p-4 text-sm">Memuat…</div>
        ) : rows.length === 0 ? (
          <div className="text-muted-foreground p-4 text-sm">Tidak ada data.</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Waktu</TableHead>
                <TableHead>Site</TableHead>
                <TableHead>Aksi</TableHead>
                <TableHead>Field</TableHead>
                <TableHead>Lama</TableHead>
                <TableHead>Baru</TableHead>
                <TableHead>Oleh</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="whitespace-nowrap text-xs">{new Date(r.created_at).toLocaleString("id-ID")}</TableCell>
                  <TableCell className="font-medium">{r.site}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{r.action}</Badge>
                  </TableCell>
                  <TableCell>{r.field}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{r.old_value ?? "-"}</TableCell>
                  <TableCell className="text-xs">{r.new_value ?? "-"}</TableCell>
                  <TableCell>{r.user ?? "sistem"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Sebelumnya
          </Button>
          <span className="text-muted-foreground text-xs">
            {page} / {pages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
            Berikutnya
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
