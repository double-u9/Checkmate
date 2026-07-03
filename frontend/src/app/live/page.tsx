'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Activity, Camera, CameraOff, MonitorUp, Wifi, WifiOff } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import ExplanationPanel from '@/components/analysis/ExplanationPanel';
import Button from '@/components/ui/Button';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { AnalysisResponse, ThreatInfo } from '@/lib/types';

type CameraState = 'idle' | 'starting' | 'live' | 'denied' | 'stopped';

function normalizeSeverity(value: string | undefined): ThreatInfo['severity'] {
  if (value === 'low' || value === 'medium' || value === 'high' || value === 'critical') return value;
  return 'medium';
}

export default function LivePage() {
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [fps, setFps] = useState(0);
  const [message, setMessage] = useState('Camera is idle.');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const intervalRef = useRef<NodeJS.Timeout>();

  const { isConnected, status: wsStatus, sendFrame, connect, disconnect } = useWebSocket('/ws/live', {
    autoConnect: false,
    onMessage: (data) => {
      if (data.type === 'analysis' && data.fen) {
        setMessage(`Board analyzed in ${Math.round(data.processing_time_ms ?? 0)} ms.`);
        setAnalysis({
          fen: data.fen,
          evaluation: data.evaluation ?? 0,
          mate_in: data.mate_in ?? null,
          best_move: {
            move_uci: '',
            move_san: data.best_move ?? '?',
            score: data.evaluation ?? 0,
            mate_in: data.mate_in ?? null,
            is_best: true,
            classification: 'best',
          },
          top_lines: [],
          threats: (data.threats ?? []).map((threat) => ({
            type: threat.type || '',
            description: threat.description || '',
            severity: normalizeSeverity(threat.severity),
            squares: threat.squares || [],
          })),
          explanation: data.explanation ?? '',
          strategic_themes: [],
          position_type: 'middlegame',
          heatmap: data.heatmap ?? null,
        });
      }

      if (data.type === 'no_board') setMessage(data.message || 'No stable board detected yet.');
      if (data.type === 'error') setMessage(data.message || 'Live analysis returned an error.');
    },
  });

  const stopWebcam = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) clearInterval(intervalRef.current);
    disconnect();
    setFps(0);
    setCameraState('stopped');
    setMessage('Camera stopped.');
  }, [disconnect]);

  const startWebcam = useCallback(async () => {
    setCameraState('starting');
    setMessage('Requesting camera access...');
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera access is not available in this browser context.');
      }

      const stream = await Promise.race([
        navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
          audio: false,
        }),
        new Promise<never>((_, reject) => {
          window.setTimeout(() => reject(new Error('Camera request timed out. Check browser permissions.')), 12000);
        }),
      ]);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => undefined);
      }

      connect();
      setCameraState('live');
      setMessage('Camera connected. Hold the board steady for detection.');
    } catch (err: any) {
      setCameraState('denied');
      setMessage(err.message || 'Camera access was denied or unavailable.');
    }
  }, [connect]);

  useEffect(() => {
    const videoElement = videoRef.current;
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (videoElement?.srcObject) {
        const tracks = (videoElement.srcObject as MediaStream).getTracks();
        tracks.forEach((track) => track.stop());
      }
      disconnect();
    };
  }, [disconnect]);

  useEffect(() => {
    if (cameraState !== 'live' || !isConnected) return undefined;

    let frameCount = 0;
    const startTime = Date.now();

    intervalRef.current = setInterval(() => {
      if (!videoRef.current || !canvasRef.current) return;
      const context = canvasRef.current.getContext('2d');
      if (!context || videoRef.current.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;

      canvasRef.current.width = 960;
      canvasRef.current.height = 540;
      context.drawImage(videoRef.current, 0, 0, 960, 540);
      const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.72);
      const base64 = dataUrl.split(',')[1];
      sendFrame(base64);

      frameCount += 1;
      const elapsed = (Date.now() - startTime) / 1000;
      setFps(Math.round(frameCount / elapsed));
    }, 220);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [cameraState, isConnected, sendFrame]);

  const isStreaming = cameraState === 'live' || cameraState === 'starting';

  return (
    <AppShell
      title="Live board"
      eyebrow="Computer vision"
      description="Stream a physical board to the backend WebSocket for board detection, FEN extraction, engine analysis, and tactical commentary."
      status={
        <StatusBadge tone={isConnected ? 'success' : wsStatus === 'reconnecting' ? 'warning' : cameraState === 'denied' ? 'danger' : 'neutral'} dot>
          WebSocket {wsStatus}
        </StatusBadge>
      }
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <section className="space-y-5">
          <GlassCard hover={false} id="webcam-feed" className="p-3 sm:p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 px-1">
              <div>
                <h2 className="text-base font-semibold text-white">Camera feed</h2>
                <p className="mt-1 text-sm text-slate-400">Keep all four board corners visible for best results.</p>
              </div>
              <Button
                variant={cameraState === 'live' ? 'danger' : 'primary'}
                icon={cameraState === 'live' ? <CameraOff className="h-4 w-4" aria-hidden="true" /> : <Camera className="h-4 w-4" aria-hidden="true" />}
                onClick={cameraState === 'live' ? stopWebcam : startWebcam}
                isLoading={cameraState === 'starting'}
              >
                {cameraState === 'live' ? 'Stop camera' : cameraState === 'starting' ? 'Starting' : 'Start camera'}
              </Button>
            </div>

            <div className="relative aspect-video overflow-hidden rounded-xl border border-slate-700 bg-slate-950">
              <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" aria-label="Live camera feed" />
              <canvas ref={canvasRef} className="hidden" />

              {!isStreaming && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/92 p-6 text-center">
                  <MonitorUp className="h-9 w-9 text-cyan-200" aria-hidden="true" />
                  <h3 className="mt-4 text-sm font-semibold text-white">Start the camera to detect a board</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{message}</p>
                </div>
              )}

              {cameraState === 'starting' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/82 p-6 text-center">
                  <Camera className="h-9 w-9 text-cyan-200" aria-hidden="true" />
                  <h3 className="mt-4 text-sm font-semibold text-white">Waiting for camera permission</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{message}</p>
                </div>
              )}

              <div className="absolute right-3 top-3">
                <StatusBadge tone={isConnected ? 'success' : wsStatus === 'reconnecting' ? 'warning' : cameraState === 'denied' ? 'danger' : 'neutral'}>
                  {cameraState === 'denied' ? 'Camera blocked' : isConnected ? 'Connected' : wsStatus}
                </StatusBadge>
              </div>
            </div>
          </GlassCard>

          <div className="grid gap-3 md:grid-cols-3">
            <GlassCard hover={false}>
              <Activity className="h-4 w-4 text-cyan-200" aria-hidden="true" />
              <p className="mt-3 text-sm font-semibold text-white">Stream</p>
              <p className="mt-1 text-sm text-slate-400">{message}</p>
            </GlassCard>
            <GlassCard hover={false}>
              <Camera className="h-4 w-4 text-cyan-200" aria-hidden="true" />
              <p className="mt-3 text-sm font-semibold text-white">{fps} FPS</p>
              <p className="mt-1 text-sm text-slate-400">Frames are throttled for API latency.</p>
            </GlassCard>
            <GlassCard hover={false}>
              {isConnected ? <Wifi className="h-4 w-4 text-emerald-200" aria-hidden="true" /> : <WifiOff className="h-4 w-4 text-amber-200" aria-hidden="true" />}
              <p className="mt-3 text-sm font-semibold text-white">Connection</p>
              <p className="mt-1 text-sm text-slate-400">WebSocket is {wsStatus}.</p>
            </GlassCard>
          </div>
        </section>

        <aside className="space-y-5">
          <ExplanationPanel analysis={analysis} />
          <GlassCard hover={false}>
            <h2 className="text-sm font-semibold text-white">Capture guidance</h2>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
              <li>Reduce glare on glossy boards and screens.</li>
              <li>Pause briefly after each move so detection can stabilize.</li>
              <li>Use even lighting and a direct angle when possible.</li>
            </ul>
          </GlassCard>
        </aside>
      </div>
    </AppShell>
  );
}
