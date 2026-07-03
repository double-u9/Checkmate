'use client';

import { motion } from 'framer-motion';
import { BrainCircuit, Castle, Gauge, Shield, Swords, Target, UserRound } from 'lucide-react';
import type { ComponentType } from 'react';
import GlassCard from '@/components/ui/GlassCard';
import StatusBadge from '@/components/ui/StatusBadge';
import type { ProfileResponse } from '@/lib/types';

interface ProfileCardProps {
  profile: ProfileResponse | null;
}

const STYLE_CONFIG: Record<string, { tone: 'danger' | 'info' | 'success' | 'warning' | 'neutral'; icon: ComponentType<{ className?: string }>; desc: string }> = {
  attacker: { tone: 'danger', icon: Swords, desc: 'Sharp, forcing, and tactically ambitious.' },
  positional: { tone: 'info', icon: Castle, desc: 'Patient maneuvering and long-term pressure.' },
  universal: { tone: 'success', icon: BrainCircuit, desc: 'Flexible style that adapts to position demands.' },
  defender: { tone: 'warning', icon: Shield, desc: 'Solid structure and resilient defensive choices.' },
  unknown: { tone: 'neutral', icon: UserRound, desc: 'More games are needed for a confident profile.' },
};

function StatBar({ label, value, icon: Icon }: { label: string; value: number; icon: ComponentType<{ className?: string }> }) {
  const percent = Math.max(0, Math.min(100, value * 100));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="flex items-center gap-2 font-medium text-slate-400">
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          {label}
        </span>
        <span className="font-mono font-semibold text-slate-100">{percent.toFixed(0)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <motion.div
          className="h-full rounded-full bg-cyan-300"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.75, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

export default function ProfileCard({ profile }: ProfileCardProps) {
  if (!profile) {
    return (
      <GlassCard id="profile-card">
        <div className="flex min-h-[180px] flex-col items-center justify-center text-center">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-purple-300/30 bg-purple-400/10 text-purple-200">
            <UserRound className="h-5 w-5" aria-hidden="true" />
          </div>
          <h2 className="text-sm font-semibold text-white">No opponent model yet</h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
            Paste PGN games in the Profiles view to identify style, risk tolerance, weaknesses, and counter-strategy.
          </p>
        </div>
      </GlassCard>
    );
  }

  const style = STYLE_CONFIG[profile.style || 'unknown'] || STYLE_CONFIG.unknown;
  const StyleIcon = style.icon;
  const psych = profile.psychological_profile;

  return (
    <GlassCard id="profile-card" className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-purple-200/70">Opponent profile</p>
          <h2 className="mt-1 text-lg font-semibold text-white">{profile.player_name}</h2>
        </div>
        <StatusBadge tone={style.tone}>{profile.total_games_analyzed} games</StatusBadge>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-950/55 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-purple-300/20 bg-purple-400/10 text-purple-200">
            <StyleIcon className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-white">{profile.style || 'Unknown'} style</p>
            <p className="mt-1 text-sm leading-6 text-slate-400">{style.desc}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <StatBar label="Aggression" value={profile.aggression_score} icon={Swords} />
        <StatBar label="Risk tolerance" value={profile.risk_tolerance} icon={Gauge} />
        <StatBar label="Tactical pull" value={profile.tactical_preference} icon={Target} />
        <StatBar label="Positional pull" value={profile.positional_preference} icon={Castle} />
        <StatBar label="Endgame skill" value={profile.endgame_skill} icon={Shield} />
      </div>

      {psych && (
        <div className="space-y-4 border-t border-slate-700/70 pt-5">
          {psych.traits.length > 0 && (
            <section aria-labelledby="player-tendencies">
              <h3 id="player-tendencies" className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Player tendencies</h3>
              <ul className="mt-3 space-y-2">
                {psych.traits.map((trait) => (
                  <li key={trait} className="rounded-lg border border-slate-700/70 bg-slate-950/45 px-3 py-2 text-sm text-slate-300">
                    {trait}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {psych.recommendations.length > 0 && (
            <section aria-labelledby="counter-strategy" className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 p-4">
              <h3 id="counter-strategy" className="flex items-center gap-2 text-sm font-semibold text-emerald-100">
                <Target className="h-4 w-4" aria-hidden="true" />
                Counter-strategy
              </h3>
              <ul className="mt-3 space-y-2">
                {psych.recommendations.map((rec) => (
                  <li key={rec} className="text-sm leading-6 text-slate-100">{rec}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </GlassCard>
  );
}
