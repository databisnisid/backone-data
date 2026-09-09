"use client";

import * as React from "react";

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
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { createSite, fetchNetworks } from "./api";
import { type NetworkOption, SDWAN_CHOICES } from "./data";

export function CreateSiteDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [networks, setNetworks] = React.useState<NetworkOption[]>([]);
  const [name, setName] = React.useState("");
  const [memberId, setMemberId] = React.useState("");
  const [address, setAddress] = React.useState("");
  const [sdwan, setSdwan] = React.useState<string>("");
  const [network, setNetwork] = React.useState<string>("");
  const [project, setProject] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (open) {
      fetchNetworks()
        .then(setNetworks)
        .catch((e) => toast.error(e.message));
    }
  }, [open]);

  function reset() {
    setName("");
    setMemberId("");
    setAddress("");
    setSdwan("");
    setNetwork("");
    setProject("");
  }

  async function submit() {
    if (!name || !memberId) {
      toast.error("Nama Site dan Kode/ID wajib diisi.");
      return;
    }
    setSubmitting(true);
    try {
      await createSite({
        name,
        member_id: memberId,
        address: address || null,
        sdwan_package: sdwan || null,
        project_number: project || null,
        network: network ? Number(network) : null,
      });
      toast.success("Situs manual dibuat.");
      reset();
      onOpenChange(false);
      window.location.reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Tambah Situs Baru</DialogTitle>
          <DialogDescription>
            Site manual (contoh: kategori Non / Tanpa SD-WAN) yang tidak terhubung API controller.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Field className="gap-1.5">
            <FieldLabel htmlFor="new-member-code">Kode Situs / Member ID *</FieldLabel>
            <Input
              id="new-member-code"
              value={memberId}
              onChange={(e) => setMemberId(e.target.value)}
              placeholder="S0104"
            />
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="new-name">Nama Site *</FieldLabel>
            <Input
              id="new-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Sariguna Primatirta Plant ..."
            />
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="new-address">Alamat</FieldLabel>
            <Input id="new-address" value={address} onChange={(e) => setAddress(e.target.value)} />
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="new-sdwan">Paket Layanan (SDWAN)</FieldLabel>
            <Select value={sdwan || undefined} onValueChange={setSdwan}>
              <SelectTrigger id="new-sdwan">
                <SelectValue placeholder="Pilih..." />
              </SelectTrigger>
              <SelectContent>
                {SDWAN_CHOICES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="new-network">Networks</FieldLabel>
            <Select value={network || undefined} onValueChange={setNetwork}>
              <SelectTrigger id="new-network">
                <SelectValue placeholder="(Opsional)" />
              </SelectTrigger>
              <SelectContent>
                {networks.map((n) => (
                  <SelectItem key={n.id} value={String(n.id)}>
                    {n.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field className="gap-1.5 md:col-span-2">
            <FieldLabel htmlFor="new-project">Project Number</FieldLabel>
            <Input
              id="new-project"
              value={project}
              onChange={(e) => setProject(e.target.value)}
              placeholder="PRJ-2026-000"
            />
          </Field>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Batal
          </Button>
          <Button onClick={submit} disabled={submitting}>
            {submitting ? "Menyimpan..." : "Simpan"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
