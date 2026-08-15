import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/utils';

interface FieldWrapperProps {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  id: string;
  children: React.ReactNode;
}

function FieldWrapper({ label, error, hint, required, id, children }: FieldWrapperProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
          {required && <span className="ml-1 text-red-500" aria-hidden>*</span>}
        </label>
      )}
      {children}
      {error && <p className="text-xs text-red-600 dark:text-red-400" role="alert">{error}</p>}
      {hint && !error && <p className="text-xs text-gray-500 dark:text-gray-400">{hint}</p>}
    </div>
  );
}

const inputBase = 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:opacity-60 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500 dark:focus:border-brand-400';
const inputError = 'border-red-500 focus:border-red-500 focus:ring-red-500/20';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftElement, rightElement, className, id, required, ...props }, ref) => {
    const inputId = id ?? `input-${Math.random().toString(36).slice(2)}`;
    return (
      <FieldWrapper label={label} error={error} hint={hint} required={required} id={inputId}>
        <div className="relative">
          {leftElement && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              {leftElement}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            required={required}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : undefined}
            className={cn(inputBase, error && inputError, leftElement && 'pl-9', rightElement && 'pr-9', className)}
            {...props}
          />
          {rightElement && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400">
              {rightElement}
            </div>
          )}
        </div>
      </FieldWrapper>
    );
  },
);
Input.displayName = 'Input';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className, id, required, ...props }, ref) => {
    const inputId = id ?? `textarea-${Math.random().toString(36).slice(2)}`;
    return (
      <FieldWrapper label={label} error={error} hint={hint} required={required} id={inputId}>
        <textarea
          ref={ref}
          id={inputId}
          required={required}
          aria-invalid={!!error}
          className={cn(inputBase, error && inputError, 'resize-y min-h-[80px]', className)}
          {...props}
        />
      </FieldWrapper>
    );
  },
);
Textarea.displayName = 'Textarea';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
  options: { value: string; label: string; disabled?: boolean }[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, hint, options, placeholder, className, id, required, ...props }, ref) => {
    const inputId = id ?? `select-${Math.random().toString(36).slice(2)}`;
    return (
      <FieldWrapper label={label} error={error} hint={hint} required={required} id={inputId}>
        <select
          ref={ref}
          id={inputId}
          required={required}
          aria-invalid={!!error}
          className={cn(inputBase, error && inputError, 'cursor-pointer', className)}
          {...props}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((o) => (
            <option key={o.value} value={o.value} disabled={o.disabled}>{o.label}</option>
          ))}
        </select>
      </FieldWrapper>
    );
  },
);
Select.displayName = 'Select';
