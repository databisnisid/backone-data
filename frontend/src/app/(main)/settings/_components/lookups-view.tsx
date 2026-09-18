"use client";

import * as React from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Lookup = { id: number; name: string };

const KINDS = [
  { kind: "sdwan", label: "SDWAN Package" },
  { kind: "baa", label: "BAA Status" },
  { kind: "role", label: "Link Role" },
  { kind: "provider", label: "Link Provider" },
] as const;

type Kind = (typeof KINDS)[number]["kind"];

const KIND_LABEL: Record<Kind, string> = {
  sdwan: "SDWAN",
  baa: "BAA",
  role: "Role",
  provider: "Provider",
};

async function listLookups(kind: Kind): Promise<Lookup[]> {
  const res = await fetch(`/api/backend/members/lookups/${kind}/`);
  if (!res.ok) throw new Error(`Fetch failed (${res.status})`);
  const body = (await res.json()) as { results?: Lookup[] };
  return body.results ?? [];
}

async function createLookup(kind: Kind, name: string): Promise<Lookup> {
  const res = await fetch(`/api/backend/members/lookups/${kind}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const body = (await res.json().catch(() => ({}))) as { detail?: string };
  if (!res.ok) throw new Error(body.detail ?? `Create failed (${res.status})`);
  return body as Lookup;
}

async function renameLookup(kind: Kind, id: number, name: string): Promise<Lookup> {
  const res = await fetch(`/api/backend/members/lookups/${kind}/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const body = (await res.json().catch(() => ({}))) as { detail?: string };
  if (!res.ok) throw new Error(body.detail ?? `Rename failed (${res.status})`);
  return body as Lookup;
}

function LookupSection({ kind, label }: { kind: Kind; label: string }) {
  const [items, setItems] = React.useState<Lookup[]>([]);
  const [newName, setNewName] = React.useState("");
  const [editing, setEditing] = React.useState<number | null>(null);
  const [editName, setEditName] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(() => {
    listLookups(kind)
      .then(setItems)
      .catch((e) => toast.error(e.message));
  }, [kind]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function add() {
    if (!newName.trim()) return;
    setBusy(true);
    try {
      await createLookup(kind, newName.trim());
      setNewName("");
      load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function save(id: number) {
    if (!editName.trim()) return;
    setBusy(true);
    try {
      await renameLookup(kind, id, editName.trim());
      setEditing(null);
      load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder={`New ${label} name`}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void add();
            }}
          />
          <Button onClick={() => void add()} disabled={busy || !newName.trim()}>
            Add
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead className="w-28">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) =>
              editing === item.id ? (
                <TableRow key={item.id}>
                  <TableCell>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") void save(item.id);
                        if (e.key === "Escape") setEditing(null);
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Button size="sm" onClick={() => void save(item.id)} disabled={busy}>
                      Save
                    </Button>
                  </TableCell>
                </TableRow>
              ) : (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditing(item.id);
                        setEditName(item.name);
                      }}
                    >
                      Rename
                    </Button>
                  </TableCell>
                </TableRow>
              ),
            )}
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={2} className="text-muted-foreground py-6 text-center">
                  No {label.toLowerCase()} yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export function LookupsView() {
  return (
    <div className="grid gap-6">
      {KINDS.map((k) => (
        <LookupSection key={k.kind} kind={k.kind} label={`${KIND_LABEL[k.kind]} — ${k.label}`} />
      ))}
    </div>
  );
}
