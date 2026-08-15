import apiClient, { createUploadClient } from './client';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  PaginatedResponse,
  PaginationParams,
  Dataset,
  DatasetPreview,
  DashboardOverview,
  KPICard,
  ActivityItem,
  MLModel,
  TrainRequest,
  Experiment,
  PredictionResult,
  DriftReport,
  Report,
  ReportFormat,
  Notification,
  BackgroundJob,
  AuditEvent,
  SearchResponse,
  Organization,
  Role,
} from '@/types';

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    apiClient.post<User>('/auth/register', data).then((r) => r.data),

  logout: () => apiClient.post('/auth/logout').then((r) => r.data),

  me: () => apiClient.get<User>('/auth/me').then((r) => r.data),

  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }).then((r) => r.data),

  resetPassword: (token: string, password: string) =>
    apiClient.post('/auth/reset-password', { token, password }).then((r) => r.data),

  verifyEmail: (token: string) =>
    apiClient.post('/auth/verify-email', { token }).then((r) => r.data),

  changePassword: (current_password: string, new_password: string) =>
    apiClient.post('/auth/change-password', { current_password, new_password }).then((r) => r.data),
};

// ─── Datasets ─────────────────────────────────────────────────────────────────

export const datasetsApi = {
  list: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<Dataset>>('/datasets', { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Dataset>(`/datasets/${id}`).then((r) => r.data),

  upload: (file: File, name: string, description: string, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append('file', file);
    form.append('name', name);
    form.append('description', description);
    return createUploadClient(onProgress)
      .post<Dataset>('/datasets/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data);
  },

  preview: (id: string, rows = 100) =>
    apiClient.get<DatasetPreview>(`/datasets/${id}/preview`, { params: { rows } }).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/datasets/${id}`).then((r) => r.data),

  versions: (id: string) =>
    apiClient.get<Dataset[]>(`/datasets/${id}/versions`).then((r) => r.data),
};

// ─── Dashboard ────────────────────────────────────────────────────────────────

export const dashboardApi = {
  overview: () => apiClient.get<DashboardOverview>('/dashboard/overview').then((r) => r.data),
  kpis: () => apiClient.get<KPICard[]>('/dashboard/kpis').then((r) => r.data),
  activity: (limit = 20) =>
    apiClient.get<ActivityItem[]>('/dashboard/activity', { params: { limit } }).then((r) => r.data),
  widget: (type: string, params?: Record<string, unknown>) =>
    apiClient.get(`/dashboard/widgets/${type}`, { params }).then((r) => r.data),
};

// ─── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  customer: (datasetId: string) =>
    apiClient.get('/analytics/customer', { params: { dataset_id: datasetId } }).then((r) => r.data),
  revenue: (datasetId: string) =>
    apiClient.get('/analytics/revenue', { params: { dataset_id: datasetId } }).then((r) => r.data),
  retention: (datasetId: string) =>
    apiClient.get('/analytics/retention', { params: { dataset_id: datasetId } }).then((r) => r.data),
  cohort: (datasetId: string) =>
    apiClient.get('/analytics/cohort', { params: { dataset_id: datasetId } }).then((r) => r.data),
  rfm: (datasetId: string) =>
    apiClient.get('/analytics/rfm', { params: { dataset_id: datasetId } }).then((r) => r.data),
  clv: (datasetId: string) =>
    apiClient.get('/analytics/clv', { params: { dataset_id: datasetId } }).then((r) => r.data),
  eda: (datasetId: string) =>
    apiClient.get('/analytics/eda', { params: { dataset_id: datasetId } }).then((r) => r.data),
  correlation: (datasetId: string) =>
    apiClient.get('/analytics/correlation', { params: { dataset_id: datasetId } }).then((r) => r.data),
  forecast: (datasetId: string, params?: Record<string, unknown>) =>
    apiClient.get('/analytics/forecast', { params: { dataset_id: datasetId, ...params } }).then((r) => r.data),
};

// ─── AI ───────────────────────────────────────────────────────────────────────

export const aiApi = {
  listModels: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<MLModel>>('/ai/models', { params }).then((r) => r.data),

  getModel: (id: string) => apiClient.get<MLModel>(`/ai/models/${id}`).then((r) => r.data),

  train: (data: TrainRequest) =>
    apiClient.post<{ job_id: string; model_id: string }>('/ai/train', data).then((r) => r.data),

  activateModel: (id: string) =>
    apiClient.post<MLModel>(`/ai/models/${id}/activate`).then((r) => r.data),

  archiveModel: (id: string) =>
    apiClient.post<MLModel>(`/ai/models/${id}/archive`).then((r) => r.data),

  predict: (modelId: string, inputData: Record<string, unknown>) =>
    apiClient.post<PredictionResult>('/ai/predict', { model_id: modelId, input_data: inputData }).then((r) => r.data),

  batchPredict: (modelId: string, datasetId: string) =>
    apiClient.post<{ job_id: string }>('/ai/predict/batch', { model_id: modelId, dataset_id: datasetId }).then((r) => r.data),

  getMetrics: (modelId: string) =>
    apiClient.get('/ai/metrics', { params: { model_id: modelId } }).then((r) => r.data),

  explain: (modelId: string, inputData: Record<string, unknown>) =>
    apiClient.post('/ai/explain', { model_id: modelId, input_data: inputData }).then((r) => r.data),

  getDrift: (modelId: string) =>
    apiClient.get<DriftReport>('/ai/drift', { params: { model_id: modelId } }).then((r) => r.data),

  getMonitoring: (modelId: string) =>
    apiClient.get('/ai/monitoring', { params: { model_id: modelId } }).then((r) => r.data),

  listExperiments: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<Experiment>>('/ai/experiments', { params }).then((r) => r.data),

  trainingHistory: (modelId: string) =>
    apiClient.get('/ai/training-history', { params: { model_id: modelId } }).then((r) => r.data),

  churnPrediction: (datasetId: string) =>
    apiClient.post('/ai/business/churn', { dataset_id: datasetId }).then((r) => r.data),

  segmentation: (datasetId: string) =>
    apiClient.post('/ai/business/segmentation', { dataset_id: datasetId }).then((r) => r.data),

  clvPrediction: (datasetId: string) =>
    apiClient.post('/ai/business/clv', { dataset_id: datasetId }).then((r) => r.data),

  revenueForecast: (datasetId: string) =>
    apiClient.post('/ai/business/revenue-forecast', { dataset_id: datasetId }).then((r) => r.data),

  salesForecast: (datasetId: string) =>
    apiClient.post('/ai/business/sales-forecast', { dataset_id: datasetId }).then((r) => r.data),

  recommendations: (datasetId: string) =>
    apiClient.post('/ai/business/recommendations', { dataset_id: datasetId }).then((r) => r.data),
};

// ─── Reports ──────────────────────────────────────────────────────────────────

export const reportsApi = {
  list: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<Report>>('/reports', { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Report>(`/reports/${id}`).then((r) => r.data),

  generate: (data: { name: string; report_type: string; format: ReportFormat; parameters?: Record<string, unknown> }) =>
    apiClient.post<{ job_id: string; report_id: string }>('/reports/generate', data).then((r) => r.data),

  download: (id: string) =>
    apiClient.get(`/reports/download/${id}`, { responseType: 'blob' }).then((r) => r.data as Blob),

  delete: (id: string) => apiClient.delete(`/reports/${id}`).then((r) => r.data),
};

// ─── Exports ──────────────────────────────────────────────────────────────────

export const exportsApi = {
  create: (data: { resource_type: string; resource_id: string; format: string }) =>
    apiClient.post('/exports', data).then((r) => r.data),

  get: (id: string) => apiClient.get(`/exports/${id}`).then((r) => r.data),

  download: (id: string) =>
    apiClient.get(`/exports/${id}/download`, { responseType: 'blob' }).then((r) => r.data as Blob),
};

// ─── Notifications ────────────────────────────────────────────────────────────

export const notificationsApi = {
  list: (params?: { unread_only?: boolean } & PaginationParams) =>
    apiClient.get<PaginatedResponse<Notification>>('/notifications', { params }).then((r) => r.data),

  unreadCount: () =>
    apiClient.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),

  markRead: (id: string) =>
    apiClient.patch<Notification>(`/notifications/${id}/read`).then((r) => r.data),

  markAllRead: () => apiClient.patch('/notifications/read-all').then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/notifications/${id}`).then((r) => r.data),
};

// ─── Jobs ─────────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<BackgroundJob>>('/jobs', { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<BackgroundJob>(`/jobs/${id}`).then((r) => r.data),

  cancel: (id: string) => apiClient.delete(`/jobs/${id}`).then((r) => r.data),
};

// ─── Audit ────────────────────────────────────────────────────────────────────

export const auditApi = {
  list: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<AuditEvent>>('/audit', { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<AuditEvent>(`/audit/${id}`).then((r) => r.data),

  activity: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<ActivityItem>>('/audit/activity', { params }).then((r) => r.data),
};

// ─── Search ───────────────────────────────────────────────────────────────────

export const searchApi = {
  search: (query: string, types?: string[]) =>
    apiClient
      .get<SearchResponse>('/search', { params: { q: query, types: types?.join(',') } })
      .then((r) => r.data),
};

// ─── Admin ────────────────────────────────────────────────────────────────────

export const adminApi = {
  listUsers: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<User>>('/users', { params }).then((r) => r.data),

  getUser: (id: string) => apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  updateUser: (id: string, data: Partial<User>) =>
    apiClient.patch<User>(`/users/${id}`, data).then((r) => r.data),

  deactivateUser: (id: string) =>
    apiClient.post<User>(`/users/${id}/deactivate`).then((r) => r.data),

  listOrganizations: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<Organization>>('/organizations', { params }).then((r) => r.data),

  listRoles: () => apiClient.get<Role[]>('/roles').then((r) => r.data),

  createRole: (data: { name: string; codename: string; permissions: string[] }) =>
    apiClient.post<Role>('/roles', data).then((r) => r.data),

  updateRole: (id: string, data: Partial<Role>) =>
    apiClient.patch<Role>(`/roles/${id}`, data).then((r) => r.data),
};
