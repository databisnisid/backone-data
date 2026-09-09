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

export const SDWAN_CHOICES = [
  "BackOne - SDWAN Lite",
  "BackOne - SDWAN Pro",
  "BackOne - SDWAN Gateway",
  "BackOne - Tanpa SDWAN",
];

export const BAA_STATUS_CHOICES = ["New Link", "Upgrade Link", "Downgrade Link", "Relokasi"];

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

export function visibleColumns(me: Me): ColVisibility {
  const support = isSupport(me);
  const sales = isSales(me);
  const finance = isFinance(me);
  return {
    situs: true,
    layanan: support || sales || finance,
    timeline: true,
    // BAA col: BAA cat+file — shown to Support/Sales. Finance does not get it.
    baa: support || sales,
    po: support || finance,
    // Invoice col isolated to Finance + Support/superuser admin.
    invoice: support || finance,
    // BAP file visible only to ops (server masks bap_file otherwise).
    dismantle: support,
    keterangan: true,
  };
}
