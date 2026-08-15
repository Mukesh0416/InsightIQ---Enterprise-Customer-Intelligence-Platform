import { describe, it, expect, beforeEach } from 'vitest';
import { tokenStorage } from '@/api/client';
import {
  formatFileSize,
  formatNumber,
  formatCurrency,
  formatPercent,
  truncate,
  getInitials,
  cn,
  getErrorMessage,
} from '@/utils';

// ─── Token Storage ────────────────────────────────────────────────────────────

describe('tokenStorage', () => {
  beforeEach(() => tokenStorage.clear());

  it('stores and retrieves access token', () => {
    tokenStorage.set('access123', 'refresh456');
    expect(tokenStorage.getAccess()).toBe('access123');
    expect(tokenStorage.getRefresh()).toBe('refresh456');
  });

  it('clears tokens', () => {
    tokenStorage.set('a', 'b');
    tokenStorage.clear();
    expect(tokenStorage.getAccess()).toBeNull();
    expect(tokenStorage.getRefresh()).toBeNull();
  });
});

// ─── Utility Functions ────────────────────────────────────────────────────────

describe('formatFileSize', () => {
  it('formats bytes', () => expect(formatFileSize(512)).toBe('512 B'));
  it('formats kilobytes', () => expect(formatFileSize(1536)).toBe('1.5 KB'));
  it('formats megabytes', () => expect(formatFileSize(2 * 1024 * 1024)).toBe('2 MB'));
  it('handles zero', () => expect(formatFileSize(0)).toBe('0 B'));
});

describe('formatNumber', () => {
  it('formats integers', () => expect(formatNumber(1234567)).toBe('1,234,567'));
  it('formats decimals', () => expect(formatNumber(3.14159, 2)).toBe('3.14'));
});

describe('formatCurrency', () => {
  it('formats USD', () => expect(formatCurrency(1500)).toBe('$1,500'));
  it('formats large amounts', () => expect(formatCurrency(1_000_000)).toBe('$1,000,000'));
});

describe('formatPercent', () => {
  it('formats ratio to percent', () => expect(formatPercent(0.856)).toBe('85.6%'));
  it('formats with custom decimals', () => expect(formatPercent(0.5, 0)).toBe('50%'));
});

describe('truncate', () => {
  it('truncates long strings', () => expect(truncate('Hello World', 5)).toBe('Hello…'));
  it('does not truncate short strings', () => expect(truncate('Hi', 10)).toBe('Hi'));
});

describe('getInitials', () => {
  it('returns initials from full name', () => expect(getInitials('Jane Smith')).toBe('JS'));
  it('handles single name', () => expect(getInitials('Alice')).toBe('A'));
  it('uses only first two words', () => expect(getInitials('John Michael Doe')).toBe('JM'));
});

describe('cn', () => {
  it('merges class names', () => expect(cn('px-4', 'py-2')).toBe('px-4 py-2'));
  it('handles conditional classes', () => expect(cn('base', false && 'hidden', 'active')).toBe('base active'));
  it('deduplicates tailwind classes', () => expect(cn('px-4', 'px-6')).toBe('px-6'));
});

describe('getErrorMessage', () => {
  it('extracts message from API error', () => {
    const error = { response: { data: { detail: 'Not found' } } };
    expect(getErrorMessage(error)).toBe('Not found');
  });

  it('extracts message from Error instance', () => {
    expect(getErrorMessage(new Error('Something failed'))).toBe('Something failed');
  });

  it('returns fallback for unknown errors', () => {
    expect(getErrorMessage(null)).toBe('An unexpected error occurred');
  });
});

// ─── Auth Store ───────────────────────────────────────────────────────────────

import { useAuthStore } from '@/stores/authStore';
import type { User } from '@/types';

const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_verified: true,
  organization_id: 'org-1',
  roles: [{ id: 'r1', name: 'Admin', codename: 'admin', permissions: [{ id: 'p1', name: 'View Analytics', codename: 'analytics.view' }] }],
  permissions: ['analytics.view', 'ai.view'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it('starts unauthenticated', () => {
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('sets user and marks authenticated', () => {
    useAuthStore.getState().setUser(mockUser);
    expect(useAuthStore.getState().user).toEqual(mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('checks permissions correctly', () => {
    useAuthStore.getState().setUser(mockUser);
    expect(useAuthStore.getState().hasPermission('analytics.view')).toBe(true);
    expect(useAuthStore.getState().hasPermission('admin.delete')).toBe(false);
  });

  it('checks roles correctly', () => {
    useAuthStore.getState().setUser(mockUser);
    expect(useAuthStore.getState().hasRole('admin')).toBe(true);
    expect(useAuthStore.getState().hasRole('superuser')).toBe(false);
  });

  it('clears state on logout', () => {
    useAuthStore.getState().setUser(mockUser);
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
