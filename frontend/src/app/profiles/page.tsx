'use client';

import { useMemo, useState } from 'react';
import { ClipboardList, Search, UserRound } from 'lucide-react';
import AppShell from '@/components/layout/AppShell';
import ProfileCard from '@/components/profiler/ProfileCard';
import Button from '@/components/ui/Button';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import api from '@/lib/api';
import type { ProfileResponse } from '@/lib/types';

export default function ProfilesPage() {
  const [playerName, setPlayerName] = useState('');
  const [pgnInput, setPgnInput] = useState('');
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parsedGames = useMemo(() => pgnInput.split(/\n\s*\n(?=\[)/).map((game) => game.trim()).filter(Boolean), [pgnInput]);

  const handleAnalyze = async () => {
    if (!playerName.trim() || parsedGames.length === 0) {
      setError('Enter a player name and at least one PGN game.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const result = await api.analyzeProfile(playerName.trim(), parsedGames);
      setProfile(result);
    } catch (err: any) {
      setError(err.message || 'Profile analysis failed. Check that the backend is online.');
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell
      title="Opponent intelligence"
      eyebrow="Profiler"
      description="Convert PGN history into a practical scouting report: style, risk appetite, phase strengths, and counter-strategy."
      status={<StatusBadge tone={profile ? 'success' : 'neutral'}>{profile ? 'Profile generated' : 'Awaiting PGN'}</StatusBadge>}
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.82fr)]">
        <section className="space-y-5">
          <GlassCard id="profile-input" hover={false} className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-purple-200/70">Profile source</p>
                <h2 className="mt-1 text-lg font-semibold text-white">PGN game sample</h2>
              </div>
              <StatusBadge tone={parsedGames.length > 0 ? 'info' : 'neutral'}>
                {parsedGames.length} parsed game{parsedGames.length === 1 ? '' : 's'}
              </StatusBadge>
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(220px,280px)_1fr]">
              <label className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Player name</span>
                <input
                  type="text"
                  value={playerName}
                  onChange={(event) => setPlayerName(event.target.value)}
                  className="control-field h-11 w-full px-3 text-sm"
                  placeholder="Player name"
                  id="player-name-input"
                  autoComplete="name"
                />
              </label>

              <label className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">PGN games</span>
                <textarea
                  value={pgnInput}
                  onChange={(event) => setPgnInput(event.target.value)}
                  className="control-field min-h-72 w-full resize-y px-3 py-3 font-mono text-xs leading-6"
                  placeholder={'[Event "Example"]\n[White "Opponent"]\n[Black "You"]\n\n1. e4 e5 2. Nf3 Nc6'}
                  id="pgn-input"
                  spellCheck={false}
                  aria-describedby={error ? 'profile-error' : undefined}
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="primary"
                icon={<Search className="h-4 w-4" aria-hidden="true" />}
                isLoading={loading}
                onClick={handleAnalyze}
              >
                {loading ? 'Profiling' : 'Analyze opponent'}
              </Button>
              {error && (
                <StatusBadge id="profile-error" tone="danger" className="normal-case tracking-normal">
                  {error}
                </StatusBadge>
              )}
            </div>
          </GlassCard>

          <div className="grid gap-3 md:grid-cols-3">
            <GlassCard hover={false}>
              <ClipboardList className="h-4 w-4 text-cyan-200" aria-hidden="true" />
              <p className="mt-3 text-sm font-semibold text-white">{parsedGames.length} games</p>
              <p className="mt-1 text-sm text-slate-400">More games improve confidence and reduce noisy style signals.</p>
            </GlassCard>
            <GlassCard hover={false}>
              <UserRound className="h-4 w-4 text-purple-200" aria-hidden="true" />
              <p className="mt-3 text-sm font-semibold text-white">{profile?.psychological_profile?.confidence ?? 'Pending'}</p>
              <p className="mt-1 text-sm text-slate-400">Profiler confidence appears after analysis.</p>
            </GlassCard>
            <GlassCard hover={false}>
              <p className="text-sm font-semibold text-white">{profile?.avg_centipawn_loss ? profile.avg_centipawn_loss.toFixed(0) : 'N/A'}</p>
              <p className="mt-1 text-sm text-slate-400">Average centipawn loss when available.</p>
            </GlassCard>
          </div>
        </section>

        <aside>
          <ProfileCard profile={profile} />
        </aside>
      </div>
    </AppShell>
  );
}
