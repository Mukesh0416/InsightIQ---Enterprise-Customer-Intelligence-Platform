import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { authApi } from '@/api';
import { useAuthStore } from '@/stores/authStore';
import { Tabs } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, Avatar } from '@/components/ui/Card';

function ProfileTab() {
  const { user } = useAuthStore();
  return (
    <div className="flex flex-col gap-6 max-w-lg">
      <Card>
        <CardHeader><CardTitle>Profile Information</CardTitle></CardHeader>
        <div className="flex items-center gap-4 mb-6">
          <Avatar name={user?.full_name ?? ''} size="xl" />
          <div>
            <p className="font-semibold text-gray-900 dark:text-gray-100">{user?.full_name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {user?.roles.map((r) => (
                <span key={r.id} className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                  {r.name}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Account Status</p>
            <p className="font-medium text-green-600">{user?.is_active ? 'Active' : 'Inactive'}</p>
          </div>
          <div>
            <p className="text-gray-500">Email Verified</p>
            <p className="font-medium">{user?.is_verified ? 'Yes' : 'Pending'}</p>
          </div>
        </div>
      </Card>
    </div>
  );
}

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(8, 'New password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type PasswordForm = z.infer<typeof passwordSchema>;

function SecurityTab() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  const mutation = useMutation({
    mutationFn: (d: PasswordForm) => authApi.changePassword(d.current_password, d.new_password),
    onSuccess: () => { toast.success('Password changed successfully'); reset(); },
    onError: () => toast.error('Current password is incorrect'),
  });

  return (
    <div className="max-w-lg">
      <Card>
        <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="flex flex-col gap-4">
          <Input label="Current password" type="password" error={errors.current_password?.message} {...register('current_password')} id="current-pw" required />
          <Input label="New password" type="password" error={errors.new_password?.message} {...register('new_password')} id="new-pw" required />
          <Input label="Confirm new password" type="password" error={errors.confirm_password?.message} {...register('confirm_password')} id="confirm-pw" required />
          <Button type="submit" loading={mutation.isPending} className="self-start">Update Password</Button>
        </form>
      </Card>
    </div>
  );
}

function NotificationsTab() {
  const [prefs, setPrefs] = useState({
    email_training_complete: true,
    email_report_ready: true,
    email_drift_detected: true,
    in_app_all: true,
  });

  const toggle = (key: keyof typeof prefs) =>
    setPrefs((p) => ({ ...p, [key]: !p[key] }));

  return (
    <div className="max-w-lg">
      <Card>
        <CardHeader><CardTitle>Notification Preferences</CardTitle></CardHeader>
        <div className="flex flex-col gap-4">
          {(Object.entries(prefs) as [keyof typeof prefs, boolean][]).map(([key, value]) => (
            <label key={key} className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={value}
                onClick={() => toggle(key)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${value ? 'bg-brand-600' : 'bg-gray-300 dark:bg-gray-600'}`}
              >
                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${value ? 'translate-x-4' : 'translate-x-1'}`} />
              </button>
            </label>
          ))}
          <Button className="self-start mt-2" onClick={() => toast.success('Preferences saved')}>
            Save Preferences
          </Button>
        </div>
      </Card>
    </div>
  );
}

const SETTINGS_TABS = [
  { id: 'profile', label: 'Profile' },
  { id: 'security', label: 'Security' },
  { id: 'notifications', label: 'Notifications' },
];

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabContent: Record<string, React.ReactNode> = {
    profile: <ProfileTab />,
    security: <SecurityTab />,
    notifications: <NotificationsTab />,
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">Manage your account and preferences</p>
      </div>
      <Tabs tabs={SETTINGS_TABS} activeTab={activeTab} onChange={setActiveTab} />
      <div>{tabContent[activeTab]}</div>
    </div>
  );
}
