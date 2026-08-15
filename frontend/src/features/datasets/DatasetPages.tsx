import { useState, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import { Upload, Trash2, Eye, Plus } from 'lucide-react';
import { datasetsApi } from '@/api';
import { QUERY_KEYS, ROUTES } from '@/constants';
import { formatFileSize, formatDate, formatRelativeTime, cn } from '@/utils';
import type { Dataset } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, Badge, ProgressBar, Skeleton } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { Modal, ConfirmDialog } from '@/components/ui/Modal';

// ─── Dataset List ─────────────────────────────────────────────────────────────

const colHelper = createColumnHelper<Dataset>();

const columns = [
  colHelper.accessor('name', {
    header: 'Name',
    cell: (info) => (
      <Link to={`/datasets/${info.row.original.id}`} className="font-medium text-brand-600 hover:underline dark:text-brand-400">
        {info.getValue()}
      </Link>
    ),
  }),
  colHelper.accessor('file_type', { header: 'Type', cell: (i) => <Badge>{i.getValue()}</Badge> }),
  colHelper.accessor('row_count', { header: 'Rows', cell: (i) => i.getValue()?.toLocaleString() ?? '—' }),
  colHelper.accessor('column_count', { header: 'Columns', cell: (i) => i.getValue() ?? '—' }),
  colHelper.accessor('file_size', { header: 'Size', cell: (i) => formatFileSize(i.getValue()) }),
  colHelper.accessor('status', {
    header: 'Status',
    cell: (i) => {
      const colors: Record<string, string> = {
        ready: 'success', processing: 'warning', error: 'danger', pending: 'default',
      };
      return <Badge variant={colors[i.getValue()] as 'success'}>{i.getValue()}</Badge>;
    },
  }),
  colHelper.accessor('created_at', { header: 'Uploaded', cell: (i) => formatRelativeTime(i.getValue()) }),
];

export function DatasetsPage() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.DATASETS,
    queryFn: () => datasetsApi.list({ page_size: 100 }),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Datasets</h1>
          <p className="text-sm text-gray-500">Manage and explore your data sources</p>
        </div>
        <Button leftIcon={<Plus size={16} />} onClick={() => setUploadOpen(true)}>
          Upload Dataset
        </Button>
      </div>

      <DataTable
        data={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        searchable
        searchPlaceholder="Search datasets…"
        emptyTitle="No datasets yet"
        emptyDescription="Upload your first dataset to get started with analytics and AI."
        toolbar={
          <Button variant="outline" size="sm" leftIcon={<Upload size={14} />} onClick={() => setUploadOpen(true)}>
            Upload
          </Button>
        }
      />

      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}

// ─── Upload Modal ─────────────────────────────────────────────────────────────

const uploadSchema = z.object({
  name: z.string().min(1, 'Dataset name is required'),
  description: z.string().optional(),
});

type UploadForm = z.infer<typeof uploadSchema>;

function UploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const qc = useQueryClient();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<UploadForm>({
    resolver: zodResolver(uploadSchema),
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/json': ['.json'], 'application/vnd.ms-excel': ['.xls'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024,
  });

  const mutation = useMutation({
    mutationFn: (d: UploadForm) => datasetsApi.upload(file!, d.name, d.description ?? '', setProgress),
    onSuccess: () => {
      toast.success('Dataset uploaded successfully');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.DATASETS });
      reset();
      setFile(null);
      setProgress(0);
      onClose();
    },
    onError: () => toast.error('Upload failed. Please try again.'),
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Upload Dataset"
      description="Supported formats: CSV, JSON, Excel (.xlsx, .xls)"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
          <Button size="sm" loading={mutation.isPending} onClick={handleSubmit((d) => mutation.mutate(d))} disabled={!file}>
            Upload
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <div
          {...getRootProps()}
          className={cn(
            'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors',
            isDragActive ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/10' : 'border-gray-300 hover:border-brand-400 dark:border-gray-600',
          )}
        >
          <input {...getInputProps()} aria-label="File upload" />
          <Upload size={32} className="mb-3 text-gray-400" />
          {file ? (
            <div className="text-center">
              <p className="font-medium text-gray-900 dark:text-gray-100">{file.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {isDragActive ? 'Drop file here' : 'Drag & drop or click to browse'}
              </p>
              <p className="mt-1 text-xs text-gray-400">Max 500 MB</p>
            </div>
          )}
        </div>

        {mutation.isPending && <ProgressBar value={progress} showValue label="Uploading…" />}

        <Input label="Dataset name" placeholder="e.g. Customer Transactions Q4 2024" error={errors.name?.message} {...register('name')} id="ds-name" required />
        <Textarea label="Description (optional)" placeholder="Brief description of this dataset…" {...register('description')} id="ds-desc" />
      </div>
    </Modal>
  );
}

// ─── Dataset Detail ───────────────────────────────────────────────────────────

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { data: dataset, isLoading } = useQuery({
    queryKey: QUERY_KEYS.DATASET(id!),
    queryFn: () => datasetsApi.get(id!),
    enabled: !!id,
  });

  const { data: preview } = useQuery({
    queryKey: QUERY_KEYS.DATASET_PREVIEW(id!),
    queryFn: () => datasetsApi.preview(id!, 50),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => datasetsApi.delete(id!),
    onSuccess: () => {
      toast.success('Dataset deleted');
      qc.invalidateQueries({ queryKey: QUERY_KEYS.DATASETS });
      navigate(ROUTES.DATASETS);
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!dataset) return <p className="text-gray-500">Dataset not found.</p>;

  const previewColumns: ColumnDef<Record<string, unknown>>[] = preview?.columns.map((col) =>
    createColumnHelper<Record<string, unknown>>().accessor(col.name as keyof Record<string, unknown>, {
      header: col.name,
      cell: (i) => <span className="font-mono text-xs">{String(i.getValue() ?? '')}</span>,
    }),
  ) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{dataset.name}</h1>
          {dataset.description && <p className="text-sm text-gray-500">{dataset.description}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" leftIcon={<Eye size={14} />}>Analyze</Button>
          <Button variant="danger" size="sm" leftIcon={<Trash2 size={14} />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: 'Rows', value: dataset.row_count?.toLocaleString() ?? '—' },
          { label: 'Columns', value: dataset.column_count ?? '—' },
          { label: 'File Size', value: formatFileSize(dataset.file_size) },
          { label: 'Uploaded', value: formatDate(dataset.created_at) },
        ].map((s) => (
          <Card key={s.label} padding="sm">
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className="mt-1 text-lg font-bold text-gray-900 dark:text-gray-100">{s.value}</p>
          </Card>
        ))}
      </div>

      {preview && (
        <Card padding="none">
          <CardHeader className="px-5 pt-5">
            <CardTitle>Data Preview</CardTitle>
            <span className="text-xs text-gray-400">First {preview.rows.length} rows</span>
          </CardHeader>
          <div className="overflow-x-auto">
            <DataTable
              data={preview.rows}
              columns={previewColumns}
              pageSize={10}
            />
          </div>
        </Card>
      )}

      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Dataset"
        description={`Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
