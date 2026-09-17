"use client";

import * as React from "react";

import { ChevronDown, Download, Plus, Search, X } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { fetchMe, fetchProviders, fetchSites, patchSite } from "./api";
import { CreateSiteDialog } from "./create-site-dialog";
import {
  type ColVisibility,
  isExternalViewOnly,
  isFinance,
  isPurchasing,
  isSales,
  isSupport,
  linkDetail,
  type Me,
  PAGE_SIZE,
  type SiteLink,
  type SiteRow,
  visibleColumns,
} from "./data";
import { SiteEditForm } from "./site-edit-form";
function fileHref(u: string | null) {
  if (!u) return null;
  if (u.startsWith("http")) return u;
  return `/api/media/${u}`;
}

function fileName(u: string | null) {
  if (!u) return null;
  return u.split("/").pop();
}

function LinkChip({ url, label }: { url: string | null; label: string }) {
  if (!url) return null;
  return (
    <div>
      <a href={url} target="_blank" rel="noreferrer" className="text-primary underline">
        {label}
      </a>
    </div>
  );
}

function SiteLinks({ links, hideSid }: { links: SiteLink[]; hideSid?: boolean }) {
  if (!links.length) return <span className="text-muted-foreground">-</span>;
  return (
    <div className="space-y-1">
      {links.map((l) => (
        <div key={l.id} className="text-xs">
          <span className="font-medium">
            LINK {l.role} {l.service ? `- ${l.service}` : ""}
          </span>
          <div className="text-muted-foreground">
            {linkDetail(l, hideSid)}
          </div>
        </div>
      ))}
    </div>
  );
}

function Cols({ me, cols, row, onEdit }: { me: Me; cols: ColVisibility; row: SiteRow; onEdit: (id: number) => void }) {
  // Role-scoped edit (T23): any role with writable feature fields may open the form.
  // External/External Network hold no edit role, so they get the read-only "View" cell (C39).
  const editable = isSupport(me) || isSales(me) || isFinance(me) || isPurchasing(me);
  const hideSid = isExternalViewOnly(me);
  const baaUrl = fileHref(row.upload_baa);
  return (
    <>
      {cols.situs && (
        <TableCell>
          <div className="font-medium">{row.name ?? row.member_id}</div>
          <div className="text-muted-foreground text-xs">{row.address ?? "-"}</div>
        </TableCell>
      )}
      {cols.layanan && (
        <TableCell>
          {row.sdwan_package && <Badge variant="secondary">{row.sdwan_package}</Badge>}
          {row.project_number && <div className="text-xs">Project: {row.project_number}</div>}
          {row.network_group && <div className="text-xs">Networks: {row.network_name ?? row.network_group}</div>}
          <SiteLinks links={row.member_links} hideSid={hideSid} />
        </TableCell>
      )}
      {cols.timeline && (
        <TableCell>
          <div className="text-xs">Start: {row.online_at ?? "-"}</div>
          <div className="text-xs">Stop: {row.offline_at ?? "-"}</div>
          <div className={row.is_online ? "text-emerald-600" : "text-destructive"}>
            {row.is_online ? "Online" : "Offline"}
          </div>
        </TableCell>
      )}
      {cols.baa && (
        <TableCell>
          {row.baa_status_category ?? <span className="text-muted-foreground">-</span>}
          <LinkChip url={baaUrl} label={fileName(row.upload_baa) ?? "BAA"} />
        </TableCell>
      )}
      {cols.po && (
        <TableCell>
          <LinkChip url={fileHref(row.po_file_user)} label="PO dari User" />
          <LinkChip url={fileHref(row.po_file_vendor)} label="PO ke Vendor" />
        </TableCell>
      )}
      {cols.invoice && (
        <TableCell>
          {row.invoice_number ?? <span className="text-muted-foreground">-</span>}
          <LinkChip url={fileHref(row.invoice_file)} label={fileName(row.invoice_file) ?? "Bukti"} />
        </TableCell>
      )}
      {cols.dismantle && (
        <TableCell>
          <LinkChip url={fileHref(row.bap_file)} label="BAP" />
        </TableCell>
      )}
      {cols.keterangan && (
        <TableCell>
          <span className="line-clamp-2 text-xs">{row.notes ?? "-"}</span>
        </TableCell>
      )}
      <TableCell>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onEdit(row.id)}
          title={editable ? "Ubah situs" : "Lihat detail situs (read-only)"}
        >
          {editable ? "Ubah" : "View"}
        </Button>
      </TableCell>
    </>
  );
}

function headersFor(cols: ColVisibility): string[] {
  const defs: { label: string; col: keyof ColVisibility }[] = [
    { label: "Situs & Address", col: "situs" },
    { label: "Detail Layanan & Project", col: "layanan" },
    { label: "Timeline", col: "timeline" },
    { label: "Status BAA", col: "baa" },
    { label: "PO Dokumen", col: "po" },
    { label: "Invoice", col: "invoice" },
    { label: "Dismantle", col: "dismantle" },
    { label: "Keterangan", col: "keterangan" },
  ];
  return defs.filter((d) => cols[d.col]).map((d) => d.label);
}

