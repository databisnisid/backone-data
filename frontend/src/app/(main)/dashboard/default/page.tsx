import { MetricCards, TopNetworks } from "./_components/metric-cards";
import { StatusOverview } from "./_components/status-overview";

export default function Page() {
  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      <MetricCards />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 md:gap-6">
        <div className="lg:col-span-2">
          <StatusOverview />
        </div>
        <TopNetworks />
      </div>
    </div>
  );
}