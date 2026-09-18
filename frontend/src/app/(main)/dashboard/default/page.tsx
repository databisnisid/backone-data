import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import {
  MetricCards,
  ProviderBreakdown,
  SdwanBreakdown,
  TopNetworks,
} from "./_components/metric-cards";
import { StatusOverview } from "./_components/status-overview";
import { GroupFilter } from "./_components/group-filter";

export default async function Page() {
  // C43/C49: provider panel is internal-only. Deny-only — External keeps the
  // dashboard, so this hides the one card instead of redirecting the page (C42).
  const { isSuperuser, groups } = await getMeAccess();
  const showProviders = isSuperuser || !isExternalNavHidden(groups);

  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      {/* C69: outside the C43/C49 gate — every viewer including External gets
          the picker; the backend's org scope is the only fence. */}
      <GroupFilter />
      <MetricCards />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 md:gap-6">
        <div className="lg:col-span-2">
          <StatusOverview />
        </div>
        <TopNetworks />
        {showProviders && <ProviderBreakdown />}
        {/* C58: deliberately outside the C43/C49 gate — External already reads
            every package name per-row in the grid, so the pie leaks nothing. */}
        <SdwanBreakdown />
      </div>
    </div>
  );
}