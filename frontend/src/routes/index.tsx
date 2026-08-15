import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { ROUTES, PERMISSIONS } from '@/constants';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { Spinner } from '@/components/ui/Card';

const UnauthorizedPage = lazy(() =>
  import('@/features/auth/AuthPages').then((m) => ({ default: m.UnauthorizedPage })),
);
const ForbiddenPage = lazy(() =>
  import('@/features/auth/AuthPages').then((m) => ({ default: m.ForbiddenPage })),
);
const DashboardPage = lazy(() =>
  import('@/features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })),
);
const DatasetsPage = lazy(() =>
  import('@/features/datasets/DatasetPages').then((m) => ({ default: m.DatasetsPage })),
);
const DatasetDetailPage = lazy(() =>
  import('@/features/datasets/DatasetPages').then((m) => ({ default: m.DatasetDetailPage })),
);
const AnalyticsPage = lazy(() =>
  import('@/features/analytics/AnalyticsPages').then((m) => ({ default: m.AnalyticsPage })),
);
const AIPage = lazy(() =>
  import('@/features/ai/AIPages').then((m) => ({ default: m.AIPage })),
);
const AIModelsPage = lazy(() =>
  import('@/features/ai/AIPages').then((m) => ({ default: m.AIModelsPage })),
);
const ExperimentsPage = lazy(() =>
  import('@/features/ai/AIPages').then((m) => ({ default: m.ExperimentsPage })),
);
const DriftDashboardPage = lazy(() =>
  import('@/features/ai/AIPages').then((m) => ({ default: m.DriftDashboardPage })),
);
const ReportsPage = lazy(() =>
  import('@/features/reports/ReportsPage').then((m) => ({ default: m.ReportsPage })),
);
const AdminPage = lazy(() =>
  import('@/features/admin/AdminPage').then((m) => ({ default: m.AdminPage })),
);
const SettingsPage = lazy(() =>
  import('@/features/settings/SettingsPage').then((m) => ({ default: m.SettingsPage })),
);

function PageLoader() {
  return (
    <div className="flex h-64 items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}

function S({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: ROUTES.LOGIN, element: <Navigate to={ROUTES.DASHBOARD} replace /> },
      { path: ROUTES.REGISTER, element: <Navigate to={ROUTES.DASHBOARD} replace /> },
      { path: ROUTES.FORGOT_PASSWORD, element: <Navigate to={ROUTES.DASHBOARD} replace /> },
      { path: ROUTES.RESET_PASSWORD, element: <Navigate to={ROUTES.DASHBOARD} replace /> },
    ],
  },

  { path: ROUTES.UNAUTHORIZED, element: <S><UnauthorizedPage /></S> },
  { path: ROUTES.FORBIDDEN, element: <S><ForbiddenPage /></S> },

  {
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: ROUTES.HOME, element: <Navigate to={ROUTES.DASHBOARD} replace /> },
      { path: ROUTES.DASHBOARD, element: <S><DashboardPage /></S> },

      { path: ROUTES.DATASETS, element: <S><DatasetsPage /></S> },
      { path: ROUTES.DATASET_DETAIL, element: <S><DatasetDetailPage /></S> },

      {
        path: ROUTES.ANALYTICS,
        element: (
          <ProtectedRoute permission={PERMISSIONS.ANALYTICS_VIEW}>
            <S><AnalyticsPage /></S>
          </ProtectedRoute>
        ),
      },
      {
        path: `${ROUTES.ANALYTICS}/*`,
        element: (
          <ProtectedRoute permission={PERMISSIONS.ANALYTICS_VIEW}>
            <S><AnalyticsPage /></S>
          </ProtectedRoute>
        ),
      },

      {
        path: ROUTES.AI,
        element: (
          <ProtectedRoute permission={PERMISSIONS.AI_VIEW}>
            <S><AIPage /></S>
          </ProtectedRoute>
        ),
      },
      {
        path: ROUTES.AI_MODELS,
        element: (
          <ProtectedRoute permission={PERMISSIONS.AI_VIEW}>
            <S><AIModelsPage /></S>
          </ProtectedRoute>
        ),
      },
      {
        path: ROUTES.AI_EXPERIMENTS,
        element: (
          <ProtectedRoute permission={PERMISSIONS.AI_VIEW}>
            <S><ExperimentsPage /></S>
          </ProtectedRoute>
        ),
      },
      {
        path: ROUTES.AI_DRIFT,
        element: (
          <ProtectedRoute permission={PERMISSIONS.AI_VIEW}>
            <S><DriftDashboardPage /></S>
          </ProtectedRoute>
        ),
      },

      {
        path: ROUTES.REPORTS,
        element: (
          <ProtectedRoute permission={PERMISSIONS.REPORTS_VIEW}>
            <S><ReportsPage /></S>
          </ProtectedRoute>
        ),
      },

      {
        path: ROUTES.ADMIN,
        element: (
          <ProtectedRoute permission={PERMISSIONS.USERS_MANAGE}>
            <S><AdminPage /></S>
          </ProtectedRoute>
        ),
      },
      {
        path: `${ROUTES.ADMIN}/*`,
        element: (
          <ProtectedRoute permission={PERMISSIONS.USERS_MANAGE}>
            <S><AdminPage /></S>
          </ProtectedRoute>
        ),
      },

      { path: ROUTES.SETTINGS, element: <S><SettingsPage /></S> },
      { path: `${ROUTES.SETTINGS}/*`, element: <S><SettingsPage /></S> },
    ],
  },

  {
    path: '*',
    element: (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 text-center">
        <p className="text-6xl font-bold text-gray-300">404</p>
        <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Page Not Found</h1>
        <a href={ROUTES.DASHBOARD} className="mt-6 text-brand-600 hover:underline">
          Go to Dashboard
        </a>
      </div>
    ),
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
