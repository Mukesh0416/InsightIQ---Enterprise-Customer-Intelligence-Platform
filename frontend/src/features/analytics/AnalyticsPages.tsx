import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi, datasetsApi } from '@/api';
import { QUERY_KEYS } from '@/constants';
import { Tabs } from '@/components/ui/Tabs';
import { Select } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, EmptyState, Skeleton } from '@/components/ui/Card';
import { KPIGrid } from '@/components/ui/KPICard';
import { AreaChartWidget, BarChartWidget, LineChartWidget, PieChartWidget } from '@/components/charts';
import { BarChart3 } from 'lucide-react';
import type { KPICard } from '@/types';

function DatasetSelector({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const { data } = useQuery({
    queryKey: QUERY_KEYS.DATASETS,
    queryFn: () => datasetsApi.list({ page_size: 100 }),
  });

  const options = (data?.items ?? [])
    .filter((d) => d.status === 'ready')
    .map((d) => ({ value: d.id, label: d.name }));

  return (
    <Select
      id="dataset-selector"
      label="Dataset"
      options={options}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Select a dataset…"
      className="max-w-xs"
    />
  );
}

// ─── EDA Page ─────────────────────────────────────────────────────────────────

export function EDAPage() {
  const [datasetId, setDatasetId] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_EDA(datasetId),
    queryFn: () => analyticsApi.eda(datasetId),
    enabled: !!datasetId,
  });

  const { data: corrData } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_EDA(datasetId + '_corr'),
    queryFn: () => analyticsApi.correlation(datasetId),
    enabled: !!datasetId,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Exploratory Data Analysis</h1>
          <p className="text-sm text-gray-500">Automated profiling, statistics, and quality checks</p>
        </div>
        <DatasetSelector value={datasetId} onChange={setDatasetId} />
      </div>

      {!datasetId ? (
        <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" description="Choose a dataset above to run exploratory analysis." />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      ) : (
        <>
          <KPIGrid kpis={(data?.summary_kpis as KPICard[]) ?? []} columns={4} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <BarChartWidget
              title="Column Data Types"
              data={(data?.dtype_distribution as Record<string, unknown>[]) ?? []}
              bars={[{ key: 'count', label: 'Columns' }]}
              xKey="dtype"
              height={240}
            />
            <BarChartWidget
              title="Missing Values by Column"
              data={(data?.missing_values as Record<string, unknown>[]) ?? []}
              bars={[{ key: 'missing_pct', label: 'Missing %', color: '#ef4444' }]}
              xKey="column"
              height={240}
            />
          </div>
          {corrData && (
            <Card>
              <CardHeader><CardTitle>Correlation Matrix</CardTitle></CardHeader>
              <pre className="overflow-x-auto text-xs text-gray-600 dark:text-gray-400">
                {JSON.stringify(corrData, null, 2)}
              </pre>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

// ─── Customer Analytics ───────────────────────────────────────────────────────

export function CustomerAnalyticsPage() {
  const [datasetId, setDatasetId] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_CUSTOMER(datasetId),
    queryFn: () => analyticsApi.customer(datasetId),
    enabled: !!datasetId,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Customer Analytics</h1>
          <p className="text-sm text-gray-500">Customer acquisition, behavior, and lifetime value insights</p>
        </div>
        <DatasetSelector value={datasetId} onChange={setDatasetId} />
      </div>

      {!datasetId ? (
        <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" description="Choose a dataset to view customer analytics." />
      ) : (
        <>
          <KPIGrid kpis={(data?.kpis as KPICard[]) ?? []} loading={isLoading} columns={4} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <LineChartWidget
              title="Customer Growth"
              data={(data?.growth_trend as Record<string, unknown>[]) ?? []}
              lines={[{ key: 'customers', label: 'Customers' }]}
              xKey="date"
              height={260}
              loading={isLoading}
            />
            <PieChartWidget
              title="Customer Segments"
              data={(data?.segments as { name: string; value: number }[]) ?? []}
              height={260}
              donut
              loading={isLoading}
            />
          </div>
        </>
      )}
    </div>
  );
}

// ─── Revenue Analytics ────────────────────────────────────────────────────────

export function RevenueAnalyticsPage() {
  const [datasetId, setDatasetId] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_REVENUE(datasetId),
    queryFn: () => analyticsApi.revenue(datasetId),
    enabled: !!datasetId,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Revenue Analytics</h1>
          <p className="text-sm text-gray-500">Revenue trends, forecasts, and breakdown analysis</p>
        </div>
        <DatasetSelector value={datasetId} onChange={setDatasetId} />
      </div>

      {!datasetId ? (
        <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" description="Choose a dataset to view revenue analytics." />
      ) : (
        <>
          <KPIGrid kpis={(data?.kpis as KPICard[]) ?? []} loading={isLoading} columns={4} />
          <AreaChartWidget
            title="Revenue Over Time"
            data={(data?.revenue_trend as Record<string, unknown>[]) ?? []}
            areas={[{ key: 'revenue', label: 'Revenue' }, { key: 'target', label: 'Target', color: '#f59e0b' }]}
            xKey="date"
            height={300}
            loading={isLoading}
          />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <BarChartWidget
              title="Revenue by Product"
              data={(data?.by_product as Record<string, unknown>[]) ?? []}
              bars={[{ key: 'revenue', label: 'Revenue' }]}
              xKey="product"
              height={240}
              loading={isLoading}
            />
            <BarChartWidget
              title="Revenue by Region"
              data={(data?.by_region as Record<string, unknown>[]) ?? []}
              bars={[{ key: 'revenue', label: 'Revenue', color: '#8b5cf6' }]}
              xKey="region"
              height={240}
              loading={isLoading}
            />
          </div>
        </>
      )}
    </div>
  );
}

// ─── Analytics Hub (tabbed) ───────────────────────────────────────────────────

const ANALYTICS_TABS = [
  { id: 'eda', label: 'EDA' },
  { id: 'customer', label: 'Customer' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'retention', label: 'Retention' },
  { id: 'cohort', label: 'Cohort' },
  { id: 'rfm', label: 'RFM' },
  { id: 'clv', label: 'CLV' },
];

function RetentionPage({ datasetId }: { datasetId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_RETENTION(datasetId),
    queryFn: () => analyticsApi.retention(datasetId),
    enabled: !!datasetId,
  });
  return (
    <>
      <KPIGrid kpis={(data?.kpis as KPICard[]) ?? []} loading={isLoading} columns={4} />
      <LineChartWidget
        title="Retention Rate Over Time"
        data={(data?.retention_trend as Record<string, unknown>[]) ?? []}
        lines={[{ key: 'retention_rate', label: 'Retention Rate' }, { key: 'churn_rate', label: 'Churn Rate', color: '#ef4444' }]}
        xKey="period"
        height={280}
        loading={isLoading}
      />
    </>
  );
}

function RFMPage({ datasetId }: { datasetId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_RFM(datasetId),
    queryFn: () => analyticsApi.rfm(datasetId),
    enabled: !!datasetId,
  });
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <PieChartWidget
        title="RFM Segments"
        data={(data?.segments as { name: string; value: number }[]) ?? []}
        height={280}
        donut
        loading={isLoading}
      />
      <BarChartWidget
        title="Segment Revenue Contribution"
        data={(data?.segment_revenue as Record<string, unknown>[]) ?? []}
        bars={[{ key: 'revenue', label: 'Revenue' }]}
        xKey="segment"
        height={280}
        loading={isLoading}
      />
    </div>
  );
}

