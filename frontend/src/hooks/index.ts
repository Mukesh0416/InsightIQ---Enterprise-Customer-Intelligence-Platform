import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/api';
import { useAuthStore } from '@/stores/authStore';
import { QUERY_KEYS } from '@/constants';
import { tokenStorage } from '@/api/client';

// ─── useCurrentUser ───────────────────────────────────────────────────────────

export function useCurrentUser() {
  const { setUser, isAuthenticated } = useAuthStore();

  return useQuery({
    queryKey: QUERY_KEYS.ME,
    queryFn: async () => {
      const user = await authApi.me();
      setUser(user);
      return user;
    },
    enabled: isAuthenticated && !!tokenStorage.getAccess(),
    staleTime: 1000 * 60 * 10,
    retry: false,
    // Don't block the UI when the backend is unavailable — the demo user
    // in the auth store keeps the app fully navigable.
  });
}

// ─── useRequireAuth ───────────────────────────────────────────────────────────

export function useRequireAuth() {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated;
}

// ─── usePermission ────────────────────────────────────────────────────────────

export function usePermission(permission: string): boolean {
  const { hasPermission } = useAuthStore();
  return hasPermission(permission);
}

export function usePermissions(permissions: string[]): Record<string, boolean> {
  const { hasPermission } = useAuthStore();
  return Object.fromEntries(permissions.map((p) => [p, hasPermission(p)]));
}

// ─── useDebounce ──────────────────────────────────────────────────────────────

import { useState } from 'react';

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

// ─── useLocalStorage ─────────────────────────────────────────────────────────

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const set = (newValue: T) => {
    setValue(newValue);
    localStorage.setItem(key, JSON.stringify(newValue));
  };

  return [value, set] as const;
}

// ─── usePageTitle ─────────────────────────────────────────────────────────────

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} — InsightIQ` : 'InsightIQ';
    return () => { document.title = 'InsightIQ'; };
  }, [title]);
}

// ─── useJobPoller ─────────────────────────────────────────────────────────────

import { jobsApi } from '@/api';

export function useJobPoller(jobId: string | null, onComplete?: (result: unknown) => void) {
  return useQuery({
    queryKey: QUERY_KEYS.JOB(jobId ?? ''),
    queryFn: () => jobsApi.get(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed' || status === 'cancelled') {
        if (status === 'completed' && onComplete) onComplete(query.state.data?.result);
        return false;
      }
      return 2000;
    },
  });
}
