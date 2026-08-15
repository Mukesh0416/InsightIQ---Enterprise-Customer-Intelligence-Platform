import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, Sun, Moon, Monitor, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { cn } from '@/utils';
import { useUIStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import { notificationsApi, authApi } from '@/api';
import { QUERY_KEYS, ROUTES } from '@/constants';
import { Avatar } from '@/components/ui/Card';
import { Dropdown } from '@/components/ui/Tabs';

type Theme = 'light' | 'dark' | 'system';

function ThemeSwitcher() {
  const { theme, setTheme } = useUIStore();
  const options: { value: Theme; icon: React.ReactNode; label: string }[] = [
    { value: 'light', icon: <Sun size={14} />, label: 'Light' },
    { value: 'dark', icon: <Moon size={14} />, label: 'Dark' },
    { value: 'system', icon: <Monitor size={14} />, label: 'System' },
  ];
  return (
    <div className="flex items-center rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => setTheme(o.value)}
          title={o.label}
          aria-label={`Switch to ${o.label} theme`}
          className={cn(
            'rounded-md p-1.5 transition-colors',
            theme === o.value
              ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
              : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300',
          )}
        >
          {o.icon}
        </button>
      ))}
    </div>
  );
}

function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: countData } = useQuery({
    queryKey: QUERY_KEYS.NOTIFICATION_COUNT,
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 30_000,
  });

  const { data: notifs } = useQuery({
    queryKey: [...QUERY_KEYS.NOTIFICATIONS, 'recent'],
    queryFn: () => notificationsApi.list({ page_size: 5, unread_only: false }),
    enabled: open,
  });

  const markRead = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATION_COUNT }),
  });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const count = countData?.count ?? 0;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notifications${count > 0 ? `, ${count} unread` : ''}`}
        className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
      >
        <Bell size={18} />
        {count > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-2xs font-bold text-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-gray-200 bg-white shadow-modal dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Notifications</span>
            {count > 0 && (
              <button
                onClick={() => markRead.mutate()}
                className="text-xs text-brand-600 hover:underline dark:text-brand-400"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-72 overflow-y-auto">
            {notifs?.items.length === 0 ? (
              <p className="py-8 text-center text-sm text-gray-500">No notifications</p>
            ) : (
              notifs?.items.map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    'border-b border-gray-100 px-4 py-3 last:border-0 dark:border-gray-700',
                    !n.is_read && 'bg-brand-50/50 dark:bg-brand-900/10',
                  )}
                >
                  <p className="text-xs font-medium text-gray-900 dark:text-gray-100">{n.title}</p>
                  <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{n.message}</p>
                </div>
              ))
            )}
          </div>
          <div className="border-t border-gray-200 px-4 py-2 dark:border-gray-700">
            <button
              onClick={() => { navigate(ROUTES.SETTINGS_NOTIFICATIONS); setOpen(false); }}
              className="text-xs text-brand-600 hover:underline dark:text-brand-400"
            >
              View all notifications
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function TopNav() {
  const { toggleSidebar, setCommandPaletteOpen } = useUIStore();
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      logout();
      qc.clear();
      navigate(ROUTES.DASHBOARD);
      toast.success('Signed out successfully');
    },
  });

  const userMenuItems = [
    { label: 'Profile', icon: <User size={14} />, onClick: () => navigate(ROUTES.SETTINGS_PROFILE) },
    { label: 'Settings', icon: <Settings size={14} />, onClick: () => navigate(ROUTES.SETTINGS) },
    { divider: true, label: '', onClick: undefined },
    { label: 'Sign out', icon: <LogOut size={14} />, onClick: () => logoutMutation.mutate(), danger: true },
  ];

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-gray-700 dark:bg-gray-900">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 lg:hidden"
        >
          <Menu size={18} />
        </button>

        <button
          onClick={() => setCommandPaletteOpen(true)}
          aria-label="Open search"
          className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm text-gray-400 transition-colors hover:border-gray-300 hover:text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600 sm:w-64"
        >
          <Search size={14} />
          <span className="hidden sm:inline">Search…</span>
          <kbd className="ml-auto hidden rounded bg-gray-200 px-1.5 py-0.5 text-2xs font-mono dark:bg-gray-700 sm:inline">
            ⌘K
          </kbd>
        </button>
      </div>

      <div className="flex items-center gap-2">
        <ThemeSwitcher />
        <NotificationBell />

        {user && (
          <Dropdown
            align="right"
            trigger={
              <button className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
                <Avatar name={user.full_name} src={user.avatar_url} size="sm" />
                <span className="hidden text-sm font-medium text-gray-700 dark:text-gray-300 sm:block">
                  {user.full_name.split(' ')[0]}
                </span>
                <ChevronDown size={14} className="text-gray-400" />
              </button>
            }
            items={userMenuItems}
          />
        )}
      </div>
    </header>
  );
}
