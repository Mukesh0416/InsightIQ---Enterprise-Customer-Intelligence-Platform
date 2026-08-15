import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ArrowRight, Database, FileText, Brain, BarChart3, X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { createPortal } from 'react-dom';
import { cn, debounce } from '@/utils';
import { useUIStore } from '@/stores/uiStore';
import { searchApi } from '@/api';
import { QUERY_KEYS, ROUTES } from '@/constants';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  dataset: <Database size={14} />,
  report: <FileText size={14} />,
  model: <Brain size={14} />,
  audit: <BarChart3 size={14} />,
};

const QUICK_ACTIONS = [
  { label: 'Go to Dashboard', to: ROUTES.DASHBOARD, icon: <BarChart3 size={14} /> },
  { label: 'Upload Dataset', to: ROUTES.DATASET_UPLOAD, icon: <Database size={14} /> },
  { label: 'Train Model', to: ROUTES.AI_TRAIN, icon: <Brain size={14} /> },
  { label: 'Generate Report', to: ROUTES.REPORTS, icon: <FileText size={14} /> },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const debouncedSet = debounce((v: unknown) => setDebouncedQuery(v as string), 300);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (e.key === 'Escape') setCommandPaletteOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [setCommandPaletteOpen]);

  useEffect(() => {
    if (commandPaletteOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setDebouncedQuery('');
    }
  }, [commandPaletteOpen]);

  const { data: results, isFetching } = useQuery({
    queryKey: QUERY_KEYS.SEARCH(debouncedQuery),
    queryFn: () => searchApi.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const handleSelect = (url: string) => {
    navigate(url);
    setCommandPaletteOpen(false);
  };

  return createPortal(
    <AnimatePresence>
      {commandPaletteOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setCommandPaletteOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -8 }}
            transition={{ duration: 0.15 }}
            className="relative z-10 w-full max-w-xl overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-modal dark:border-gray-700 dark:bg-gray-800"
          >
            <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
              <Search size={16} className="shrink-0 text-gray-400" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => { setQuery(e.target.value); debouncedSet(e.target.value); }}
                placeholder="Search datasets, models, reports…"
                className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 outline-none dark:text-gray-100"
                aria-label="Global search"
              />
              {isFetching && <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-brand-600" />}
              <button onClick={() => setCommandPaletteOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={16} />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto p-2">
              {debouncedQuery.length < 2 ? (
                <div>
                  <p className="px-3 py-1.5 text-2xs font-semibold uppercase tracking-wide text-gray-400">Quick Actions</p>
                  {QUICK_ACTIONS.map((a) => (
                    <button
                      key={a.to}
                      onClick={() => handleSelect(a.to)}
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                    >
                      <span className="text-gray-400">{a.icon}</span>
                      {a.label}
                      <ArrowRight size={12} className="ml-auto text-gray-300" />
                    </button>
                  ))}
                </div>
              ) : results?.results.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-500">No results for "{debouncedQuery}"</p>
              ) : (
                <div>
                  <p className="px-3 py-1.5 text-2xs font-semibold uppercase tracking-wide text-gray-400">
                    {results?.total} results
                  </p>
                  {results?.results.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => handleSelect(r.url)}
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <span className={cn('shrink-0 text-gray-400')}>{TYPE_ICONS[r.type] ?? <ArrowRight size={14} />}</span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{r.title}</p>
                        {r.description && <p className="truncate text-xs text-gray-500">{r.description}</p>}
                      </div>
                      <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-2xs text-gray-500 dark:bg-gray-700">{r.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-gray-200 px-4 py-2 dark:border-gray-700">
              <div className="flex items-center gap-4 text-2xs text-gray-400">
                <span><kbd className="rounded bg-gray-100 px-1 dark:bg-gray-700">↑↓</kbd> navigate</span>
                <span><kbd className="rounded bg-gray-100 px-1 dark:bg-gray-700">↵</kbd> select</span>
                <span><kbd className="rounded bg-gray-100 px-1 dark:bg-gray-700">esc</kbd> close</span>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
