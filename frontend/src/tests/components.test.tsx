import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { render } from './utils';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge, Card, Spinner, EmptyState, ProgressBar } from '@/components/ui/Card';

// ─── Button ───────────────────────────────────────────────────────────────────

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('shows loading spinner when loading=true', () => {
    render(<Button loading>Submit</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });

  it('calls onClick handler', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('does not call onClick when disabled', () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies danger variant class', () => {
    render(<Button variant="danger">Delete</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-red-600');
  });
});

// ─── Input ────────────────────────────────────────────────────────────────────

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" id="email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Input label="Email" id="email" error="Invalid email" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Invalid email');
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows hint when no error', () => {
    render(<Input label="Email" id="email" hint="Enter your work email" />);
    expect(screen.getByText('Enter your work email')).toBeInTheDocument();
  });

  it('accepts user input', () => {
    render(<Input label="Name" id="name" />);
    const input = screen.getByLabelText('Name');
    fireEvent.change(input, { target: { value: 'John' } });
    expect(input).toHaveValue('John');
  });
});

// ─── Badge ────────────────────────────────────────────────────────────────────

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('applies success variant', () => {
    render(<Badge variant="success">OK</Badge>);
    expect(screen.getByText('OK')).toHaveClass('bg-green-100');
  });

  it('renders dot when dot=true', () => {
    const { container } = render(<Badge dot>Live</Badge>);
    expect(container.querySelector('.rounded-full.bg-current')).toBeInTheDocument();
  });
});

// ─── Card ─────────────────────────────────────────────────────────────────────

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies hover class when hover=true', () => {
    const { container } = render(<Card hover>Content</Card>);
    expect(container.firstChild).toHaveClass('cursor-pointer');
  });
});

// ─── Spinner ──────────────────────────────────────────────────────────────────

describe('Spinner', () => {
  it('has accessible role and label', () => {
    render(<Spinner />);
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument();
  });
});

// ─── EmptyState ───────────────────────────────────────────────────────────────

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(<EmptyState title="No data" description="Upload a dataset to get started." />);
    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('Upload a dataset to get started.')).toBeInTheDocument();
  });

  it('renders action when provided', () => {
    render(<EmptyState title="Empty" action={<button>Add Item</button>} />);
    expect(screen.getByRole('button', { name: 'Add Item' })).toBeInTheDocument();
  });
});

// ─── ProgressBar ──────────────────────────────────────────────────────────────

describe('ProgressBar', () => {
  it('renders with correct aria attributes', () => {
    render(<ProgressBar value={60} max={100} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '60');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('shows percentage when showValue=true', () => {
    render(<ProgressBar value={75} showValue />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('clamps value to 0-100', () => {
    render(<ProgressBar value={150} />);
    const inner = document.querySelector('[style*="width"]') as HTMLElement;
    expect(inner?.style.width).toBe('100%');
  });
});
