'use client';

import type { ReactNode } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import StatusBadge from '@/components/ui/StatusBadge';
import { useBackendHealth } from '@/hooks/useBackendHealth';

interface AppShellProps {
  children: ReactNode;
  title: string;
  eyebrow?: string;
  description?: string;
  status?: ReactNode;
}

export default function AppShell({ children, title, eyebrow, description, status }: AppShellProps) {
  const backend = useBackendHealth();

  return (
    <div className="relative min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-cyan-400 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-slate-950"
      >
        Skip to content
      </a>
      <Sidebar backendStatus={backend.status} />
      <main id="main-content" className="relative z-10 mx-auto min-h-screen max-w-[1760px] px-4 pb-24 pt-5 sm:px-6 lg:pl-80 lg:pr-8">
        <header className="mb-5 flex flex-col gap-4 border-b border-slate-800/80 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300/70">{eyebrow}</p>}
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h1>
            {description && <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{description}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={backend.status === 'online' ? 'success' : backend.status === 'offline' ? 'danger' : 'warning'} dot>
              API {backend.status}
            </StatusBadge>
            {status}
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
