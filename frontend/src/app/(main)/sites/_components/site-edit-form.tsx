"use client";

import * as React from "react";

import { Link2, Pencil, Plus, Trash2, Upload, X } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import { createSiteLink, deleteSiteLink, fetchLinkServices, fetchMemberOptions, fetchSite, patchSiteLink, uploadSiteFile, type MemberOptions } from "./api";
import {
  isFinance,
  isPurchasing,
  isSales,
  isSupport,
  type Me,
  type SiteLink,
  type SiteRow,
} from "./data";



type ScalarDef = {
  name: string;
  label: string;
  kind: "text" | "select" | "textarea";
  choices?: string[];
};

function scalarDefsFor(me: Me, options: MemberOptions): ScalarDef[] {
  if (isSupport(me)) {
    return [
      { name: "name", label: "Nama Site", kind: "text" },
      { name: "address", label: "Alamat", kind: "text" },
      { name: "member_code", label: "Kode Situs", kind: "text" },
      { name: "project_number", label: "Project Number", kind: "text" },
      { name: "sdwan_package", label: "Paket Layanan (SDWAN)", kind: "select", choices: options.sdwan_package },
      { name: "baa_status_category", label: "Status BAA", kind: "select", choices: options.baa_status_category },
      { name: "notes", label: "Keterangan", kind: "textarea" },
    ];
  }
  if (isSales(me)) {
    return [
      { name: "baa_status_category", label: "Status BAA", kind: "select", choices: options.baa_status_category },
      { name: "notes", label: "Keterangan", kind: "textarea" },
    ];
  }
  if (isFinance(me)) {
    return [
      { name: "invoice_number", label: "No Invoice", kind: "text" },
      { name: "notes", label: "Keterangan", kind: "textarea" },
    ];
  }
  if (isPurchasing(me)) {
    return [{ name: "notes", label: "Keterangan", kind: "textarea" }];
  }
  return [];
}

function fileFieldsFor(me: Me): { field: string; label: string }[] {
  if (isSupport(me)) {
    return [
      { field: "upload_baa", label: "Upload BAA" },
      { field: "po_file_user", label: "PO dari User" },
      { field: "po_file_vendor", label: "PO ke Vendor" },
      { field: "invoice_file", label: "Upload Bukti Invoice" },
      { field: "bap_file", label: "BAP Dismantle" },
    ];
  }
  if (isSales(me)) return [{ field: "upload_baa", label: "Upload BAA (Sales)" }];
  if (isFinance(me)) return [{ field: "invoice_file", label: "Upload Bukti Invoice" }];
  if (isPurchasing(me)) return [{ field: "po_file_vendor", label: "Upload PO ke Vendor" }];
  return [];
}

function useLinkServices(me: Me): { id: number; name: string }[] {
  const [services, setServices] = React.useState<{ id: number; name: string }[]>([]);
  React.useEffect(() => {
    if (!isSales(me) && !isSupport(me)) return;
    fetchLinkServices()
      .then(setServices)
      .catch(() => setServices([]));
  }, [me]);
  return services;
}

function useMemberOptions(): MemberOptions {
  const [options, setOptions] = React.useState<MemberOptions>({
    sdwan_package: [],
    baa_status_category: [],
    role: [],
  });
  React.useEffect(() => {
    fetchMemberOptions()
      .then(setOptions)
      .catch(() => setOptions({ sdwan_package: [], baa_status_category: [], role: [] }));
  }, []);
  return options;
}

function serviceName(services: { id: number; name: string }[], id: number | null): string {
  if (id == null) return "";
  return services.find((s) => s.id === id)?.name ?? String(id);
}

