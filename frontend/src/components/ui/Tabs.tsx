import { useState, useRef, useEffect } from 'react';
import { cn } from '@/utils';
import { ChevronDown } from 'lucide-react';

// ─── Tabs ─────────────────────────────────────────────────────────────────────

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
  variant?: 'line' | 'pill';
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, variant = 'line', className }: TabsProps) {
  return (
    <div
      role="tablist"
      className={cn(
        variant === 'line' && 'flex border-b border-gray-200 dark:border-gray-700',
        variant === 'pill' && 'flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800',
        className,
      )}
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          disabled={tab.disabled}
          onClick={() => onChange(tab.id)}
          className={cn(
            'inline-flex items-center gap-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
            variant === 'line' && [
              'border-b-2 px-4 py-2.5 -mb-px',
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
            ],
            variant === 'pill' && [
              'rounded-md px-3 py-1.5',
              activeTab === tab.id
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
            ],
          )}
        >
          {tab.icon}
          {tab.label}
          {tab.badge !== undefined && (
            <span className="rounded-full bg-gray-200 px-1.5 py-0.5 text-xs dark:bg-gray-600">
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ─── Accordion ────────────────────────────────────────────────────────────────

interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  defaultOpen?: string[];
  multiple?: boolean;
}

export function Accordion({ items, defaultOpen = [], multiple = false }: AccordionProps) {
  const [open, setOpen] = useState<Set<string>>(new Set(defaultOpen));

  const toggle = (id: string) => {
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); }
      else { if (!multiple) next.clear(); next.add(id); }
      return next;
    });
  };

  return (
    <div className="divide-y divide-gray-200 rounded-xl border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
      {items.map((item) => (
        <div key={item.id}>
          <button
            onClick={() => toggle(item.id)}
            aria-expanded={open.has(item.id)}
            className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 hover:bg-gray-50 dark:text-gray-100 dark:hover:bg-gray-700/50"
          >
            {item.title}
            <ChevronDown
              size={16}
              className={cn('text-gray-400 transition-transform', open.has(item.id) && 'rotate-180')}
            />
          </button>
          {open.has(item.id) && (
            <div className="px-4 pb-4 text-sm text-gray-600 dark:text-gray-400">{item.content}</div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Tooltip ──────────────────────────────────────────────────────────────────

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, side = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const positions = {
    top: 'bottom-full left-1/2 mb-2 -translate-x-1/2',
    bottom: 'top-full left-1/2 mt-2 -translate-x-1/2',
    left: 'right-full top-1/2 mr-2 -translate-y-1/2',
    right: 'left-full top-1/2 ml-2 -translate-y-1/2',
  };
  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className={cn(
            'pointer-events-none absolute z-50 whitespace-nowrap rounded-lg bg-gray-900 px-2.5 py-1.5 text-xs text-white shadow-lg dark:bg-gray-700',
            positions[side],
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}

// ─── Dropdown ─────────────────────────────────────────────────────────────────

interface DropdownItem {
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  href?: string;
  danger?: boolean;
  disabled?: boolean;
  divider?: boolean;
}

interface DropdownProps {
  trigger: React.ReactElement;
  items: DropdownItem[];
  align?: 'left' | 'right';
}

export function Dropdown({ trigger, items, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="relative inline-block">
      <div onClick={() => setOpen((o) => !o)}>{trigger}</div>
      {open && (
        <div
          className={cn(
            'absolute z-50 mt-1 min-w-[160px] rounded-xl border border-gray-200 bg-white py-1 shadow-modal dark:border-gray-700 dark:bg-gray-800',
            align === 'right' ? 'right-0' : 'left-0',
          )}
        >
          {items.map((item, i) =>
            item.divider ? (
              <hr key={i} className="my-1 border-gray-200 dark:border-gray-700" />
            ) : (
              <button
                key={i}
                disabled={item.disabled}
                onClick={() => { item.onClick?.(); setOpen(false); }}
                className={cn(
                  'flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors',
                  'disabled:pointer-events-none disabled:opacity-50',
                  item.danger
                    ? 'text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700',
                )}
              >
                {item.icon && <span className="text-gray-400">{item.icon}</span>}
                {item.label}
              </button>
            ),
          )}
        </div>
      )}
    </div>
  );
}