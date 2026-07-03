'use client';

import { useEffect } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';
import Button from '@/components/ui/Button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Page error:', error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <section className="glass-card max-w-md p-6 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-red-400/30 bg-red-500/15 text-red-200">
          <AlertTriangle className="h-6 w-6" aria-hidden="true" />
        </div>
        <h1 className="mt-4 text-xl font-semibold text-white">Aethelred could not render this view</h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          {error.message || 'An unexpected interface error occurred. Your analysis data is safe.'}
        </p>
        <Button className="mt-5" variant="primary" icon={<RotateCcw className="h-4 w-4" aria-hidden="true" />} onClick={reset}>
          Try again
        </Button>
      </section>
    </main>
  );
}
