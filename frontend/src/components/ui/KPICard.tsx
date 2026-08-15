import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, formatMetricValue } from '@/utils';
import type { KPICard } from '@/types';
import { Skeleton } from '@/components/ui/Card';

interface KPICardProps {
  kpi: KPICard;
  loading?: boolean;
}

export function KPICardWidget({ kpi, loading }: KPICardProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <Skeleton className="mb-3 h-4 w-24" />
        <Skeleton className="mb-2 h-8 w-32" />
        <Skeleton className="h-3 w-20" />
      </div>
    );
  }

  const trendIcon =
    kpi.trend === 'up' ? <TrendingUp size={14} /> :
    kpi.trend === 'down' ? <TrendingDown size={14} /> :
    <Minus size={14} />;

  const trendColor =
    kpi.trend === 'up' ? 'text-green-600 dark:text-green-400' :
    kpi.trend === 'down' ? 'text-red-600 dark:text-red-400' :
    'text-gray-500 dark:text-gray-400';

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-card dark:border-gray-700 dark:bg-gray-800">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {kpi.label}
      </p>
      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
        {formatMetricValue(kpi.value, kpi.format)}
      </p>
      {kpi.change !== undefined && (
        <div className={cn('mt-2 flex items-center gap-1 text-xs font-medium', trendColor)}>
          {trendIcon}
          <span>
            {kpi.change > 0 ? '+' : ''}{kpi.change.toFixed(1)}%
            {kpi.change_period && <span className="ml-1 font-normal text-gray-400">{kpi.change_period}</span>}
          </span>
        </div>
      )}
    </div>
  );
}

interface KPIGridProps {
  kpis: KPICard[];
  loading?: boolean;
  columns?: 2 | 3 | 4;
}

export function KPIGrid({ kpis, loading, columns = 4 }: KPIGridProps) {
  const colClass = { 2: 'grid-cols-1 sm:grid-cols-2', 3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3', 4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4' }[columns];
  const items = loading ? Array.from({ length: columns }, (_, i) => ({ label: '', value: 0, id: i })) : kpis;
  return (
    <div className={cn('grid gap-4', colClass)}>
      {items.map((kpi, i) => (
        <KPICardWidget key={loading ? i : kpi.label} kpi={kpi as KPICard} loading={loading} />
      ))}
    </div>
  );
}