import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { createColumnHelper } from '@tanstack/react-table';
import toast from 'react-hot-toast';
import { Play, Archive, CheckCircle, AlertTriangle } from 'lucide-react';
import { aiApi, datasetsApi } from '@/api';
import { QUERY_KEYS, TASK_TYPE_LABELS, MODEL_STATUS_COLORS } from '@/constants';
import { formatDate, formatRelativeTime, cn } from '@/utils';
import type { MLModel, Experiment, TrainRequest } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input, Select, Textarea } from '@/components/ui/Input';
import { Card, Badge, EmptyState, Skeleton } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { Tabs } from '@/components/ui/Tabs';
import { BarChartWidget } from '@/components/charts';

// ─── Model List ───────────────────────────────────────────────────────────────

const modelColHelper = createColumnHelper<MLModel>();

const modelColumns = [
  modelColHelper.accessor('name', {
    header: 'Model',
    cell: (i) => (
      <div>
        <p className="font-medium text-gray-900 dark:text-gray-100">{i.getValue()}</p>
        <p className="text-xs text-gray-400">{i.row.original.algorithm}</p>
      </div>
    ),
  }),
  modelColHelper.accessor('task_type', {
    header: 'Task',
    cell: (i) => <Badge variant="info">{TASK_TYPE_LABELS[i.getValue()]}</Badge>,
  }),
  modelColHelper.accessor('status', {
    header: 'Status',
    cell: (i) => (
      <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', MODEL_STATUS_COLORS[i.getValue()])}>
        {i.getValue()}
      </span>
    ),
  }),
  modelColHelper.accessor('metrics', {
    header: 'Accuracy',
    cell: (i) => {
      const m = i.getValue();
      const val = m?.accuracy ?? m?.r2 ?? m?.silhouette_score;
      return val !== undefined ? `${(val * 100).toFixed(1)}%` : '—';
    },
  }),
  modelColHelper.accessor('version', { header: 'Version', cell: (i) => `v${i.getValue()}` }),
  modelColHelper.accessor('created_at', { header: 'Created', cell: (i) => formatRelativeTime(i.getValue()) }),
];

export function AIModelsPage() {
  const [trainOpen, setTrainOpen] = useState(false);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.AI_MODELS,
    queryFn: () => aiApi.listModels({ page_size: 100 }),
  });

  const activateMutation = useMutation({
    mutationFn: aiApi.activateModel,
    onSuccess: () => { toast.success('Model activated'); qc.invalidateQueries({ queryKey: QUERY_KEYS.AI_MODELS }); },
  });

  const archiveMutation = useMutation({
    mutationFn: aiApi.archiveModel,
    onSuccess: () => { toast.success('Model archived'); qc.invalidateQueries({ queryKey: QUERY_KEYS.AI_MODELS }); },
  });

  const columnsWithActions = [
    ...modelColumns,
    modelColHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: (i) => (
        <div className="flex gap-1">
          {i.row.original.status === 'ready' && (
            <Button size="xs" variant="ghost" leftIcon={<CheckCircle size={12} />}
              onClick={() => activateMutation.mutate(i.row.original.id)}>
              Activate
            </Button>
          )}
          {i.row.original.status === 'active' && (
            <Button size="xs" variant="ghost" leftIcon={<Archive size={12} />}
              onClick={() => archiveMutation.mutate(i.row.original.id)}>
              Archive
            </Button>
          )}
        </div>
      ),
    }),
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">AI Models</h1>
          <p className="text-sm text-gray-500">Train, manage, and deploy machine learning models</p>
        </div>
        <Button leftIcon={<Play size={16} />} onClick={() => setTrainOpen(true)}>Train Model</Button>
      </div>

      <DataTable
        data={data?.items ?? []}
        columns={columnsWithActions}
        loading={isLoading}
        searchable
        searchPlaceholder="Search models…"
        emptyTitle="No models yet"
        emptyDescription="Train your first model to get started with AI predictions."
      />

      <TrainModelModal open={trainOpen} onClose={() => setTrainOpen(false)} />
    </div>
  );
}