function CLVPage({ datasetId }: { datasetId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ANALYTICS_CLV(datasetId),
    queryFn: () => analyticsApi.clv(datasetId),
    enabled: !!datasetId,
  });
  return (
    <>
      <KPIGrid kpis={(data?.kpis as KPICard[]) ?? []} loading={isLoading} columns={3} />
      <AreaChartWidget
        title="CLV Distribution"
        data={(data?.clv_distribution as Record<string, unknown>[]) ?? []}
        areas={[{ key: 'clv', label: 'Customer Lifetime Value' }]}
        xKey="bucket"
        height={280}
        loading={isLoading}
      />
    </>
  );
}

export function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('eda');
  const [datasetId, setDatasetId] = useState('');

  const tabContent: Record<string, React.ReactNode> = {
    eda: <EDAPage />,
    customer: <CustomerAnalyticsPage />,
    revenue: <RevenueAnalyticsPage />,
    retention: datasetId ? <RetentionPage datasetId={datasetId} /> : <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" />,
    cohort: <EmptyState icon={<BarChart3 size={48} />} title="Cohort Analysis" description="Select a dataset to view cohort analysis." />,
    rfm: datasetId ? <RFMPage datasetId={datasetId} /> : <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" />,
    clv: datasetId ? <CLVPage datasetId={datasetId} /> : <EmptyState icon={<BarChart3 size={48} />} title="Select a dataset" />,
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
          <p className="text-sm text-gray-500">Comprehensive business and customer intelligence</p>
        </div>
        <DatasetSelector value={datasetId} onChange={setDatasetId} />
      </div>
      <Tabs tabs={ANALYTICS_TABS} activeTab={activeTab} onChange={setActiveTab} />
      <div>{tabContent[activeTab]}</div>
    </div>
  );
}
