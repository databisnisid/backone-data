"use client";

import * as React from "react";

import { Link2, Pencil, Plus, Trash2, Upload, X, FileText } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import { createSiteLink, deleteSiteFile, deleteSiteLink, fetchLinkServices, fetchMemberOptions, fetchSite, patchSiteLink, uploadSiteFile, type MemberOptions } from "./api";
import {
  isExternalViewOnly,
  isFieldVisible,
  isFieldWritable,
  linkDetail,
  type Me,
  type SiteLink,
  type SiteRow,
} from "./data";



type ScalarDef = {
  name: string;
  label: string;
  kind: "text" | "select" | "textarea";
  choices?: string[];
  writable: boolean;
  displayFor?: (row: SiteRow) => string;
};

// V34-view: all fields shown to all 5 groups; non-writable fields rendered disabled.
function scalarDefsFor(me: Me, options: MemberOptions): ScalarDef[] {
  const defs: { name: string; label: string; kind: "text" | "select" | "textarea"; choices?: string[]; displayFor?: (row: SiteRow) => string }[] = [
    { name: "name", label: "Nama Site", kind: "text" },
    { name: "address", label: "Alamat", kind: "text" },
    { name: "member_code", label: "Kode Situs", kind: "text" },
    { name: "member_id", label: "Member ID", kind: "text" },
    { name: "online_at", label: "Online At", kind: "text" },
    { name: "offline_at", label: "Offline At", kind: "text" },
    { name: "network", label: "Network", kind: "text", displayFor: (r) => r.network_name ?? "" },
    { name: "project_number", label: "Project Number", kind: "text" },
    { name: "sdwan_package", label: "Paket Layanan (SDWAN)", kind: "select", choices: options.sdwan_package },
    { name: "baa_status_category", label: "Status BAA", kind: "select", choices: options.baa_status_category },
    { name: "invoice_number", label: "Nomor Invoice", kind: "text" },
    { name: "notes", label: "Keterangan", kind: "textarea" },
    { name: "ip_address", label: "IP Address", kind: "text" },
  ];
  return defs.filter((d) => isFieldVisible(me, d.name)).map((d) => ({ ...d, writable: isFieldWritable(me, d.name) }));
}

// V34-view: all file fields shown; non-writable disabled.
function fileFieldsFor(me: Me): { field: string; label: string; writable: boolean }[] {
  const defs = [
    { field: "upload_baa", label: "Upload BAA" },
    { field: "po_file_user", label: "PO dari User" },
    { field: "po_file_vendor", label: "PO ke Vendor" },
    { field: "invoice_file", label: "Upload Bukti Invoice" },
    { field: "bap_file", label: "BAP Dismantle" },
  ];
  return defs.filter((d) => isFieldVisible(me, d.field)).map((d) => ({ ...d, writable: isFieldWritable(me, d.field) }));
}


function useLinkServices(me: Me): { id: number; name: string }[] {
  const [services, setServices] = React.useState<{ id: number; name: string }[]>([]);
  const canEditLinks = isFieldWritable(me, "member_links");
  React.useEffect(() => {
    if (!canEditLinks) return;
    fetchLinkServices()
      .then(setServices)
      .catch(() => setServices([]));
  }, [canEditLinks]);
  return services;
}

const EMPTY_OPTIONS: MemberOptions = {
  sdwan_package: [],
  default_sdwan_package: "",
  baa_status_category: [],
  role: [],
};