// ─── Train Model Modal ────────────────────────────────────────────────────────

const trainSchema = z.object({
  name: z.string().min(1, 'Model name is required'),
  description: z.string().optional(),
  dataset_id: z.string().min(1, 'Select a dataset'),
  task_type: z.enum(['classification', 'regression', 'clustering']),
  target_column: z.string().optional(),
  algorithm: z.string().optional(),
});

type TrainFormData = z.infer<typeof trainSchema>;

import { Modal } from '@/components/ui/Modal';

function TrainModelModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();

  const { data: datasets } = useQuery({
    queryKey: QUERY_KEYS.DATASETS,
    queryFn: () => datasetsApi.list({ page_size: 100 }),
  });

  const { register, handleSubmit, watch, formState: { errors } } = useForm<TrainFormData>({
    resolver: zodResolver(trainSchema),
    defaultValues: { task_type: 'classification' },
  });

  const taskType = watch('task_type');

  const mutation = useMutation({
    mutationFn: (d: TrainFormData) => aiApi.train(d as TrainRequest),
    onSuccess: () => {
      toast.success('Training started! Check the Jobs panel for progress.');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.AI_MODELS });
      onClose();
    },
    onError: () => toast.error('Failed to start training'),
  });

  const datasetOptions = (datasets?.items ?? [])
    .filter((d) => d.status === 'ready')
    .map((d) => ({ value: d.id, label: d.name }));

  const algorithmOptions: Record<string, { value: string; label: string }[]> = {
    classification: [
      { value: 'random_forest', label: 'Random Forest' },
      { value: 'gradient_boosting', label: 'Gradient Boosting' },
      { value: 'logistic_regression', label: 'Logistic Regression' },
      { value: 'xgboost', label: 'XGBoost' },
      { value: 'lightgbm', label: 'LightGBM' },
    ],
    regression: [
      { value: 'random_forest_regressor', label: 'Random Forest' },
      { value: 'gradient_boosting_regressor', label: 'Gradient Boosting' },
      { value: 'linear_regression', label: 'Linear Regression' },
      { value: 'xgboost_regressor', label: 'XGBoost' },
    ],
    clustering: [
      { value: 'kmeans', label: 'K-Means' },
      { value: 'dbscan', label: 'DBSCAN' },
      { value: 'hierarchical', label: 'Hierarchical' },
    ],
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Train New Model"
      description="Configure and launch a new ML training job"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" loading={mutation.isPending} onClick={handleSubmit((d) => mutation.mutate(d))}>
            Start Training
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Input label="Model name" placeholder="e.g. Churn Predictor v1" error={errors.name?.message} {...register('name')} id="model-name" required />
        <Textarea label="Description (optional)" placeholder="What does this model predict?" {...register('description')} id="model-desc" />
        <Select
          label="Dataset" id="model-dataset" required
          options={datasetOptions} placeholder="Select dataset…"
          error={errors.dataset_id?.message} {...register('dataset_id')}
        />
        <Select
          label="Task type" id="model-task" required
          options={Object.entries(TASK_TYPE_LABELS).map(([v, l]) => ({ value: v, label: l }))}
          error={errors.task_type?.message} {...register('task_type')}
        />
        {taskType !== 'clustering' && (
          <Input label="Target column" placeholder="e.g. churn, revenue" error={errors.target_column?.message} {...register('target_column')} id="model-target" />
        )}
        <Select
          label="Algorithm (optional)" id="model-algo"
          options={algorithmOptions[taskType] ?? []}
          placeholder="Auto-select best algorithm"
          {...register('algorithm')}
        />
      </div>
    </Modal>
  );
}

// ─── Experiments Page ─────────────────────────────────────────────────────────

const expColHelper = createColumnHelper<Experiment>();

