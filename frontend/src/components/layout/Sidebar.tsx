'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Brain, Crown, Home, UserRound, Video } from 'lucide-react';
import StatusBadge from '@/components/ui/StatusBadge';
import { cn } from '@/lib/cn';
import type { BackendState } from '@/hooks/useBackendHealth';

const NAV_ITEMS = [
  { href: '/', icon: Home, label: 'Dashboard', desc: 'Workspace' },
  { href: '/analysis', icon: Brain, label: 'Analysis', desc: 'Deep engine' },
  { href: '/live', icon: Video, label: 'Live', desc: 'Webcam' },
  { href: '/profiles', icon: UserRound, label: 'Profiles', desc: 'Opponent intel' },
];

function backendTone(status: BackendState) {
  if (status === 'online') return 'success';
  if (status === 'offline') return 'danger';
  return 'warning';
}

export default function Sidebar({ backendStatus = 'checking' }: { backendStatus?: BackendState }) {
  const pathname = usePathname();

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-800/80 bg-slate-950/92 px-4 py-5 backdrop-blur-xl lg:block">
        <div className="flex h-full flex-col">
          <Link href="/" className="flex items-center gap-3 rounded-lg px-2 py-2 focus-visible:outline-cyan-300">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan-300/40 bg-cyan-400/15 text-cyan-200">
              <Crown className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight text-white">Aethelred</p>
              <p className="text-xs text-slate-400">Chess intelligence suite</p>
            </div>
          </Link>

          <nav className="mt-8 space-y-1" aria-label="Primary navigation">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={`${item.label}: ${item.desc}`}
                  aria-current={isActive ? 'page' : undefined}
                  className={cn(
                    'group relative flex items-center gap-3 rounded-lg px-3 py-3 transition-colors',
                    isActive ? 'bg-cyan-400/10 text-white' : 'text-slate-400 hover:bg-slate-800/65 hover:text-white',
                  )}
                >
                  {isActive && (
                    <motion.span
                      layoutId="desktop-active-nav"
                      className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-cyan-300"
                    />
                  )}
                  <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border', isActive ? 'border-cyan-300/30 bg-slate-950/80 text-cyan-200' : 'border-transparent')}>
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="block text-sm font-semibold">{item.label}</span>
                    <span className="block text-xs text-slate-500">{item.desc}</span>
                  </span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <StatusBadge tone={backendTone(backendStatus)} dot>
                Backend {backendStatus}
              </StatusBadge>
              <p className="mt-3 text-xs leading-5 text-slate-400">
                Analysis, vision, live board detection, and profiling use the FastAPI service.
              </p>
            </div>
            <div className="flex items-center gap-2 px-2 text-[11px] text-slate-500">
              <Activity className="h-3.5 w-3.5" aria-hidden="true" />
              <span>v1.0 tactical workspace</span>
            </div>
          </div>
        </div>
      </aside>

      <nav className="fixed inset-x-3 bottom-3 z-50 grid grid-cols-4 rounded-2xl border border-slate-700/80 bg-slate-950/95 p-1 shadow-2xl backdrop-blur-xl lg:hidden" aria-label="Primary navigation">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={`${item.label}: ${item.desc}`}
              aria-current={isActive ? 'page' : undefined}
              className={cn('relative flex min-h-12 flex-col items-center justify-center rounded-xl px-2 py-1 text-[11px] font-semibold transition-colors', isActive ? 'text-cyan-200' : 'text-slate-500 hover:text-white')}
            >
              {isActive && <motion.span layoutId="mobile-active-nav" className="absolute inset-0 rounded-xl bg-cyan-400/10" />}
              <Icon className="relative h-4 w-4" aria-hidden="true" />
              <span className="relative mt-1 truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
