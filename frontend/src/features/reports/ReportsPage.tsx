import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { createColumnHelper } from '@tanstack/react-table';
import toast from 'react-hot-toast';
import { FileText, Download, Trash2, Plus } from 'lucide-react';
import { reportsApi } from '@/api';
import { QUERY_KEYS } from '@/constants';
import { formatFileSize, formatRelativeTime, downloadBlob } from '@/utils';
import type { Report, ReportFormat } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { Modal, ConfirmDialog } from '@/components/ui/Modal';

const colHelper = createColumnHelper<Report>();

const generateSchema = z.object({
  name: z.string().min(1, 'Report name is required'),
  report_type: z.string().min(1, 'Select a report type'),
  format: z.enum(['pdf', 'excel', 'csv', 'json']),
});

type GenerateForm = z.infer<typeof generateSchema>;

const REPORT_TYPES = [
  { value: 'customer_summary', label: 'Customer Summary' },
  { value: 'revenue_analysis', label: 'Revenue Analysis' },
  { value: 'retention_report', label: 'Retention Report' },
  { value: 'cohort_analysis', label: 'Cohort Analysis' },
  { value: 'rfm_analysis', label: 'RFM Analysis' },
  { value: 'model_performance', label: 'Model Performance' },
  { value: 'audit_summary', label: 'Audit Summary' },
];

const FORMAT_OPTIONS: { value: ReportFormat; label: string }[] = [
  { value: 'pdf', label: 'PDF' },
  { value: 'excel', label: 'Excel (.xlsx)' },
  { value: 'csv', label: 'CSV' },
  { value: 'json', label: 'JSON' },
];

function GenerateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm<GenerateForm>({
    resolver: zodResolver(generateSchema),
    defaultValues: { format: 'pdf' },
  });

  const mutation = useMutation({
    mutationFn: reportsApi.generate,
    onSuccess: () => {
      toast.success('Report generation started');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.REPORTS });
      onClose();
    },
    onError: () => toast.error('Failed to generate report'),
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Generate Report"
      description="Configure and generate a new report"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" loading={mutation.isPending} onClick={handleSubmit((d) => mutation.mutate(d))}>
            Generate
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Input label="Report name" placeholder="e.g. Q4 Customer Summary" error={errors.name?.message} {...register('name')} id="report-name" required />
        <Select label="Report type" id="report-type" options={REPORT_TYPES} placeholder="Select type…" error={errors.report_type?.message} {...register('report_type')} required />
        <Select label="Format" id="report-format" options={FORMAT_OPTIONS} error={errors.format?.message} {...register('format')} required />
      </div>
    </Modal>
  );
}

export function ReportsPage() {
  const [generateOpen, setGenerateOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.REPORTS,
    queryFn: () => reportsApi.list({ page_size: 100 }),
    refetchInterval: 10_000,
  });

  const downloadMutation = useMutation({
    mutationFn: reportsApi.download,
    onSuccess: (blob, id) => {
      const report = data?.items.find((r) => r.id === id);
      downloadBlob(blob, `${report?.name ?? 'report'}.${report?.format ?? 'pdf'}`);
    },
    onError: () => toast.error('Download failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: reportsApi.delete,
    onSuccess: () => {
      toast.success('Report deleted');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.REPORTS });
      setDeleteId(null);
    },
  });

  const columns = [
    colHelper.accessor('name', {
      header: 'Report',
      cell: (i) => (
        <div className="flex items-center gap-2">
          <FileText size={16} className="shrink-0 text-gray-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">{i.getValue()}</span>
        </div>
      ),
    }),
    colHelper.accessor('report_type', { header: 'Type', cell: (i) => <Badge>{i.getValue().replace(/_/g, ' ')}</Badge> }),
    colHelper.accessor('format', { header: 'Format', cell: (i) => <Badge variant="info">{i.getValue().toUpperCase()}</Badge> }),
    colHelper.accessor('status', {
      header: 'Status',
      cell: (i) => {
        const colors: Record<string, string> = { ready: 'success', generating: 'warning', failed: 'danger', pending: 'default' };
        return <Badge variant={colors[i.getValue()] as 'success'}>{i.getValue()}</Badge>;
      },
    }),
    colHelper.accessor('file_size', { header: 'Size', cell: (i) => i.getValue() ? formatFileSize(i.getValue()!) : '—' }),
    colHelper.accessor('created_at', { header: 'Created', cell: (i) => formatRelativeTime(i.getValue()) }),
    colHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: (i) => (
        <div className="flex gap-1">
          {i.row.original.status === 'ready' && (
            <Button size="xs" variant="ghost" leftIcon={<Download size={12} />}
              loading={downloadMutation.isPending && downloadMutation.variables === i.row.original.id}
              onClick={() => downloadMutation.mutate(i.row.original.id)}>
              Download
            </Button>
          )}
          <Button size="xs" variant="ghost" leftIcon={<Trash2 size={12} />}
            onClick={() => setDeleteId(i.row.original.id)}
            className="text-red-500 hover:text-red-700">
            Delete
          </Button>
        </div>
      ),
    }),
  ];

  const deleteReport = data?.items.find((r) => r.id === deleteId);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Reports</h1>
          <p className="text-sm text-gray-500">Generate and download business intelligence reports</p>
        </div>
        <Button leftIcon={<Plus size={16} />} onClick={() => setGenerateOpen(true)}>Generate Report</Button>
      </div>

      <DataTable
        data={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        searchable
        searchPlaceholder="Search reports…"
        emptyTitle="No reports yet"
        emptyDescription="Generate your first report to share insights with your team."
      />

      <GenerateModal open={generateOpen} onClose={() => setGenerateOpen(false)} />

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        title="Delete Report"
        description={`Delete "${deleteReport?.name}"? This cannot be undone.`}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
