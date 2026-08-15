// ─── Auth ────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  organization_id: string;
  roles: Role[];
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  name: string;
  codename: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  codename: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: 'free' | 'starter' | 'professional' | 'enterprise';
  is_active: boolean;
  created_at: string;
}

// ─── Common API ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ─── Dataset ─────────────────────────────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  file_name: string;
  file_size: number;
  file_type: string;
  row_count?: number;
  column_count?: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  version: number;
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetColumn {
  name: string;
  dtype: string;
  nullable: boolean;
  unique_count: number;
  null_count: number;
  sample_values: unknown[];
}

export interface DatasetPreview {
  columns: DatasetColumn[];
  rows: Record<string, unknown>[];
  total_rows: number;
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface KPICard {
  label: string;
  value: number | string;
  change?: number;
  change_period?: string;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'number' | 'currency' | 'percent' | 'duration';
  icon?: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  [key: string]: unknown;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
  [key: string]: unknown;
}

export interface DashboardOverview {
  kpis: KPICard[];
  recent_activity: ActivityItem[];
  dataset_count: number;
  model_count: number;
  report_count: number;
}

export interface ActivityItem {
  id: string;
  type: string;
  description: string;
  user_name: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

// ─── AI / ML ─────────────────────────────────────────────────────────────────

export type ModelStatus = 'training' | 'ready' | 'active' | 'archived' | 'failed';
export type TaskType = 'classification' | 'regression' | 'clustering';

export interface MLModel {
  id: string;
  name: string;
  description?: string;
  task_type: TaskType;
  algorithm: string;
  status: ModelStatus;
  version: number;
  dataset_id: string;
  target_column?: string;
  feature_columns: string[];
  metrics?: ModelMetrics;
  created_at: string;
  updated_at: string;
}

export interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  roc_auc?: number;
  rmse?: number;
  mae?: number;
  r2?: number;
  silhouette_score?: number;
  [key: string]: number | undefined;
}

export interface TrainRequest {
  name: string;
  description?: string;
  dataset_id: string;
  task_type: TaskType;
  target_column?: string;
  feature_columns?: string[];
  algorithm?: string;
  hyperparameter_opt?: {
    method: 'grid' | 'random' | 'optuna';
    n_trials?: number;
  };
  cross_validation?: {
    strategy: 'kfold' | 'stratified' | 'timeseries';
    n_splits?: number;
  };
}

export interface Experiment {
  id: string;
  name: string;
  model_id: string;
  status: 'running' | 'completed' | 'failed';
  metrics?: ModelMetrics;
  params?: Record<string, unknown>;
  created_at: string;
}

export interface PredictionResult {
  id: string;
  model_id: string;
  input_data: Record<string, unknown>;
  prediction: unknown;
  probability?: number;
  confidence?: number;
  created_at: string;
}

export interface DriftReport {
  id: string;
  model_id: string;
  drift_detected: boolean;
  drift_score: number;
  feature_drift: Record<string, number>;
  created_at: string;
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export type ReportFormat = 'pdf' | 'excel' | 'csv' | 'json';
export type ReportStatus = 'pending' | 'generating' | 'ready' | 'failed';

export interface Report {
  id: string;
  name: string;
  report_type: string;
  format: ReportFormat;
  status: ReportStatus;
  file_path?: string;
  file_size?: number;
  parameters?: Record<string, unknown>;
  created_by: string;
  created_at: string;
}

// ─── Notifications ───────────────────────────────────────────────────────────

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

// ─── Jobs ────────────────────────────────────────────────────────────────────

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface BackgroundJob {
  id: string;
  job_type: string;
  status: JobStatus;
  progress?: number;
  result?: unknown;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

// ─── Audit ───────────────────────────────────────────────────────────────────

export interface AuditEvent {
  id: string;
  event_type: string;
  resource_type: string;
  resource_id?: string;
  user_id: string;
  user_email: string;
  ip_address?: string;
  details?: Record<string, unknown>;
  created_at: string;
}

// ─── Search ──────────────────────────────────────────────────────────────────

export interface SearchResult {
  id: string;
  type: 'dataset' | 'report' | 'model' | 'user' | 'audit';
  title: string;
  description?: string;
  url: string;
  score: number;
  created_at: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  suggestions: string[];
}
