import type { Page, SiteLink, SiteRow } from "./data";

async function jsonOrThrow<T>(res: Response): Promise<T> {
  const body = (await res.json().catch(() => ({}))) as { detail?: string };
  if (!res.ok) throw new Error(body.detail ?? `Request failed (${res.status})`);
  return body as T;
}

export async function fetchMe() {
  const res = await fetch("/api/auth/me");
  return jsonOrThrow<import("./data").Me>(res);
}

export async function fetchSites(params: {
  page: number;
  search?: string;
  providers?: string[];
  // V62: slice links carry these, so the grid's count matches the pie slice.
  sdwan?: string;
  status?: string;
  // V63: a `Top Networks` row carries the network id, never a status.
  networks?: string[];
}) {
  const q = new URLSearchParams();
  q.set("page", String(params.page));
  if (params.search) q.set("search", params.search);
  for (const p of params.providers ?? []) q.append("provider", p);
  if (params.sdwan) q.set("sdwan", params.sdwan);
  if (params.status) q.set("status", params.status);
  for (const n of params.networks ?? []) q.append("network", n);
  const res = await fetch(`/api/backend/members/sites?${q.toString()}`);
  return jsonOrThrow<Page<SiteRow>>(res);
}

export async function fetchNetworks() {
  const res = await fetch("/api/backend/networks");
  const data = await jsonOrThrow<Page<import("./data").NetworkOption>>(res);
  return data.results;
}

export async function patchSite(id: number, payload: Record<string, unknown>) {
  const res = await fetch(`/api/backend/members/sites/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<SiteRow>(res);
}

export async function uploadSiteFile(id: number, field: string, file: File) {
  const form = new FormData();
  form.append(field, file);
  const res = await fetch(`/api/backend/members/sites/${id}/upload/`, {
    method: "POST",
    body: form,
  });
  return jsonOrThrow<SiteRow>(res);
}
export async function deleteSiteFile(id: number, field: string) {
  const res = await fetch(`/api/backend/members/sites/${id}/delete-file/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ field }),
  });
  return jsonOrThrow<SiteRow>(res);
}

export async function createSite(payload: Record<string, unknown>) {
  const res = await fetch("/api/backend/members/sites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<SiteRow>(res);
}
export async function fetchSite(id: number) {
  const res = await fetch(`/api/backend/members/sites/${id}`);
  return jsonOrThrow<SiteRow>(res);
}

export async function fetchLinkServices() {
  const res = await fetch("/api/backend/members/links/services/");
  const data = await jsonOrThrow<{ id: number; name: string }[]>(res);
  return Array.isArray(data) ? data : [];
}
export type MemberOptions = {
  sdwan_package: string[];
  // C59: server-declared default package name the create dialog preselects.
  default_sdwan_package: string;
  baa_status_category: string[];
  role: string[];
};

export async function fetchMemberOptions() {
  const res = await fetch("/api/backend/members/options/");
  return jsonOrThrow<MemberOptions>(res);
}

export async function fetchProviders() {
  const res = await fetch("/api/backend/members/sites/providers/");
  return jsonOrThrow<string[]>(res);
}

export async function createSiteLink(memberId: number, link: Partial<SiteLink>) {
  const payload: Record<string, unknown> = { ...link, member: memberId };
  const res = await fetch("/api/backend/members/links/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<SiteLink>(res);
}

export async function patchSiteLink(id: number, link: Record<string, unknown>) {
  const res = await fetch(`/api/backend/members/links/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(link),
  });
  return jsonOrThrow<SiteLink>(res);
}

export async function deleteSiteLink(id: number) {
  const res = await fetch(`/api/backend/members/links/${id}/`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
}
