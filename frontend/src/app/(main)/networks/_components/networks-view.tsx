"use client";

import * as React from "react";

import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type SiteOption = { id: number; name: string; network_name: string | null };
type Network = { id: number; name: string; network_id: string; network_group: number | null };
type NetworkGroup = {
  id: number;
  name: string;
  sites: number;
  member_sites: number[];
  member_sites_detail: SiteOption[];
};
type Org = { id: number; name: string; networks: number[]; is_no_org: boolean };

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let message = "Terjadi kesalahan";
    try {
      const j = (await res.json()) as { detail?: string };
      if (j.detail) message = j.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(message);
  }
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const body = (await res.json()) as { results?: T; detail?: string };
  if (!res.ok) throw new Error((body as { detail?: string }).detail ?? "Fetch failed");
  if (body.results) return body.results as T;
  return body as T;
}

export function NetworksView({ isSuperuser }: { isSuperuser: boolean }) {
  const [networks, setNetworks] = React.useState<Network[]>([]);
  const [groups, setGroups] = React.useState<NetworkGroup[]>([]);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const [nets, grps] = await Promise.all([
        get<Network[]>("/api/backend/networks"),
        get<NetworkGroup[]>("/api/backend/networks/groups"),
      ]);
      setNetworks(nets);
      setGroups(grps);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }, []);
  // Fetch data on mount.
  React.useEffect(() => { void load(); }, [load]);

  const groupName = (id: number | null) => groups.find((g) => g.id === id)?.name ?? "Ungroup";
  // --- group CRUD ---
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<NetworkGroup | null>(null);
  const [name, setName] = React.useState("");
  const [selected, setSelected] = React.useState<Set<number>>(new Set());
  const [memberSites, setMemberSites] = React.useState<Set<number>>(new Set());
  const [siteQuery, setSiteQuery] = React.useState("");
  const [siteOptions, setSiteOptions] = React.useState<SiteOption[]>([]);
  const [deleteTarget, setDeleteTarget] = React.useState<NetworkGroup | null>(null);

  // Build network IDs query string for site picker.
  const netsParam = React.useMemo(
    () => [...selected].map((id) => `network=${id}`).join("&"),
    [selected],
  );

  // Auto-load first 50 sites from selected networks when selection changes.
  React.useEffect(() => {
    setSiteOptions([]);
    setSiteQuery("");
    if (!selected.size) return;
    const t = setTimeout(() => {
      void get<SiteOption[]>(`/api/backend/members/sites?${netsParam}`)
        .then(setSiteOptions)
        .catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [netsParam, selected.size]);

  // Debounced search filtered by selected networks.
  React.useEffect(() => {
    const q = siteQuery.trim();
    if (!q || !selected.size) return;
    const t = setTimeout(() => {
      void get<SiteOption[]>(`/api/backend/members/sites?search=${encodeURIComponent(q)}&${netsParam}`)
        .then(setSiteOptions)
        .catch((e) => toast.error((e as Error).message));
    }, 350);
    return () => clearTimeout(t);
  }, [siteQuery, netsParam, selected.size]);

  const openCreate = () => {
    setEditing(null);
    setName("");
    setSelected(new Set());
    setMemberSites(new Set());
    setSiteQuery("");
    setSiteOptions([]);
    setDialogOpen(true);
  };

  const openEdit = (g: NetworkGroup) => {
    setEditing(g);
    setName(g.name);
    setSelected(new Set(networks.filter((n) => n.network_group === g.id).map((n) => n.id)));
    setMemberSites(new Set(g.member_sites ?? []));
    setSiteQuery("");
    setSiteOptions([]);
    setDialogOpen(true);
  };

  const toggleNetwork = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSite = (id: number) => {
    setMemberSites((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };


  const save = async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      toast.error("Nama group wajib diisi.");
      return;
    }
    setBusy(true);
    try {
      const payload = { name: trimmed, member_sites: [...memberSites] };
      let groupId: number;
      if (editing) {
        groupId = editing.id;
        await request("PATCH", `/api/backend/networks/groups/${editing.id}/`, payload);
      } else {
        const created = await request<NetworkGroup>("POST", "/api/backend/networks/groups/", payload);
        groupId = created.id;
      }
      // Assign/unassign networks: diff current memberships against the selection.
      const current = new Set(networks.filter((n) => n.network_group === groupId).map((n) => n.id));
      const toAdd = [...selected].filter((id) => !current.has(id));
      const toRemove = [...current].filter((id) => !selected.has(id));
      await Promise.all([
        ...toAdd.map((id) => request("PATCH", `/api/backend/networks/${id}/`, { network_group: groupId })),
        ...toRemove.map((id) => request("PATCH", `/api/backend/networks/${id}/`, { network_group: null })),
      ]);
      toast.success(editing ? "Network Group diperbarui" : "Network Group ditambahkan");
      setDialogOpen(false);
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setBusy(true);
    try {
      await request("DELETE", `/api/backend/networks/groups/${deleteTarget.id}/`);
      toast.success("Network Group dihapus");
      setDialogOpen(false);
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
      setDeleteTarget(null);
    }
  };


  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Network Groups</CardTitle>
          {isSuperuser && (
            <Button size="sm" onClick={openCreate} disabled={busy}>
              + Tambah Group
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nama Group</TableHead>
                <TableHead>Jumlah Situs</TableHead>
                {isSuperuser && <TableHead className="text-right">Aksi</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {groups.length === 0 && (
                <TableRow>
                  <TableCell colSpan={isSuperuser ? 3 : 2} className="text-muted-foreground h-16 text-center">
                    Belum ada grup.
                  </TableCell>
                </TableRow>
              )}
              {groups.map((g) => (
                <TableRow key={g.id}>
                  <TableCell className="font-medium">{g.name}</TableCell>
                  <TableCell>{g.sites}</TableCell>
                  {isSuperuser && (
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(g)} disabled={busy}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(g)}
                        disabled={busy}
                        className="text-destructive hover:text-destructive"
                      >
                        Hapus
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Networks</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Network ID</TableHead>
                <TableHead>Group</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {networks.length === 0 && (
                <TableRow>
                  <TableCell className="text-muted-foreground h-16 text-center" colSpan={3}>
                    Tidak ada data.
                  </TableCell>
                </TableRow>
              )}
              {networks.map((n) => (
                <TableRow key={n.id}>
                  <TableCell className="font-medium">{n.name}</TableCell>
                  <TableCell>
                    <code className="text-xs">{n.network_id}</code>
                  </TableCell>
                  <TableCell>{groupName(n.network_group)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <OrganizationsView />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Network Group" : "Tambah Network Group"}</DialogTitle>
            <DialogDescription>
              Pilih network yang menjadi anggota grup. Situs yang terhubung ke network otomatis mengikuti grup.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="group-name">Nama Group</Label>
              <Input
                id="group-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Contoh: Regional Jawa"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Network Anggota</Label>
              <div className="max-h-56 overflow-y-auto rounded-md border p-2">
                {networks.length === 0 && (
                  <p className="text-muted-foreground text-sm">Tidak ada network.</p>
                )}
                {networks.map((n) => (
                  <label key={n.id} className="flex items-center gap-2 py-1">
                    <Checkbox checked={selected.has(n.id)} onCheckedChange={() => toggleNetwork(n.id)} />
                    <span className="text-sm">{n.name}</span>
                    <code className="text-xs text-muted-foreground">{n.network_id}</code>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Member Sites (opsional)</Label>
              <p className="text-muted-foreground text-sm">
                Pilih situs secara langsung sebagai anggota grup dari network yang dipilih.
              </p>
              <Input
                value={siteQuery}
                onChange={(e) => setSiteQuery(e.target.value)}
                placeholder={selected.size ? "Cari situs…" : "Pilih network terlebih dahulu…"}
                disabled={!selected.size}
              />
              <div className="max-h-40 overflow-y-auto rounded-md border p-2">
                {!selected.size && (
                  <p className="text-muted-foreground text-sm">
                    Centang network di atas terlebih dahulu untuk melihat daftar situs.
                  </p>
                )}
                {selected.size > 0 && !siteQuery.trim() && siteOptions.length === 0 && (
                  <p className="text-muted-foreground text-sm">Memuat…</p>
                )}
                {selected.size > 0 && !siteQuery.trim() && siteOptions.length > 0 && (
                  <p className="text-muted-foreground text-sm">
                    {siteOptions.length} situs ditampilkan. Ketik untuk mencari lebih banyak.
                  </p>
                )}
                {siteQuery.trim() && siteOptions.length === 0 && (
                  <p className="text-muted-foreground text-sm">Tidak ada hasil.</p>
                )}
                {siteOptions.map((s) => (
                  <label key={s.id} className="flex items-center gap-2 py-1">
                    <Checkbox checked={memberSites.has(s.id)} onCheckedChange={() => toggleSite(s.id)} />
                    <span className="text-sm">{s.name}</span>
                    {s.network_name && (
                      <span className="text-xs text-muted-foreground">({s.network_name})</span>
                    )}
                  </label>
                ))}
              </div>
              {memberSites.size > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {(editing?.member_sites_detail ?? siteOptions)
                    .filter((s) => memberSites.has(s.id))
                    .map((s) => (
                      <span
                        key={s.id}
                        className="bg-muted text-muted-foreground inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs"
                      >
                        {s.name}
                      </span>
                    ))}
                </div>
              )}
            </div>
            {editing && (
              <p className="text-muted-foreground text-sm">
                Jumlah situs di grup ini: <span className="font-medium">{editing.sites}</span>
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)} disabled={busy}>
              Batal
            </Button>
            <Button onClick={() => void save()} disabled={busy}>
              Simpan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus Network Group?</AlertDialogTitle>
            <AlertDialogDescription>
              Network di grup ini akan menjadi &ldquo;Ungroup&rdquo; (network_group dikosongkan). Situs tidak akan ikut
              terhapus.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={busy}>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={() => void confirmDelete()} disabled={busy}>
              Hapus
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export function OrganizationsView() {
  const [orgs, setOrgs] = React.useState<Org[]>([]);

  React.useEffect(() => {
    void get<Org[]>("/api/backend/organizations")
      .then(setOrgs)
      .catch((e) => toast.error(e.message));
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Organizations</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Networks</TableHead>
              <TableHead>No Org</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orgs.length === 0 && (
              <TableRow>
                <TableCell className="text-muted-foreground h-16 text-center" colSpan={3}>
                  Tidak ada data.
                </TableCell>
              </TableRow>
            )}
            {orgs.map((o) => (
              <TableRow key={o.id}>
                <TableCell className="font-medium">{o.name}</TableCell>
                <TableCell>{o.networks.length}</TableCell>
                <TableCell>{o.is_no_org ? "Ya" : "-"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
