import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  type TooltipProps,
} from 'recharts';
import { CHART_COLORS } from '@/constants';
import { cn } from '@/utils';
import { Spinner } from '@/components/ui/Card';

interface ChartContainerProps {
  title?: string;
  description?: string;
  height?: number;
  loading?: boolean;
  children: React.ReactNode;
  className?: string;
  toolbar?: React.ReactNode;
}

export function ChartContainer({ title, description, height = 300, loading, children, className, toolbar }: ChartContainerProps) {
  return (
    <div className={cn('rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800', className)}>
      {(title || toolbar) && (
        <div className="mb-4 flex items-start justify-between">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h3>}
            {description && <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{description}</p>}
          </div>
          {toolbar}
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center" style={{ height }}>
          <Spinner />
        </div>
      ) : (
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            {children as React.ReactElement}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: 'var(--tooltip-bg, #1e293b)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#f1f5f9',
  },
  itemStyle: { color: '#cbd5e1' },
  labelStyle: { color: '#f1f5f9', fontWeight: 600 },
};

interface LineChartProps {
  data: Record<string, unknown>[];
  lines: { key: string; label: string; color?: string }[];
  xKey: string;
  title?: string;
  description?: string;
  height?: number;
  loading?: boolean;
}

export function LineChartWidget({ data, lines, xKey, title, description, height, loading }: LineChartProps) {
  return (
    <ChartContainer title={title} description={description} height={height} loading={loading}>
      <LineChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {lines.map((l, i) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.label}
            stroke={l.color ?? CHART_COLORS[i % CHART_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ChartContainer>
  );
}

interface BarChartProps {
  data: Record<string, unknown>[];
  bars: { key: string; label: string; color?: string }[];
  xKey: string;
  title?: string;
  description?: string;
  height?: number;
  loading?: boolean;
  stacked?: boolean;
}

export function BarChartWidget({ data, bars, xKey, title, description, height, loading, stacked }: BarChartProps) {
  return (
    <ChartContainer title={title} description={description} height={height} loading={loading}>
      <BarChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {bars.map((b, i) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.label}
            fill={b.color ?? CHART_COLORS[i % CHART_COLORS.length]}
            stackId={stacked ? 'stack' : undefined}
            radius={stacked ? undefined : [3, 3, 0, 0]}
          />
        ))}
      </BarChart>
    </ChartContainer>
  );
}

interface AreaChartProps {
  data: Record<string, unknown>[];
  areas: { key: string; label: string; color?: string }[];
  xKey: string;
  title?: string;
  description?: string;
  height?: number;
  loading?: boolean;
}

export function AreaChartWidget({ data, areas, xKey, title, description, height, loading }: AreaChartProps) {
  return (
    <ChartContainer title={title} description={description} height={height} loading={loading}>
      <AreaChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <defs>
          {areas.map((a) => (
            <linearGradient key={a.key} id={`grad-${a.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={a.color ?? CHART_COLORS[0]} stopOpacity={0.3} />
              <stop offset="95%" stopColor={a.color ?? CHART_COLORS[0]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {areas.map((a) => (
          <Area
            key={a.key}
            type="monotone"
            dataKey={a.key}
            name={a.label}
            stroke={a.color ?? CHART_COLORS[0]}
            fill={`url(#grad-${a.key})`}
            strokeWidth={2}
          />
        ))}
      </AreaChart>
    </ChartContainer>
  );
}

interface PieChartProps {
  data: { name: string; value: number }[];
  title?: string;
  description?: string;
  height?: number;
  loading?: boolean;
  donut?: boolean;
}

const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-lg">
      <p className="font-semibold">{payload[0].name}</p>
      <p>{payload[0].value?.toLocaleString()}</p>
    </div>
  );
};

export function PieChartWidget({ data, title, description, height, loading, donut }: PieChartProps) {
  return (
    <ChartContainer title={title} description={description} height={height} loading={loading}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={donut ? '55%' : 0}
          outerRadius="75%"
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((_entry, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ChartContainer>
  );
}