/* WebSocket hook for real-time analysis */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import type { WSAnalysisMessage } from '@/lib/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onMessage?: (data: WSAnalysisMessage) => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(path: string = '/ws/live', options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error'>('idle');
  const [lastMessage, setLastMessage] = useState<WSAnalysisMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const shouldReconnectRef = useRef(false);

  // P10 fix: Store options in refs to avoid recreating callbacks on every render.
  // Object literals in function args create new references every render, causing
  // infinite reconnection loops when used in dependency arrays.
  const onMessageRef = useRef(options.onMessage);
  const onErrorRef = useRef(options.onError);
  const autoConnectRef = useRef(options.autoConnect);

  // Keep refs up to date without triggering re-renders
  useEffect(() => {
    onMessageRef.current = options.onMessage;
    onErrorRef.current = options.onError;
    autoConnectRef.current = options.autoConnect;
  }, [options.onMessage, options.onError, options.autoConnect]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    shouldReconnectRef.current = true;
    setStatus(wsRef.current ? 'reconnecting' : 'connecting');

    const ws = new WebSocket(`${WS_URL}${path}`);

    ws.onopen = () => {
      setIsConnected(true);
      setStatus('connected');
      console.log('[WS] Connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSAnalysisMessage;
        setLastMessage(data);
        onMessageRef.current?.(data);
      } catch (err) {
        console.error('[WS] Parse error:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('[WS] Error:', error);
      setStatus('error');
      onErrorRef.current?.(error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      if (shouldReconnectRef.current) {
        setStatus('reconnecting');
        console.log('[WS] Disconnected, reconnecting in 3s...');
        reconnectTimeout.current = setTimeout(connect, 3000);
      } else {
        setStatus('disconnected');
      }
    };

    wsRef.current = ws;
  }, [path]); // P10 fix: Only depends on `path`, not the unstable `options` object

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
    setStatus('disconnected');
  }, []);

  const sendFrame = useCallback((base64Data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'frame', data: base64Data }));
    }
  }, []);

  // P10 fix: Proper dependency array including connect and disconnect
  useEffect(() => {
    if (autoConnectRef.current !== false) connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, status, lastMessage, connect, disconnect, sendFrame };
}
