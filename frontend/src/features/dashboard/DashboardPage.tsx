import { useQuery } from '@tanstack/react-query';
import { formatRelativeTime } from '@/utils';
import { dashboardApi } from '@/api';
import { QUERY_KEYS } from '@/constants';
import { KPIGrid } from '@/components/ui/KPICard';
import { AreaChartWidget, BarChartWidget } from '@/components/charts';
import { Card, CardHeader, CardTitle, Skeleton } from '@/components/ui/Card';
import { Avatar } from '@/components/ui/Card';

function ActivityFeed() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.DASHBOARD_ACTIVITY,
    queryFn: () => dashboardApi.activity(10),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <div className="flex flex-col divide-y divide-gray-100 dark:divide-gray-700">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 py-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="mb-1 h-3 w-48" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            ))
          : data?.map((item) => (
              <div key={item.id} className="flex items-start gap-3 py-3">
                <Avatar name={item.user_name} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">{item.description}</p>
                  <p className="mt-0.5 text-xs text-gray-400">{formatRelativeTime(item.created_at)}</p>
                </div>
              </div>
            ))}
      </div>
    </Card>
  );
}

function QuickStats() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.DASHBOARD_OVERVIEW,
    queryFn: dashboardApi.overview,
  });

  const stats = [
    { label: 'Datasets', value: data?.dataset_count ?? 0, color: 'bg-blue-500' },
    { label: 'AI Models', value: data?.model_count ?? 0, color: 'bg-purple-500' },
    { label: 'Reports', value: data?.report_count ?? 0, color: 'bg-green-500' },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((s) => (
        <Card key={s.label} padding="sm" className="text-center">
          {isLoading ? (
            <Skeleton className="mx-auto h-8 w-12" />
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </>
          )}
        </Card>
      ))}
    </div>
  );
}

const MOCK_REVENUE = Array.from({ length: 12 }, (_, i) => ({
  month: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i],
  revenue: Math.round(80000 + Math.random() * 40000),
  customers: Math.round(1200 + Math.random() * 400),
}));

const MOCK_SEGMENTS = [
  { segment: 'Champions', count: 342 },
  { segment: 'Loyal', count: 521 },
  { segment: 'At Risk', count: 189 },
  { segment: 'Lost', count: 97 },
  { segment: 'New', count: 413 },
];

export function DashboardPage() {
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: QUERY_KEYS.DASHBOARD_KPIS,
    queryFn: dashboardApi.kpis,
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Executive Dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Real-time overview of your customer intelligence platform</p>
      </div>

      <KPIGrid kpis={kpis ?? []} loading={kpisLoading} columns={4} />

      <QuickStats />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AreaChartWidget
            title="Revenue Trend"
            description="Monthly revenue over the past 12 months"
            data={MOCK_REVENUE}
            areas={[{ key: 'revenue', label: 'Revenue' }]}
            xKey="month"
            height={260}
          />
        </div>
        <ActivityFeed />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <BarChartWidget
          title="Customer Segments"
          description="Distribution of customers by segment"
          data={MOCK_SEGMENTS}
          bars={[{ key: 'count', label: 'Customers' }]}
          xKey="segment"
          height={240}
        />
        <BarChartWidget
          title="Monthly Customers"
          description="New customers acquired per month"
          data={MOCK_REVENUE}
          bars={[{ key: 'customers', label: 'New Customers', color: '#10b981' }]}
          xKey="month"
          height={240}
        />
      </div>
    </div>
  );
}
