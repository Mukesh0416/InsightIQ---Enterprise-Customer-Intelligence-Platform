import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { ROUTES } from '@/constants';
import { Spinner } from '@/components/ui/Card';
import { useCurrentUser } from '@/hooks';

interface ProtectedRouteProps {
  children: React.ReactNode;
  permission?: string;
  role?: string;
}

export function ProtectedRoute({ children, permission, role }: ProtectedRouteProps) {
  const { isAuthenticated, hasPermission, hasRole } = useAuthStore();
  const { isLoading } = useCurrentUser();

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to={ROUTES.FORBIDDEN} replace />;
  }

  if (role && !hasRole(role)) {
    return <Navigate to={ROUTES.FORBIDDEN} replace />;
  }

  return <>{children}</>;
}

export function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) return <Navigate to={ROUTES.DASHBOARD} replace />;
  return <>{children}</>;
}
