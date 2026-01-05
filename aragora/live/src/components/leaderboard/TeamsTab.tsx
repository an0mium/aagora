'use client';

import Link from 'next/link';
import { getRankBadge, getScoreColor } from '@/utils/colors';
import type { TeamCombination } from './types';

interface TeamsTabProps {
  teams: TeamCombination[];
  loading: boolean;
}

export function TeamsTab({ teams, loading }: TeamsTabProps) {
  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {loading && (
        <div className="text-center text-text-muted py-4">Loading team data...</div>
      )}

      {!loading && teams.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No team combinations yet. Run more debates to find winning teams.
        </div>
      )}

      {teams.map((team, index) => (
        <div
          key={team.agents.join('-')}
          className="flex items-center gap-3 p-2 bg-bg border border-border rounded-lg hover:border-accent/50 transition-colors"
        >
          {/* Rank Badge */}
          <div
            className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold border ${getRankBadge(index + 1)}`}
          >
            {index + 1}
          </div>

          {/* Team Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {team.agents.map((agent, i) => (
                <Link
                  key={agent}
                  href={`/agent/${encodeURIComponent(agent)}/`}
                  className="text-sm font-medium text-text hover:text-accent transition-colors cursor-pointer"
                  title="View agent profile"
                >
                  {agent}{i < team.agents.length - 1 && <span className="text-text-muted ml-1">+</span>}
                </Link>
              ))}
            </div>
            <div className="text-xs text-text-muted">
              {team.wins}W / {team.total_debates} debates
            </div>
          </div>

          {/* Success Rate */}
          <div className={`text-sm font-mono font-bold ${getScoreColor(team.success_rate)}`}>
            {(team.success_rate * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}
