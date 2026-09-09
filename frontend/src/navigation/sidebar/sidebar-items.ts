import { Gauge, Globe, LayoutDashboard, Server, Settings, type LucideIcon, Users } from "lucide-react";

export type NavBadge = "new" | "soon";

export interface NavSubItem {
  id: string;
  title: string;
  url: string;
  icon?: LucideIcon;
  badge?: NavBadge;
  disabled?: boolean;
  newTab?: boolean;
}

interface NavItemBase {
  id: string;
  title: string;
  icon?: LucideIcon;
  badge?: NavBadge;
  disabled?: boolean;
  newTab?: boolean;
}

export interface NavMainLinkItem extends NavItemBase {
  url: string;
  subItems?: never;
}

export interface NavMainParentItem extends NavItemBase {
  subItems: NavSubItem[];
}

export type NavMainItem = NavMainLinkItem | NavMainParentItem;

export interface NavGroup {
  id: number;
  label?: string;
  items: NavMainItem[];
}

export const sidebarItems: NavGroup[] = [
  {
    id: 0,
    label: "BackOne Data",
    items: [
      {
        id: "dashboard",
        title: "Dashboard",
        url: "/dashboard/default",
        icon: LayoutDashboard,
      },
      {
        id: "sites",
        title: "Sites",
        url: "/sites",
        icon: Globe,
      },
      {
        id: "quota",
        title: "Quota",
        url: "/quota",
        icon: Gauge,
      },
      {
        id: "networks",
        title: "Networks",
        url: "/networks",
        icon: Server,
      },
      {
        id: "organizations",
        title: "Pengaturan",
        url: "/organizations",
        icon: Users,
      },
      {
        id: "settings-lookups",
        title: "Lookups",
        url: "/settings/lookups",
        icon: Settings,
      },
    ],
  },
];