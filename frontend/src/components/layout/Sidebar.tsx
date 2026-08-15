import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Database, BarChart3, Brain, FileText,
  Settings, ChevronLeft, ChevronRight, X,
  TrendingUp, Shield,
} from 'lucide-react';
import { cn } from '@/utils';
import { useUIStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import { ROUTES, PERMISSIONS } from '@/constants';

interface NavItem {
  label: string;
  icon: React.ReactNode;
  to: string;
  permission?: string;
  badge?: string | number;
  children?: { label: string; to: string }[];
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: <LayoutDashboard size={18} />, to: ROUTES.DASHBOARD },
  { label: 'Datasets', icon: <Database size={18} />, to: ROUTES.DATASETS },
  {
    label: 'Analytics', icon: <BarChart3 size={18} />, to: ROUTES.ANALYTICS,
    permission: PERMISSIONS.ANALYTICS_VIEW,
    children: [
      { label: 'EDA', to: ROUTES.ANALYTICS_EDA },
      { label: 'Customer', to: ROUTES.ANALYTICS_CUSTOMER },
      { label: 'Revenue', to: ROUTES.ANALYTICS_REVENUE },
      { label: 'Retention', to: ROUTES.ANALYTICS_RETENTION },
      { label: 'Cohort', to: ROUTES.ANALYTICS_COHORT },
      { label: 'RFM', to: ROUTES.ANALYTICS_RFM },
      { label: 'CLV', to: ROUTES.ANALYTICS_CLV },
    ],
  },
  {
    label: 'AI Platform', icon: <Brain size={18} />, to: ROUTES.AI,
    permission: PERMISSIONS.AI_VIEW,
    children: [
      { label: 'Models', to: ROUTES.AI_MODELS },
      { label: 'Train', to: ROUTES.AI_TRAIN },
      { label: 'Experiments', to: ROUTES.AI_EXPERIMENTS },
      { label: 'Predictions', to: ROUTES.AI_PREDICTIONS },
      { label: 'Drift', to: ROUTES.AI_DRIFT },
    ],
  },
  { label: 'Reports', icon: <FileText size={18} />, to: ROUTES.REPORTS, permission: PERMISSIONS.REPORTS_VIEW },
  { label: 'Forecasting', icon: <TrendingUp size={18} />, to: ROUTES.ANALYTICS_CLV },
];

const BOTTOM_ITEMS: NavItem[] = [
  { label: 'Admin', icon: <Shield size={18} />, to: ROUTES.ADMIN, permission: PERMISSIONS.USERS_MANAGE },
  { label: 'Settings', icon: <Settings size={18} />, to: ROUTES.SETTINGS },
];

function NavItemComponent({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const location = useLocation();
  const { hasPermission } = useAuthStore();
  const [expanded, setExpanded] = useState(false);

  if (item.permission && !hasPermission(item.permission)) return null;

  const isActive = location.pathname.startsWith(item.to);

  if (item.children) {
    return (
      <div>
        <button
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          className={cn(
            'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive
              ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100',
          )}
        >
          <span className="shrink-0">{item.icon}</span>
          {!collapsed && (
            <>
              <span className="flex-1 text-left">{item.label}</span>
              <ChevronRight size={14} className={cn('transition-transform', expanded && 'rotate-90')} />
            </>
          )}
        </button>
        {!collapsed && expanded && (
          <div className="ml-6 mt-1 flex flex-col gap-0.5 border-l border-gray-200 pl-3 dark:border-gray-700">
            {item.children.map((child) => (
              <NavLink
                key={child.to}
                to={child.to}
                className={({ isActive }) =>
                  cn('rounded-md px-2 py-1.5 text-xs font-medium transition-colors',
                    isActive
                      ? 'text-brand-700 dark:text-brand-300'
                      : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100',
                  )
                }
              >
                {child.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <NavLink
      to={item.to}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100',
        )
      }
    >
      <span className="shrink-0">{item.icon}</span>
      {!collapsed && <span className="flex-1">{item.label}</span>}
      {!collapsed && item.badge !== undefined && (
        <span className="rounded-full bg-brand-600 px-1.5 py-0.5 text-2xs font-bold text-white">
          {item.badge}
        </span>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { sidebarOpen, sidebarCollapsed, setSidebarOpen, toggleSidebarCollapsed } = useUIStore();

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-30 bg-black/40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        animate={{ width: sidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900',
          'lg:relative lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 px-4 dark:border-gray-700">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
                <Brain size={16} className="text-white" />
              </div>
              <span className="text-base font-bold text-gray-900 dark:text-gray-100">InsightIQ</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 lg:hidden dark:hover:bg-gray-800"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
          <button
            onClick={toggleSidebarCollapsed}
            className="hidden rounded-lg p-1 text-gray-400 hover:bg-gray-100 lg:block dark:hover:bg-gray-800"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Main navigation">
          <div className="flex flex-col gap-0.5">
            {NAV_ITEMS.map((item) => (
              <NavItemComponent key={item.to} item={item} collapsed={sidebarCollapsed} />
            ))}
          </div>
        </nav>

        {/* Bottom nav */}
        <div className="border-t border-gray-200 px-3 py-3 dark:border-gray-700">
          <div className="flex flex-col gap-0.5">
            {BOTTOM_ITEMS.map((item) => (
              <NavItemComponent key={item.to} item={item} collapsed={sidebarCollapsed} />
            ))}
          </div>
        </div>
      </motion.aside>
    </>
  );
}
