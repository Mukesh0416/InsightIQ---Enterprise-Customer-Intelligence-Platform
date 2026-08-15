import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type RowSelectionState,
} from '@tanstack/react-table';
import { useState } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/utils';
import { Button } from './Button';
import { Input, Select } from './Input';
import { Spinner, EmptyState } from './Card';
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from '@/constants';

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T, any>[];
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  selectable?: boolean;
  onSelectionChange?: (rows: T[]) => void;
  emptyTitle?: string;
  emptyDescription?: string;
  toolbar?: React.ReactNode;
  pageSize?: number;
}

export function DataTable<T>({
  data,
  columns,
  loading,
  searchable,
  searchPlaceholder = 'Search…',
  selectable,
  onSelectionChange,
  emptyTitle = 'No results',
  emptyDescription,
  toolbar,
  pageSize: initialPageSize = DEFAULT_PAGE_SIZE,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter, rowSelection },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: (updater) => {
      const next = typeof updater === 'function' ? updater(rowSelection) : updater;
      setRowSelection(next);
      if (onSelectionChange) {
        const selected = table.getSelectedRowModel().rows.map((r) => r.original);
        onSelectionChange(selected);
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    enableRowSelection: selectable,
    initialState: { pagination: { pageSize: initialPageSize } },
  });

  return (
    <div className="flex flex-col gap-3">
      {(searchable || toolbar) && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {searchable && (
            <Input
              placeholder={searchPlaceholder}
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="max-w-xs"
              id="table-search"
            />
          )}
          {toolbar && <div className="flex items-center gap-2">{toolbar}</div>}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm" role="grid">
          <thead className="bg-gray-50 dark:bg-gray-800/60">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
                    style={{ width: header.getSize() !== 150 ? header.getSize() : undefined }}
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={cn('flex items-center gap-1', header.column.getCanSort() && 'cursor-pointer select-none')}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className="text-gray-400">
                            {header.column.getIsSorted() === 'asc' ? <ChevronUp size={14} /> :
                             header.column.getIsSorted() === 'desc' ? <ChevronDown size={14} /> :
                             <ChevronsUpDown size={14} />}
                          </span>
                        )}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="py-16 text-center">
                  <Spinner className="mx-auto" />
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <EmptyState title={emptyTitle} description={emptyDescription} />
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className={cn(
                    'transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/40',
                    row.getIsSelected() && 'bg-brand-50 dark:bg-brand-900/10',
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <Select
            id="page-size"
            options={PAGE_SIZE_OPTIONS.map((n) => ({ value: String(n), label: String(n) }))}
            value={String(table.getState().pagination.pageSize)}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
            className="w-20 py-1"
          />
        </div>
        <span>
          {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}–
          {Math.min(
            (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
            table.getFilteredRowModel().rows.length,
          )}{' '}
          of {table.getFilteredRowModel().rows.length}
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="xs"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            aria-label="Previous page"
          >
            <ChevronLeft size={16} />
          </Button>
          <Button
            variant="ghost"
            size="xs"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            aria-label="Next page"
          >
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </div>
  );
}