export function SitesView() {
  const [me, setMe] = React.useState<Me | null>(null);
  const [rows, setRows] = React.useState<SiteRow[]>([]);
  const [total, setTotal] = React.useState(0);
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [providers, setProviders] = React.useState<string[]>([]);
  const [providerOptions, setProviderOptions] = React.useState<string[]>([]);
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [createOpen, setCreateOpen] = React.useState(false);

  React.useEffect(() => {
    fetchMe()
      .then((m) => setMe(m))
      .catch((e) => toast.error((e as Error).message));
  }, []);

  React.useEffect(() => {
    fetchProviders()
      .then((p) => setProviderOptions(p))
      .catch((e) => toast.error((e as Error).message));
  }, []);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSites({ page, search, providers });
      setRows(data.results);
      setTotal(data.count);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [page, search, providers]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const applyEdit = React.useCallback((updated: SiteRow) => {
    setRows((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
  }, []);

  const saveScalars = React.useCallback(
    async (id: number, payload: Record<string, unknown>) => {
      try {
        const updated = await patchSite(id, payload);
        applyEdit(updated);
        setEditingId(null);
        toast.success("Saved");
      } catch (e) {
        toast.error((e as Error).message);
      }
    },
    [applyEdit],
  );

  if (!me) {
    return <div className="p-6">Loading session...</div>;
  }

  const cols = visibleColumns(me);
  const headerList = headersFor(cols);
  const colSpan = headerList.length + 1;
  const pageCount = Math.max(Math.ceil(total / PAGE_SIZE), 1);
  const hasPrev = page > 1;
  const hasNext = page < pageCount;

  let body: React.ReactNode;
  if (loading) {
    body = <div className="p-6 text-center text-muted-foreground">Loading...</div>;
  } else if (rows.length === 0) {
    body = <div className="p-6 text-center text-muted-foreground">Tidak ada situs.</div>;
  } else {
    body = (
      <>
        <Table className="table-fixed [&_td]:whitespace-normal [&_th]:whitespace-normal">
          <colgroup>
            <col className="w-[24%]" />
            <col className="w-[20%]" />
            <col />
            <col />
            <col />
            <col />
            <col />
            <col />
            <col className="w-[10%]" />
          </colgroup>
            <TableHeader>
              <TableRow>
                {headerList.map((h) => (
                  <TableHead key={h}>{h}</TableHead>
                ))}
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) =>
                editingId === row.id ? (
                  <TableRow key={row.id}>
                    <TableCell colSpan={colSpan}>
                      <SiteEditForm
                        me={me}
                        row={row}
                        onSave={saveScalars}
                        onDone={() => setEditingId(null)}
                        onRowUpdate={applyEdit}
                      />
                    </TableCell>
                  </TableRow>
                ) : (
                  <TableRow key={row.id}>
                    <Cols me={me} cols={cols} row={row} onEdit={setEditingId} />
                  </TableRow>
                ),
              )}
            </TableBody>
        </Table>
        <div className="flex items-center justify-between">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (hasPrev) setPage(page - 1);
                  }}
                  className={!hasPrev ? "pointer-events-none opacity-50" : undefined}
                />
              </PaginationItem>
              <PaginationItem>
                <span className="text-muted-foreground text-sm">
                  Page {page} / {pageCount}
                </span>
              </PaginationItem>
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (hasNext) setPage(page + 1);
                  }}
                  className={!hasNext ? "pointer-events-none opacity-50" : undefined}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      </>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium tracking-tight">Sites</div>
          <div className="text-muted-foreground text-sm">
            {total} dari {total} situs
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isSupport(me) && (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" /> Tambah Situs Baru
            </Button>
          )}
          {!isExternalViewOnly(me) && (
            <Button variant="outline" asChild>
              <a href="/api/backend/members/sites/export">
                <Download className="size-4" /> Download XLSX
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative w-72">
          <Search className="absolute top-2.5 left-2.5 size-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Pencarian sites..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
          {search && (
            <button
              type="button"
              aria-label="Clear search"
              className="absolute top-2.5 right-2 text-muted-foreground"
              onClick={() => {
                setSearch("");
                setPage(1);
              }}
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-48 justify-between font-normal">
              {providers.length === 0 ? "Semua Provider" : `${providers.length} Provider`}
              <ChevronDown className="size-4 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="max-h-72 overflow-y-auto">
            {providerOptions.length === 0 && (
              <div className="px-2 py-1.5 text-sm text-muted-foreground">Tidak ada provider.</div>
            )}
            {providerOptions.map((p) => (
              <DropdownMenuCheckboxItem
                key={p}
                checked={providers.includes(p)}
                onSelect={(e) => e.preventDefault()}
                onCheckedChange={(on) => {
                  setProviders((prev) => (on ? [...prev, p] : prev.filter((x) => x !== p)));
                  setPage(1);
                }}
              >
                {p}
              </DropdownMenuCheckboxItem>
            ))}
            {providers.length > 0 && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={() => {
                    setProviders([]);
                    setPage(1);
                  }}
                >
                  <X className="size-4" /> Reset
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Card>
        <CardContent className="space-y-4 p-4">{body}</CardContent>
      </Card>
      <CreateSiteDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