function useMemberOptions(): MemberOptions {
  const [options, setOptions] = React.useState<MemberOptions>(EMPTY_OPTIONS);
  React.useEffect(() => {
    fetchMemberOptions()
      .then(setOptions)
      .catch(() => setOptions(EMPTY_OPTIONS));
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
  const [draft, setDraft] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(
      scalarDefs.map((d) => [d.name, (row as unknown as Record<string, string | null>)[d.name] ?? ""]),
    ),
  );
  const dirty = scalarDefs
    .filter((d) => d.writable)
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
      payload[name] = v === "" ? null : (name === "network" ? Number(v) : v);
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
  const canEditLinks = isFieldWritable(me, "member_links");
  // C40/V55: one form serves both edit and read-only; derived from the writable
  // flags the form already computes, so no new prop and no second code path.
  const noWritableField = !canEditLinks && !scalarDefs.some((d) => d.writable) && !fileFields.some((f) => f.writable);
  const hideSid = isExternalViewOnly(me);
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
  async function onFileDelete(field: string) {
    try {
      await deleteSiteFile(row.id, field);
      const updated = await fetchSite(row.id);
      onRowUpdate(updated);
      toast.success("File dihapus");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{noWritableField ? "READ ONLY" : "EDIT MODE ACTIVE"}</Badge>
          <span className="font-medium">{row.name}</span>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone}>
            <X className="size-4" /> {noWritableField ? "Tutup" : "Batal"}
          </Button>
          {!noWritableField && (
            <Button size="sm" onClick={submit} disabled={!dirty.length}>
              <Pencil className="size-4" /> Simpan
            </Button>
          )}
        </div>
      </div>

      {/* Read-only info fields */}
      {(() => {
        const INFO_FIELDS = ["name", "address", "member_id", "online_at", "offline_at", "network"];
        const infoDefs = scalarDefs.filter((d) => INFO_FIELDS.includes(d.name));
        const editDefs = scalarDefs.filter((d) => !INFO_FIELDS.includes(d.name));
        return (
          <>
            <div className="flex flex-col gap-2">
              <div className="text-muted-foreground flex items-center gap-2 text-xs font-medium">
                <FileText className="size-3.5" /> INFORMASI SITUS
              </div>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1 rounded-md border border-border bg-muted/30 px-4 py-3 md:grid-cols-3">
                {infoDefs.map((def) => {
                  const val = def.displayFor ? def.displayFor(row) : draft[def.name];
                  return (
                    <div key={def.name} className="flex flex-col gap-0.5">
                      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">{def.label}</span>
                      <span className="text-sm">{val || <span className="text-muted-foreground">—</span>}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <FieldGroup className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {editDefs.map((def) => {
                const isDirty = dirty.includes(def.name);
                const readOnly = !def.writable;
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
                        value={def.displayFor ? def.displayFor(row) : draft[def.name]}
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
          </>
        );
      })()}
      {row.member_links.length > 0 && (
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
                  {linkDetail(l, hideSid)}
                </div>
                {canEditLinks && (
                  <button
                    type="button"
                    className="text-destructive hover:text-destructive/70"
                    onClick={() => onLinkDelete(l.id)}
                    title="Hapus link"
                  >
                    <Trash2 className="size-4" />
                  </button>
                )}
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
              <FieldLabel htmlFor="link-capacity">CID</FieldLabel>
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
        <div className="flex flex-col gap-3">
          {/* Uploaded files list */}
          {(() => {
            const uploaded = fileFields.filter((f) => {
              const val = (row as unknown as Record<string, string | null>)[f.field];
              return !!val;
            });
            if (uploaded.length === 0) return null;
            return (
              <div className="flex flex-col gap-1">
                <div className="text-muted-foreground flex items-center gap-2 text-xs font-medium">
                  <FileText className="size-3.5" /> FILE TERUPLOAD
                </div>
                <div className="flex flex-col gap-0.5">
                  {uploaded.map((f) => {
                    const val = (row as unknown as Record<string, string | null>)[f.field]!;
                    const fileName = val.split("/").pop();
                    const fileUrl = `/api/media/${val}`;
                    return (
                      <div key={f.field} className="flex items-center gap-2">
                        <a href={fileUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-primary hover:underline text-xs">
                          <FileText className="size-3.5 shrink-0" /> <span className="font-medium">{f.label}:</span> {fileName}
                        </a>
                        {me.is_superuser && (
                          <button type="button" className="text-destructive hover:text-destructive/70" onClick={() => onFileDelete(f.field)} title={`Hapus ${f.label}`}>
                            <Trash2 className="size-3.5" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}
          {/* Upload buttons */}
          {fileFields.some((f) => f.writable) && (
            <div className="flex flex-col gap-1">
              <div className="text-muted-foreground flex items-center gap-2 text-xs font-medium">
                <Upload className="size-3.5" /> UNGGAH DOKUMEN
              </div>
              <div className="flex flex-wrap gap-3">
                {fileFields.map((f) => {
                  const val = (row as unknown as Record<string, string | null>)[f.field];
                  const hasFile = !!val;
                  const fileName = hasFile ? val!.split("/").pop() : null;
                  return f.writable ? (
                    <label key={f.field} className={`flex flex-col gap-0.5 rounded-md border border-dashed border-muted-foreground/40 bg-muted/40 px-3 py-1.5 cursor-pointer hover:border-primary/60 hover:bg-muted/70 transition-colors`}>
                      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">{f.label}</span>
                      <div className="flex items-center gap-1.5">
                        <Upload className="size-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground text-xs">{hasFile ? `Ganti ${fileName}` : "Pilih file"}</span>
                      </div>
                      <input type="file" className="hidden" onChange={(e) => onFile(f.field, e.target.files?.[0])} />
                    </label>
                  ) : (
                    <div key={f.field} className="flex flex-col gap-0.5 rounded-md border border-border bg-muted/40 px-3 py-1.5 opacity-50">
                      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">{f.label}</span>
                      <span className="text-muted-foreground text-xs">{hasFile ? fileName : "Tidak dapat diubah"}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
