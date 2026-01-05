'use client';

import Link from 'next/link';
import { LeaderboardSkeleton } from '../Skeleton';
import { getScoreColor } from '@/utils/colors';
import type { AgentReputation } from './types';

interface ReputationTabProps {
  reputations: AgentReputation[];
  loading: boolean;
}

export function ReputationTab({ reputations, loading }: ReputationTabProps) {
  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {loading && <LeaderboardSkeleton count={3} />}

      {!loading && reputations.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No reputation data yet. Run debate cycles to build agent reputations.
        </div>
      )}

      {reputations.map((rep, index) => (
        <div
          key={rep.agent}
          className="flex items-center gap-3 p-2 bg-bg border border-border rounded-lg hover:border-accent/50 transition-colors"
        >
          {/* Rank */}
          <div className="w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold bg-surface text-text-muted">
            {index + 1}
          </div>

          {/* Agent Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Link
                href={`/agent/${encodeURIComponent(rep.agent)}/`}
                className="text-sm font-medium text-text hover:text-accent transition-colors cursor-pointer"
                title="View agent profile"
              >
                {rep.agent}
              </Link>
              <span className={`text-sm font-mono font-bold ${getScoreColor(rep.score)}`}>
                {(rep.score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex gap-3 text-xs text-text-muted">
              <span title="Vote weight in consensus">
                Vote: <span className="text-text">{rep.vote_weight.toFixed(2)}x</span>
              </span>
              <span title="Proposal acceptance rate">
                Accept: <span className="text-text">{(rep.proposal_acceptance_rate * 100).toFixed(0)}%</span>
              </span>
              <span title="Critique value score">
                Critique: <span className="text-text">{rep.critique_value.toFixed(2)}</span>
              </span>
            </div>
          </div>

          {/* Debates count */}
          <div className="text-xs text-text-muted">
            {rep.debates_participated} debates
          </div>
        </div>
      ))}
    </div>
  );
}
