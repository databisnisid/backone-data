"use client";

import * as React from "react";

import { FileUp } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { type ImportResult, importSitesXlsx } from "./api";

// C72/V76: preview then apply on the SAME bytes — the user must not re-pick the
// file between the two calls, so the chosen File is held in state, not an input.
export function ImportDialog({ open, onOpenChange, onImported }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported: () => void;
}) {
  const [file, setFile] = React.useState<File | null>(null);
  const [preview, setPreview] = React.useState<ImportResult | null>(null);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setFile(null);
      setPreview(null);
    }
  }, [open]);

  function pick(selected: File | null) {
    setFile(selected);
    setPreview(null);
  }

  async function previewUpload() {
    if (!file) return;
    setBusy(true);
    try {
      setPreview(await importSitesXlsx("preview", file));
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function applyUpload() {
    if (!file) return;
    setBusy(true);
    try {
      // V76: a rejected apply returns the same problems payload as preview, so
      // the rejection renders in place instead of a bare "Request failed (400)".
      const result = await importSitesXlsx("apply", file);
      setPreview(result);
      if (result.problems.length > 0) {
        toast.error("Import ditolak — tidak ada baris yang ditulis.");
        return;
      }
      toast.success("Import diterapkan.");
      onOpenChange(false);
      onImported();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const changed = preview ? Object.entries(preview.changed).filter(([, n]) => n > 0) : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import XLSX</DialogTitle>
          <DialogDescription>
            Unggah kembali file hasil edit dari <span className="font-medium">Download XLSX</span>. Baris yang tidak ada
            di file tidak diubah dan tidak dihapus.
          </DialogDescription>
        </DialogHeader>

        <label className="flex cursor-pointer items-center gap-2 rounded-md border border-dashed p-3 text-sm">
          <FileUp className="size-4" />
          <span>{file ? file.name : "Pilih file .xlsx"}</span>
          <input
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0] ?? null)}
          />
        </label>

        {preview && (
          <div className="space-y-2 text-sm">
            {preview.problems.length > 0 ? (
              <div className="space-y-1">
                <div className="font-medium text-destructive">{preview.problems.length} masalah — belum ada yang ditulis.</div>
                <ul className="max-h-48 space-y-1 overflow-auto text-muted-foreground">
                  {preview.problems.slice(0, 50).map((p, i) => (
                    <li key={i}>
                      {p.sheet} baris {p.row}: {p.message}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="space-y-1">
                <div className="font-medium">Siap diterapkan — tidak ada masalah.</div>
                <div className="text-muted-foreground">
                  {changed.length === 0
                    ? "Tidak ada perubahan pada file ini."
                    : changed.map(([sheet, n]) => `${sheet}: ${n} sel berubah`).join(" · ")}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Batal
          </Button>
          <Button variant="outline" onClick={previewUpload} disabled={!file || busy}>
            {busy ? "Memeriksa..." : "Preview"}
          </Button>
          <Button onClick={applyUpload} disabled={!preview || preview.problems.length > 0 || busy}>
            Terapkan
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
