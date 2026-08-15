import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';
import { CommandPalette } from '@/components/layout/CommandPalette';

export function DashboardLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav />
        <main
          id="main-content"
          className="flex-1 overflow-y-auto p-4 sm:p-6"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
