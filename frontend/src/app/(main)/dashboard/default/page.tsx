import {
  MetricCards,
  ProviderBreakdown,
  SdwanBreakdown,
  TopNetworks,
} from "./_components/metric-cards";
import { StatusOverview } from "./_components/status-overview";
import { GroupFilter } from "./_components/group-filter";

export default async function Page() {
  // C78/V80: the provider panel renders for every viewer — the backend's org
  // scope is the only fence, same stance as GroupFilter (C69) and SDWAN (C58).

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
        <ProviderBreakdown />
        {/* C58: deliberately outside the C43/C49 gate — External already reads
            every package name per-row in the grid, so the pie leaks nothing. */}
        <SdwanBreakdown />
      </div>
    </div>
  );
}