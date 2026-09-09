"use client";

import * as React from "react";

import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Network = { id: number; name: string; network_id: string; network_group: number | null };
type NetworkGroup = { id: number; name: string };
type Org = { id: number; name: string; networks: number[]; is_no_org: boolean };

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const body = (await res.json()) as { results?: T; detail?: string };
  if (!res.ok) throw new Error((body as { detail?: string }).detail ?? "Fetch failed");
  if (body.results) return body.results as T;
  return body as T;
}

export function NetworksView() {
  const [networks, setNetworks] = React.useState<Network[]>([]);
  const [groups, setGroups] = React.useState<NetworkGroup[]>([]);

  React.useEffect(() => {
    void get<Network[]>("/api/backend/networks")
      .then(setNetworks)
      .catch((e) => toast.error(e.message));
    void get<NetworkGroup[]>("/api/backend/networks/groups")
      .then(setGroups)
      .catch((e) => toast.error(e.message));
  }, []);

  const groupName = (id: number | null) => groups.find((g) => g.id === id)?.name ?? "Ungroup";

  return (
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
