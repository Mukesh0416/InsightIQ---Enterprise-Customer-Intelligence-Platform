import { Outlet } from 'react-router-dom';
import { Brain } from 'lucide-react';

export function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-brand-950 via-brand-900 to-gray-900 px-4 py-12">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500">
          <Brain size={22} className="text-white" />
        </div>
        <span className="text-2xl font-bold text-white">InsightIQ</span>
      </div>

      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-sm">
        <Outlet />
      </div>

      <p className="mt-6 text-xs text-white/40">
        © {new Date().getFullYear()} InsightIQ. Enterprise Customer Intelligence Platform.
      </p>
    </div>
  );
}
