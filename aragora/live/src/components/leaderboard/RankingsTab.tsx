'use client';

import Link from 'next/link';
import { LeaderboardSkeleton } from '../Skeleton';
import { getEloColor, getConsistencyColor, getRankBadge } from '@/utils/colors';
import type { AgentRanking } from './types';

interface RankingsTabProps {
  agents: AgentRanking[];
  loading: boolean;
  error: string | null;
  endpointErrors: Record<string, string>;
}

export function RankingsTab({ agents, loading, error, endpointErrors }: RankingsTabProps) {
  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {loading && <LeaderboardSkeleton count={5} />}

      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded p-3 mb-2">
          <div className="text-red-400 text-sm font-medium mb-1">{error}</div>
          {Object.keys(endpointErrors).length > 0 && (
            <details className="text-xs">
              <summary className="cursor-pointer text-red-300 hover:text-red-200">
                Show details
              </summary>
              <ul className="mt-2 space-y-1 text-red-300/80">
                {Object.entries(endpointErrors).map(([endpoint, msg]) => (
                  <li key={endpoint}>
                    <span className="font-mono">{endpoint}:</span> {msg}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      {!loading && !error && agents.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No rankings yet. Run debate cycles to generate rankings.
        </div>
      )}

      {agents.map((agent, index) => (
        <div
          key={agent.name}
          className="flex items-center gap-3 p-2 bg-bg border border-border rounded-lg hover:border-accent/50 transition-colors"
        >
          {/* Rank Badge */}
          <div
            className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold border ${getRankBadge(index + 1)}`}
          >
            {index + 1}
          </div>

          {/* Agent Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Link
                href={`/agent/${encodeURIComponent(agent.name)}/`}
                className="text-sm font-medium text-text hover:text-accent transition-colors cursor-pointer"
                title="View agent profile"
              >
                {agent.name}
              </Link>
              <span className={`text-sm font-mono font-bold ${getEloColor(agent.elo)}`}>
                {agent.elo}
              </span>
              {agent.consistency !== undefined && (
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${getConsistencyColor(agent.consistency)} bg-surface`}
                  title={`Consistency: ${(agent.consistency * 100).toFixed(0)}%`}
                >
                  {(agent.consistency * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <div className="text-xs text-text-muted">
              {agent.wins}W-{agent.losses}L-{agent.draws}D ({agent.win_rate}%)
            </div>
          </div>

          {/* Games Played */}
          <div className="text-xs text-text-muted">
            {agent.games} games
          </div>
        </div>
      ))}
    </div>
  );
}
