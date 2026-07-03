'use client';

import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';

export type BackendState = 'checking' | 'online' | 'offline';

export function useBackendHealth(intervalMs = 15000) {
  const [status, setStatus] = useState<BackendState>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const check = useCallback(async () => {
    try {
      await api.health();
      setStatus('online');
    } catch {
      setStatus('offline');
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    void check();
    const interval = window.setInterval(() => void check(), intervalMs);
    return () => window.clearInterval(interval);
  }, [check, intervalMs]);

  return { status, lastChecked, refresh: check };
}
