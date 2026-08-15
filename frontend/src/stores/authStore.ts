import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { tokenStorage } from '@/api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (roleCodename: string) => boolean;
}

// Demo user with all permissions so the UI is fully accessible without login.
const DEMO_USER: User = {
  id: 'demo-user',
  email: 'demo@insightiq.local',
  full_name: 'Demo User',
  is_active: true,
  is_verified: true,
  organization_id: 'demo-org',
  roles: [
    {
      id: 'demo-admin',
      name: 'Administrator',
      codename: 'admin',
      permissions: [
        { id: 'p1', name: 'Analytics View', codename: 'analytics.view' },
        { id: 'p2', name: 'AI Train', codename: 'ai.train' },
        { id: 'p3', name: 'AI Predict', codename: 'ai.predict' },
        { id: 'p4', name: 'AI View', codename: 'ai.view' },
        { id: 'p5', name: 'AI Manage', codename: 'ai.manage' },
        { id: 'p6', name: 'Reports Generate', codename: 'reports.generate' },
        { id: 'p7', name: 'Reports View', codename: 'reports.view' },
        { id: 'p8', name: 'Reports Delete', codename: 'reports.delete' },
        { id: 'p9', name: 'Exports Create', codename: 'exports.create' },
        { id: 'p10', name: 'Exports View', codename: 'exports.view' },
        { id: 'p11', name: 'Jobs View', codename: 'jobs.view' },
        { id: 'p12', name: 'Jobs Manage', codename: 'jobs.manage' },
        { id: 'p13', name: 'Audit View', codename: 'audit.view' },
        { id: 'p14', name: 'Users Manage', codename: 'users.manage' },
        { id: 'p15', name: 'Roles Manage', codename: 'roles.manage' },
        { id: 'p16', name: 'Settings Manage', codename: 'settings.manage' },
      ],
    },
  ],
  permissions: [
    'analytics.view',
    'ai.train',
    'ai.predict',
    'ai.view',
    'ai.manage',
    'reports.generate',
    'reports.view',
    'reports.delete',
    'exports.create',
    'exports.view',
    'jobs.view',
    'jobs.manage',
    'audit.view',
    'users.manage',
    'roles.manage',
    'settings.manage',
  ],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: DEMO_USER,
      isAuthenticated: true,

      setUser: (user) => set({ user, isAuthenticated: true }),

      setTokens: (access, refresh) => {
        tokenStorage.set(access, refresh);
        set({ isAuthenticated: true });
      },

      logout: () => {
        tokenStorage.clear();
        set({ user: null, isAuthenticated: false });
      },

      hasPermission: (permission) => {
        const { user } = get();
        if (!user) return false;
        return user.permissions.includes(permission);
      },

      hasRole: (roleCodename) => {
        const { user } = get();
        if (!user) return false;
        return user.roles.some((r) => r.codename === roleCodename);
      },
    }),
    {
      name: 'iq_auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    },
  ),
);
