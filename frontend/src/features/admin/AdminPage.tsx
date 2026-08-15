import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createColumnHelper } from '@tanstack/react-table';
import toast from 'react-hot-toast';
import { UserX, Shield } from 'lucide-react';
import { adminApi, auditApi } from '@/api';
import { QUERY_KEYS } from '@/constants';
import { formatDate, formatRelativeTime } from '@/utils';
import type { User, AuditEvent } from '@/types';
import { Button } from '@/components/ui/Button';
import { Badge, Avatar } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { Tabs } from '@/components/ui/Tabs';
import { ConfirmDialog } from '@/components/ui/Modal';

// ─── Users Tab ────────────────────────────────────────────────────────────────

const userColHelper = createColumnHelper<User>();

function UsersTab() {
  const [deactivateId, setDeactivateId] = useState<string | null>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.USERS,
    queryFn: () => adminApi.listUsers({ page_size: 100 }),
  });

  const deactivateMutation = useMutation({
    mutationFn: adminApi.deactivateUser,
    onSuccess: () => {
      toast.success('User deactivated');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.USERS });
      setDeactivateId(null);
    },
  });

  const columns = [
    userColHelper.accessor('full_name', {
      header: 'User',
      cell: (i) => (
        <div className="flex items-center gap-3">
          <Avatar name={i.getValue()} src={i.row.original.avatar_url} size="sm" />
          <div>
            <p className="font-medium text-gray-900 dark:text-gray-100">{i.getValue()}</p>
            <p className="text-xs text-gray-400">{i.row.original.email}</p>
          </div>
        </div>
      ),
    }),
    userColHelper.accessor('roles', {
      header: 'Roles',
      cell: (i) => (
        <div className="flex flex-wrap gap-1">
          {i.getValue().map((r) => <Badge key={r.id} variant="purple">{r.name}</Badge>)}
        </div>
      ),
    }),
    userColHelper.accessor('is_active', {
      header: 'Status',
      cell: (i) => <Badge variant={i.getValue() ? 'success' : 'danger'}>{i.getValue() ? 'Active' : 'Inactive'}</Badge>,
    }),
    userColHelper.accessor('is_verified', {
      header: 'Verified',
      cell: (i) => <Badge variant={i.getValue() ? 'success' : 'warning'}>{i.getValue() ? 'Verified' : 'Pending'}</Badge>,
    }),
    userColHelper.accessor('created_at', { header: 'Joined', cell: (i) => formatDate(i.getValue()) }),
    userColHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: (i) => i.row.original.is_active ? (
        <Button size="xs" variant="ghost" leftIcon={<UserX size={12} />}
          onClick={() => setDeactivateId(i.row.original.id)}
          className="text-red-500">
          Deactivate
        </Button>
      ) : null,
    }),
  ];

  const deactivateUser = data?.items.find((u) => u.id === deactivateId);

  return (
    <>
      <DataTable
        data={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        searchable
        searchPlaceholder="Search users…"
        emptyTitle="No users found"
      />
      <ConfirmDialog
        open={!!deactivateId}
        onClose={() => setDeactivateId(null)}
        onConfirm={() => deactivateId && deactivateMutation.mutate(deactivateId)}
        title="Deactivate User"
        description={`Deactivate ${deactivateUser?.full_name}? They will lose access immediately.`}
        loading={deactivateMutation.isPending}
      />
    </>
  );
}

// ─── Audit Log Tab ────────────────────────────────────────────────────────────

const auditColHelper = createColumnHelper<AuditEvent>();

function AuditTab() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.AUDIT,
    queryFn: () => auditApi.list({ page_size: 100 }),
    refetchInterval: 30_000,
  });

  const columns = [
    auditColHelper.accessor('event_type', {
      header: 'Event',
      cell: (i) => <span className="font-mono text-xs">{i.getValue()}</span>,
    }),
    auditColHelper.accessor('resource_type', { header: 'Resource' }),
    auditColHelper.accessor('user_email', {
      header: 'User',
      cell: (i) => <span className="text-xs">{i.getValue()}</span>,
    }),
    auditColHelper.accessor('ip_address', { header: 'IP', cell: (i) => i.getValue() ?? '—' }),
    auditColHelper.accessor('created_at', { header: 'Time', cell: (i) => formatRelativeTime(i.getValue()) }),
  ];

  return (
    <DataTable
      data={data?.items ?? []}
      columns={columns}
      loading={isLoading}
      searchable
      searchPlaceholder="Search audit events…"
      emptyTitle="No audit events"
    />
  );
}

// ─── Roles Tab ────────────────────────────────────────────────────────────────

function RolesTab() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.ROLES,
    queryFn: adminApi.listRoles,
  });

  if (isLoading) return <div className="py-8 text-center text-sm text-gray-500">Loading roles…</div>;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data?.map((role) => (
        <div key={role.id} className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2 mb-3">
            <Shield size={16} className="text-brand-600" />
            <p className="font-semibold text-gray-900 dark:text-gray-100">{role.name}</p>
          </div>
          <p className="mb-3 text-xs font-mono text-gray-400">{role.codename}</p>
          <div className="flex flex-wrap gap-1">
            {role.permissions.slice(0, 5).map((p) => (
              <Badge key={p.id} variant="default" className="text-2xs">{p.codename}</Badge>
            ))}
            {role.permissions.length > 5 && (
              <Badge variant="default" className="text-2xs">+{role.permissions.length - 5} more</Badge>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Admin Hub ────────────────────────────────────────────────────────────────

const ADMIN_TABS = [
  { id: 'users', label: 'Users' },
  { id: 'roles', label: 'Roles & Permissions' },
  { id: 'audit', label: 'Audit Log' },
];

export function AdminPage() {
  const [activeTab, setActiveTab] = useState('users');

  const tabContent: Record<string, React.ReactNode> = {
    users: <UsersTab />,
    roles: <RolesTab />,
    audit: <AuditTab />,
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Administration</h1>
        <p className="text-sm text-gray-500">Manage users, roles, permissions, and audit logs</p>
      </div>
      <Tabs tabs={ADMIN_TABS} activeTab={activeTab} onChange={setActiveTab} />
      <div>{tabContent[activeTab]}</div>
    </div>
  );
}
