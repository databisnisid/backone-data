export type SiteLink = {
  id: number;
  role: string;
  service: number | null;
  provider: string | null;
  capacity: string | null;
  sid: string | null;
};

export type SiteRow = {
  id: number;
  name: string | null;
  member_code: string | null;
  member_id: string;
  address: string | null;
  location: string | null;
  online_at: string | null;
  offline_at: string | null;
  network: number | null;
  network_name: string | null;
  network_group: string | null;
  links: number[];
  member_links: SiteLink[];
  service_line: string | null;
  quota_string: string | null;
  upload_baa: string | null;
  invoice_number: string | null;
  invoice_file: string | null;
  po_file_user: string | null;
  po_file_vendor: string | null;
  bap_file: string | null;
  ip_address: string | null;
  sdwan_package: string | null;
  project_number: string | null;
  baa_status_category: string | null;
  notes: string | null;
  is_manual: boolean;
  is_online: number;
};

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type Me = {
  id: number;
  username: string;
  is_superuser: boolean;
  groups: string[];
  organization: { id: number; name: string } | null;
};

export type NetworkOption = { id: number; name: string; network_id: string };

export const PAGE_SIZE = 25;

// Role groups present in Django Groups (members.rbac mirrors these server-side).
export const SUPPORT_ROLES = new Set(["Support"]);
export const SALES_ROLES = new Set(["Sales"]);
export const FINANCE_ROLES = new Set(["Finance"]);
export const PURCHASING_ROLES = new Set(["Purchasing"]);

export function isSupport(me: Me) {
  return me.is_superuser || me.groups.some((g) => SUPPORT_ROLES.has(g));
}
export function isSales(me: Me) {
  return me.groups.some((g) => SALES_ROLES.has(g));
}
export function isFinance(me: Me) {
  return me.groups.some((g) => FINANCE_ROLES.has(g));
}
export function isPurchasing(me: Me) {
  return me.groups.some((g) => PURCHASING_ROLES.has(g));
}
export type ColKey = "situs" | "layanan" | "timeline" | "baa" | "po" | "invoice" | "dismantle" | "keterangan";

export type ColVisibility = Record<ColKey, boolean>;

// V34-view: all 5 groups see the same columns. No role-based column hiding.
export function visibleColumns(_me: Me): ColVisibility {
  return {
    situs: true,
    layanan: true,
    timeline: true,
    baa: true,
    po: true,
    invoice: true,
    dismantle: true,
    keterangan: true,
  };
}

// V34-view: writable fields per role (mirrors members/rbac.py WRITE_BY_ROLE).
const WRITE_BY_ROLE: Record<string, Set<string>> = {
  Superuser: new Set(["name","member_id","address","location","online_at","offline_at","service_line","network","links","quota_string","upload_baa","invoice_number","invoice_file","po_file_user","po_file_vendor","bap_file","ip_address","sdwan_package","project_number","baa_status_category","notes","member_code","member_links"]),
  Support: new Set(["ip_address","member_links"]),
  Sales: new Set(["baa_status_category","upload_baa","notes","member_links","member_code","sdwan_package","po_file_user"]),
  Purchasing: new Set(["po_file_vendor","project_number"]),
  Finance: new Set(["invoice_number","invoice_file","notes"]),
};

export function writableFieldSet(me: Me): Set<string> {
  const roles: string[] = [];
  if (me.is_superuser) roles.push("Superuser");
  roles.push(...me.groups);
  const out = new Set<string>();
  for (const r of roles) {
    const w = WRITE_BY_ROLE[r];
    if (w) for (const f of w) out.add(f);
  }
  return out;
}

export function isFieldWritable(me: Me, field: string): boolean {
  return writableFieldSet(me).has(field);
}
