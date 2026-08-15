import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { authApi } from '@/api';
import { useAuthStore } from '@/stores/authStore';
import { ROUTES, QUERY_KEYS } from '@/constants';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  remember_me: z.boolean().optional(),
});

type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { setTokens, setUser } = useAuthStore();
  const qc = useQueryClient();

  const from = (location.state as { from?: string })?.from ?? ROUTES.DASHBOARD;

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { remember_me: false },
  });

  const mutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      const user = await authApi.me();
      setUser(user);
      qc.setQueryData(QUERY_KEYS.ME, user);
      toast.success(`Welcome back, ${user.full_name.split(' ')[0]}!`);
      navigate(from, { replace: true });
    },
    onError: () => toast.error('Invalid email or password'),
  });

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-white">Sign in</h1>
      <p className="mb-6 text-sm text-white/60">Enter your credentials to access your workspace</p>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="flex flex-col gap-4">
        <Input
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@company.com"
          error={errors.email?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20 focus:border-brand-400"
          {...register('email')}
          id="email"
        />

        <Input
          label="Password"
          type={showPassword ? 'text' : 'password'}
          autoComplete="current-password"
          placeholder="••••••••"
          error={errors.password?.message}
          className="bg-white/10 text-white placeholder-white/30 border-white/20 focus:border-brand-400"
          rightElement={
            <button type="button" onClick={() => setShowPassword((s) => !s)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          }
          {...register('password')}
          id="password"
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer">
            <input type="checkbox" {...register('remember_me')} className="rounded border-white/20 bg-white/10" />
            Remember me
          </label>
          <Link to={ROUTES.FORGOT_PASSWORD} className="text-sm text-brand-400 hover:text-brand-300 hover:underline">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" loading={mutation.isPending} className="mt-2 w-full">
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-white/50">
        Don't have an account?{' '}
        <Link to={ROUTES.REGISTER} className="text-brand-400 hover:text-brand-300 hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
