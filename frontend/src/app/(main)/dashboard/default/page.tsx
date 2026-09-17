import { getMeAccess } from "@/lib/auth";
import { isExternalNavHidden } from "@/lib/nav-access";

import { MetricCards, ProviderBreakdown, TopNetworks } from "./_components/metric-cards";
import { StatusOverview } from "./_components/status-overview";

export default async function Page() {
  // C43/C49: provider panel is internal-only. Deny-only — External keeps the
  // dashboard, so this hides the one card instead of redirecting the page (C42).
  const { isSuperuser, groups } = await getMeAccess();
  const showProviders = isSuperuser || !isExternalNavHidden(groups);

  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      <MetricCards />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 md:gap-6">
        <div className="lg:col-span-2">
          <StatusOverview />
        </div>
        <TopNetworks />
        {showProviders && <ProviderBreakdown />}
      </div>
    </div>
  );
}