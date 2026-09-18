"use client";

import { ChevronDown, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { useGroupCommit, useSelectedGroups, useStats } from "./stats";

// C65/C69: rendered for every dashboard viewer including External — the org
// scope on `stats` is the only fence, matching the provider dropdown's rule
// on /sites rather than the C43/C49 internal-only CARD gate.
export function GroupFilter() {
  const stats = useStats();
  const selected = useSelectedGroups();
  const commit = useGroupCommit();
  // T69: the picker's options ARE the card payload, so there is no second
  // request and no second endpoint.
  const options = (stats?.group_aggregates ?? []).map((g) => g.network_group);

  return (
    <div className="flex items-center gap-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-52 justify-between font-normal">
            {selected.length === 0 ? "Semua Group" : `${selected.length} Group`}
            <ChevronDown className="size-4 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="max-h-72 overflow-y-auto">
          {options.length === 0 && <div className="px-2 py-1.5 text-sm text-muted-foreground">Tidak ada group.</div>}
          {options.map((g) => (
            <DropdownMenuCheckboxItem
              key={g}
              checked={selected.includes(g)}
              onSelect={(e) => e.preventDefault()}
              onCheckedChange={(on) => commit(on ? [...selected, g] : selected.filter((x) => x !== g))}
            >
              {g}
            </DropdownMenuCheckboxItem>
          ))}
          {selected.length > 0 && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => commit([])}>
                <X className="size-4" /> Reset
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
