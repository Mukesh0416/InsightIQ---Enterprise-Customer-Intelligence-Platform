import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { authApi } from '@/api';
import { ROUTES } from '@/constants';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

// ─── Register ─────────────────────────────────────────────────────────────────

const registerSchema = z.object({
  full_name: z.string().min(2, 'Full name must be at least 2 characters'),
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  organization_name: z.string().optional(),
});

type RegisterData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterData>({
    resolver: zodResolver(registerSchema),
  });

  const mutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      toast.success('Account created! Please check your email to verify.');
      navigate(ROUTES.LOGIN);
    },
    onError: () => toast.error('Registration failed. Email may already be in use.'),
  });

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-white">Create account</h1>
      <p className="mb-6 text-sm text-white/60">Start your free InsightIQ workspace</p>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="flex flex-col gap-4">
        <Input label="Full name" placeholder="Jane Smith" error={errors.full_name?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('full_name')} id="full_name" />
        <Input label="Work email" type="email" placeholder="you@company.com" error={errors.email?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('email')} id="email" />
        <Input label="Password" type="password" placeholder="Min. 8 characters" error={errors.password?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('password')} id="password" />
        <Input label="Organization name (optional)" placeholder="Acme Corp" error={errors.organization_name?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('organization_name')} id="organization_name" />

        <Button type="submit" loading={mutation.isPending} className="mt-2 w-full">
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-white/50">
        Already have an account?{' '}
        <Link to={ROUTES.LOGIN} className="text-brand-400 hover:text-brand-300 hover:underline">Sign in</Link>
      </p>
    </div>
  );
}

// ─── Forgot Password ──────────────────────────────────────────────────────────

const forgotSchema = z.object({ email: z.string().email('Enter a valid email address') });

export function ForgotPasswordPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<{ email: string }>({
    resolver: zodResolver(forgotSchema),
  });

  const mutation = useMutation({
    mutationFn: ({ email }: { email: string }) => authApi.forgotPassword(email),
    onSuccess: () => toast.success('If that email exists, a reset link has been sent.'),
  });

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-white">Reset password</h1>
      <p className="mb-6 text-sm text-white/60">Enter your email and we'll send a reset link</p>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="flex flex-col gap-4">
        <Input label="Email address" type="email" placeholder="you@company.com" error={errors.email?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('email')} id="email" />
        <Button type="submit" loading={mutation.isPending} className="mt-2 w-full">
          Send reset link
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-white/50">
        <Link to={ROUTES.LOGIN} className="text-brand-400 hover:text-brand-300 hover:underline">Back to sign in</Link>
      </p>
    </div>
  );
}

// ─── Reset Password ───────────────────────────────────────────────────────────

const resetSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] });

type ResetData = z.infer<typeof resetSchema>;

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';

  const { register, handleSubmit, formState: { errors } } = useForm<ResetData>({
    resolver: zodResolver(resetSchema),
  });

  const mutation = useMutation({
    mutationFn: (d: ResetData) => authApi.resetPassword(token, d.password),
    onSuccess: () => {
      toast.success('Password reset successfully. Please sign in.');
      navigate(ROUTES.LOGIN);
    },
    onError: () => toast.error('Reset link is invalid or expired.'),
  });

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-white">New password</h1>
      <p className="mb-6 text-sm text-white/60">Choose a strong password for your account</p>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="flex flex-col gap-4">
        <Input label="New password" type="password" placeholder="Min. 8 characters" error={errors.password?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('password')} id="password" />
        <Input label="Confirm password" type="password" placeholder="Repeat password" error={errors.confirm?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20"
          {...register('confirm')} id="confirm" />
        <Button type="submit" loading={mutation.isPending} className="mt-2 w-full">
          Set new password
        </Button>
      </form>
    </div>
  );
}

// ─── Unauthorized / Forbidden ─────────────────────────────────────────────────

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 text-center">
      <p className="text-6xl font-bold text-brand-600">401</p>
      <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Authentication Required</h1>
      <p className="mt-2 text-gray-500">Please sign in to access this page.</p>
      <Link to={ROUTES.LOGIN} className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
        Sign in
      </Link>
    </div>
  );
}

export function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 text-center">
      <p className="text-6xl font-bold text-red-500">403</p>
      <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Access Denied</h1>
      <p className="mt-2 text-gray-500">You don't have permission to view this page.</p>
      <Link to={ROUTES.DASHBOARD} className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
        Go to Dashboard
      </Link>
    </div>
  );
}