export function ExperimentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.AI_EXPERIMENTS,
    queryFn: () => aiApi.listExperiments({ page_size: 100 }),
  });

  const columns = [
    expColHelper.accessor('name', { header: 'Experiment' }),
    expColHelper.accessor('status', {
      header: 'Status',
      cell: (i) => {
        const colors: Record<string, string> = { completed: 'success', running: 'info', failed: 'danger' };
        return <Badge variant={colors[i.getValue()] as 'success'}>{i.getValue()}</Badge>;
      },
    }),
    expColHelper.accessor('metrics', {
      header: 'Best Metric',
      cell: (i) => {
        const m = i.getValue();
        if (!m) return '—';
        const val = m.accuracy ?? m.r2 ?? m.f1_score;
        return val !== undefined ? `${(val * 100).toFixed(2)}%` : '—';
      },
    }),
    expColHelper.accessor('created_at', { header: 'Started', cell: (i) => formatRelativeTime(i.getValue()) }),
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Experiments</h1>
        <p className="text-sm text-gray-500">Track and compare training experiments</p>
      </div>
      <DataTable
        data={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        searchable
        emptyTitle="No experiments yet"
        emptyDescription="Train a model to create your first experiment."
      />
    </div>
  );
}

// ─── Drift Dashboard ──────────────────────────────────────────────────────────

export function DriftDashboardPage() {
  const { data: models } = useQuery({
    queryKey: QUERY_KEYS.AI_MODELS,
    queryFn: () => aiApi.listModels({ page_size: 100 }),
  });

  const [selectedModel, setSelectedModel] = useState('');

  const { data: drift, isLoading } = useQuery({
    queryKey: QUERY_KEYS.AI_DRIFT(selectedModel),
    queryFn: () => aiApi.getDrift(selectedModel),
    enabled: !!selectedModel,
  });

  const activeModels = (models?.items ?? []).filter((m) => m.status === 'active');

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Drift Detection</h1>
          <p className="text-sm text-gray-500">Monitor data and concept drift for deployed models</p>
        </div>
        <Select
          id="drift-model"
          label="Model"
          options={activeModels.map((m) => ({ value: m.id, label: m.name }))}
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          placeholder="Select active model…"
          className="max-w-xs"
        />
      </div>

      {!selectedModel ? (
        <EmptyState icon={<AlertTriangle size={48} />} title="Select a model" description="Choose an active model to view drift analysis." />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      ) : drift ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <p className="text-xs text-gray-500">Drift Detected</p>
              <p className={cn('mt-2 text-2xl font-bold', drift.drift_detected ? 'text-red-600' : 'text-green-600')}>
                {drift.drift_detected ? 'Yes' : 'No'}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Drift Score</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
                {(drift.drift_score * 100).toFixed(1)}%
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Last Checked</p>
              <p className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                {formatDate(drift.created_at)}
              </p>
            </Card>
          </div>
          <BarChartWidget
            title="Feature Drift Scores"
            data={Object.entries(drift.feature_drift).map(([feature, score]) => ({ feature, score }))}
            bars={[{ key: 'score', label: 'Drift Score', color: '#ef4444' }]}
            xKey="feature"
            height={280}
          />
        </>
      ) : null}
    </div>
  );
}

// ─── AI Hub (tabbed) ──────────────────────────────────────────────────────────

const AI_TABS = [
  { id: 'models', label: 'Models' },
  { id: 'experiments', label: 'Experiments' },
  { id: 'drift', label: 'Drift' },
];

export function AIPage() {
  const [activeTab, setActiveTab] = useState('models');
  const tabContent: Record<string, React.ReactNode> = {
    models: <AIModelsPage />,
    experiments: <ExperimentsPage />,
    drift: <DriftDashboardPage />,
  };
  return (
    <div className="flex flex-col gap-6">
      <Tabs tabs={AI_TABS} activeTab={activeTab} onChange={setActiveTab} />
      {tabContent[activeTab]}
    </div>
  );
}
