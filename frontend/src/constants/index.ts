export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',
  UNAUTHORIZED: '/unauthorized',
  FORBIDDEN: '/forbidden',

  DASHBOARD: '/dashboard',

  DATASETS: '/datasets',
  DATASET_DETAIL: '/datasets/:id',
  DATASET_UPLOAD: '/datasets/upload',

  ANALYTICS: '/analytics',
  ANALYTICS_EDA: '/analytics/eda',
  ANALYTICS_BUSINESS: '/analytics/business',
  ANALYTICS_CUSTOMER: '/analytics/customer',
  ANALYTICS_REVENUE: '/analytics/revenue',
  ANALYTICS_RETENTION: '/analytics/retention',
  ANALYTICS_COHORT: '/analytics/cohort',
  ANALYTICS_RFM: '/analytics/rfm',
  ANALYTICS_CLV: '/analytics/clv',

  AI: '/ai',
  AI_MODELS: '/ai/models',
  AI_TRAIN: '/ai/train',
  AI_EXPERIMENTS: '/ai/experiments',
  AI_PREDICTIONS: '/ai/predictions',
  AI_DRIFT: '/ai/drift',

  REPORTS: '/reports',
  REPORT_DETAIL: '/reports/:id',

  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_ORGANIZATIONS: '/admin/organizations',
  ADMIN_ROLES: '/admin/roles',
  ADMIN_AUDIT: '/admin/audit',
  ADMIN_SETTINGS: '/admin/settings',

  SETTINGS: '/settings',
  SETTINGS_PROFILE: '/settings/profile',
  SETTINGS_SECURITY: '/settings/security',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
} as const;

export const QUERY_KEYS = {
  ME: ['me'],
  USERS: ['users'],
  ORGANIZATIONS: ['organizations'],
  ROLES: ['roles'],

  DATASETS: ['datasets'],
  DATASET: (id: string) => ['datasets', id],
  DATASET_PREVIEW: (id: string) => ['datasets', id, 'preview'],

  DASHBOARD_OVERVIEW: ['dashboard', 'overview'],
  DASHBOARD_KPIS: ['dashboard', 'kpis'],
  DASHBOARD_ACTIVITY: ['dashboard', 'activity'],

  ANALYTICS_CUSTOMER: (datasetId: string) => ['analytics', 'customer', datasetId],
  ANALYTICS_REVENUE: (datasetId: string) => ['analytics', 'revenue', datasetId],
  ANALYTICS_RETENTION: (datasetId: string) => ['analytics', 'retention', datasetId],
  ANALYTICS_COHORT: (datasetId: string) => ['analytics', 'cohort', datasetId],
  ANALYTICS_RFM: (datasetId: string) => ['analytics', 'rfm', datasetId],
  ANALYTICS_CLV: (datasetId: string) => ['analytics', 'clv', datasetId],
  ANALYTICS_EDA: (datasetId: string) => ['analytics', 'eda', datasetId],

  AI_MODELS: ['ai', 'models'],
  AI_MODEL: (id: string) => ['ai', 'models', id],
  AI_EXPERIMENTS: ['ai', 'experiments'],
  AI_METRICS: (modelId: string) => ['ai', 'models', modelId, 'metrics'],
  AI_DRIFT: (modelId: string) => ['ai', 'models', modelId, 'drift'],
  AI_MONITORING: (modelId: string) => ['ai', 'models', modelId, 'monitoring'],

  REPORTS: ['reports'],
  REPORT: (id: string) => ['reports', id],

  NOTIFICATIONS: ['notifications'],
  NOTIFICATION_COUNT: ['notifications', 'count'],

  JOBS: ['jobs'],
  JOB: (id: string) => ['jobs', id],

  AUDIT: ['audit'],
  ACTIVITY: ['activity'],

  SEARCH: (query: string) => ['search', query],
} as const;

export const PERMISSIONS = {
  ANALYTICS_VIEW: 'analytics.view',
  AI_TRAIN: 'ai.train',
  AI_PREDICT: 'ai.predict',
  AI_VIEW: 'ai.view',
  AI_MANAGE: 'ai.manage',
  REPORTS_GENERATE: 'reports.generate',
  REPORTS_VIEW: 'reports.view',
  REPORTS_DELETE: 'reports.delete',
  EXPORTS_CREATE: 'exports.create',
  EXPORTS_VIEW: 'exports.view',
  JOBS_VIEW: 'jobs.view',
  JOBS_MANAGE: 'jobs.manage',
  AUDIT_VIEW: 'audit.view',
  USERS_MANAGE: 'users.manage',
  ROLES_MANAGE: 'roles.manage',
  SETTINGS_MANAGE: 'settings.manage',
} as const;

export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;
export const DEFAULT_PAGE_SIZE = 25;

export const DATE_FORMATS = {
  DISPLAY: 'MMM d, yyyy',
  DISPLAY_WITH_TIME: 'MMM d, yyyy HH:mm',
  ISO: "yyyy-MM-dd'T'HH:mm:ss",
  SHORT: 'MM/dd/yyyy',
} as const;

export const CHART_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
] as const;

export const TASK_TYPE_LABELS: Record<string, string> = {
  classification: 'Classification',
  regression: 'Regression',
  clustering: 'Clustering',
};

export const MODEL_STATUS_COLORS: Record<string, string> = {
  training: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  ready: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  archived: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

export const JOB_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-yellow-100 text-yellow-800',
};