export function SiteEditForm({
  me,
  row,
  onSave,
  onDone,
  onRowUpdate,
}: {
  me: Me;
  row: SiteRow;
  onSave: (id: number, payload: Record<string, unknown>) => void;
  onDone: () => void;
  onRowUpdate: (r: SiteRow) => void;
}) {
  const memberOptions = useMemberOptions();
  const scalarDefs = scalarDefsFor(me, memberOptions);
  const fileFields = fileFieldsFor(me);
  // Synced (upstream) sites: CORE_EDIT_FIELDS (mirrors members/rbac.py) are
  // rejected server-side, so render them disabled instead of letting superuser
  // hit a 400. Feature fields stay editable.
  const isSynced = !row.is_manual;
  const CORE_FIELD_NAMES = new Set([
    "name",
    "member_code",
    "member_id",
    "address",
    "location",
    "online_at",
    "offline_at",
    "service_line",
    "network",
    "links",
  ]);
  const coreReadOnly = (name: string) => isSynced && CORE_FIELD_NAMES.has(name);
  const [draft, setDraft] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(
      scalarDefs.map((d) => [d.name, (row as unknown as Record<string, string | null>)[d.name] ?? ""]),
    ),
  );
  const dirty = scalarDefs
    .filter((d) => !coreReadOnly(d.name))
    .filter((d) => (draft[d.name] ?? "") !== ((row as unknown as Record<string, string | null>)[d.name] ?? ""))
    .map((d) => d.name);


  const submit = () => {
    if (!dirty.length) {
      onDone();
      return;
    }
    const payload: Record<string, unknown> = {};
    for (const name of dirty) {
      const v = draft[name];
      payload[name] = v === "" ? null : v;
    }
    onSave(row.id, payload);
  };

  async function onFile(field: string, file: File | undefined) {
    if (!file) return;
    try {
      const updated = await uploadSiteFile(row.id, field, file);
      onRowUpdate(updated);
      toast.success(`${field} uploaded`);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  const services = useLinkServices(me);
  // Support/superuser and Sales may write member_links (V24 mirrors WRITE_BY_ROLE).
  const canEditLinks = isSupport(me) || isSales(me);
  const [newLink, setNewLink] = React.useState<Partial<SiteLink>>({
    role: "MAIN",
    service: null,
    provider: "",
    capacity: "",
    sid: "",
  });

  async function onLinkSave(link: Partial<SiteLink>) {
    try {
      if (link.id) {
        const payload: Record<string, unknown> = {
          role: link.role,
          service: link.service ?? null,
          provider: link.provider ?? null,
          capacity: link.capacity ?? null,
          sid: link.sid ?? null,
        };
        await patchSiteLink(link.id, payload);
      } else {
        await createSiteLink(row.id, link);
        setNewLink({ role: "MAIN", service: null, provider: "", capacity: "", sid: "" });
      }
      const updated = await fetchSite(row.id);
      onRowUpdate(updated);
      toast.success(link.id ? "Link diperbarui" : "Link ditambahkan");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  async function onLinkDelete(id: number) {
    try {
      await deleteSiteLink(id);
      const updated = await fetchSite(row.id);
      onRowUpdate(updated);
      toast.success("Link dihapus");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline">EDIT MODE ACTIVE</Badge>
          <span className="font-medium">{row.name}</span>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone}>
            <X className="size-4" /> Batal
          </Button>
          <Button size="sm" onClick={submit} disabled={!dirty.length}>
            <Pencil className="size-4" /> Simpan
          </Button>
        </div>
      </div>

      <FieldGroup className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {scalarDefs.map((def) => {
          const isDirty = dirty.includes(def.name);
          const readOnly = coreReadOnly(def.name);
          let control: React.ReactNode;
          if (def.kind === "select") {
            control = (
              <div className="flex flex-col gap-1.5">
                <FieldLabel htmlFor={`edit-${def.name}`}>{def.label}</FieldLabel>
                <Select
                  value={draft[def.name] || undefined}
                  disabled={readOnly}
                  onValueChange={(v) => setDraft((d) => ({ ...d, [def.name]: v }))}
                >
                  <SelectTrigger id={`edit-${def.name}`} className="w-full">
                    <SelectValue placeholder="Pilih..." />
                  </SelectTrigger>
                  <SelectContent>
                    {def.choices?.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            );
          } else if (def.kind === "textarea") {
            control = (
              <div className="flex flex-col gap-1.5">
                <FieldLabel htmlFor={`edit-${def.name}`}>{def.label}</FieldLabel>
                <Textarea
                  id={`edit-${def.name}`}
                  value={draft[def.name]}
                  disabled={readOnly}
                  onChange={(e) => setDraft((d) => ({ ...d, [def.name]: e.target.value }))}
                />
              </div>
            );
          } else {
            control = (
              <Field className="gap-1.5">
                <FieldLabel htmlFor={`edit-${def.name}`}>{def.label}</FieldLabel>
                <Input
                  id={`edit-${def.name}`}
                  value={draft[def.name]}
                  disabled={readOnly}
                  onChange={(e) => setDraft((d) => ({ ...d, [def.name]: e.target.value }))}
                />
              </Field>
            );
          }
          return (
            <div
              key={def.name}
              className={
                readOnly
                  ? "rounded-md bg-muted/30"
                  : isDirty
                    ? "rounded-md ring-2 ring-primary/40"
                    : ""
              }
            >
              {control}
            </div>
          );
        })}
      </FieldGroup>
      {canEditLinks && row.member_links.length > 0 && (
        <div className="flex flex-col gap-2">
          <div className="text-muted-foreground flex items-center gap-2 text-xs font-medium">
            <Link2 className="size-3.5" /> LINK TERPASANG
          </div>
          <div className="flex flex-col gap-2">
            {row.member_links.map((l) => (
              <div key={l.id} className="flex items-center justify-between gap-2 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
                <span className="font-medium">
                  LINK {l.role} {l.service ? `- ${serviceName(services, l.service)}` : ""}
                </span>
                <div className="text-muted-foreground text-xs">
                  {[l.provider, l.capacity, l.sid ? `SID: ${l.sid}` : null].filter(Boolean).join(" | ")}
                </div>
                <button
                  type="button"
                  className="text-destructive hover:text-destructive/70"
                  onClick={() => onLinkDelete(l.id)}
                  title="Hapus link"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {canEditLinks && (
        <div className="flex flex-col gap-2">
          <div className="text-muted-foreground flex items-center gap-2 text-xs font-medium">
            <Link2 className="size-3.5" /> TAMBAH LINK
          </div>

          <div className="grid grid-cols-1 gap-2 md:grid-cols-5">
            <div className="flex flex-col gap-1">
              <FieldLabel htmlFor="link-role">Role</FieldLabel>
              <Select value={newLink.role} onValueChange={(v) => setNewLink((n) => ({ ...n, role: v }))}>
                <SelectTrigger id="link-role" className="w-full">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  {memberOptions.role.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <FieldLabel htmlFor="link-service">Service</FieldLabel>
              <Select value={newLink.service ? String(newLink.service) : "none"} onValueChange={(v) => setNewLink((n) => ({ ...n, service: v === "none" ? null : Number(v) }))}>
                <SelectTrigger id="link-service" className="w-full">
                  <SelectValue placeholder="Service" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-</SelectItem>
                  {services.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <FieldLabel htmlFor="link-provider">Provider</FieldLabel>
              <Input id="link-provider" value={newLink.provider ?? ""} onChange={(e) => setNewLink((n) => ({ ...n, provider: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-1">
              <FieldLabel htmlFor="link-capacity">Capacity</FieldLabel>
              <Input id="link-capacity" value={newLink.capacity ?? ""} onChange={(e) => setNewLink((n) => ({ ...n, capacity: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-1">
              <FieldLabel htmlFor="link-sid">SID</FieldLabel>
              <div className="flex gap-1">
                <Input id="link-sid" value={newLink.sid ?? ""} onChange={(e) => setNewLink((n) => ({ ...n, sid: e.target.value }))} />
                <Button size="sm" onClick={() => onLinkSave(newLink)} title="Simpan link baru">
                  <Plus className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      {fileFields.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {fileFields.map((f) => (
            <label key={f.field} className="flex cursor-pointer items-center gap-2">
              <span className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-border bg-muted/40 px-3 py-1.5 font-medium text-muted-foreground text-xs">
                <Upload className="size-3.5" /> {f.label}
              </span>
              <input type="file" className="hidden" onChange={(e) => onFile(f.field, e.target.files?.[0])} />
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
