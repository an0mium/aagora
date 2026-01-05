'use client';

import type { GenesisStats } from './types';

interface EvolutionTabProps {
  genesisStats: GenesisStats | null;
  loading: boolean;
}

export function EvolutionTab({ genesisStats, loading }: EvolutionTabProps) {
  return (
    <div className="space-y-4 max-h-80 overflow-y-auto">
      {loading && !genesisStats && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          Loading evolution data...
        </div>
      )}

      {!loading && !genesisStats && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          No evolution data available yet.
        </div>
      )}

      {genesisStats && (
        <>
          {/* Population Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div className="text-2xl font-mono text-green-400">{genesisStats.total_births}</div>
              <div className="text-xs text-text-muted">Births</div>
            </div>
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div className="text-2xl font-mono text-red-400">{genesisStats.total_deaths}</div>
              <div className="text-xs text-text-muted">Deaths</div>
            </div>
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div
                className={`text-2xl font-mono ${genesisStats.net_population_change >= 0 ? 'text-green-400' : 'text-red-400'}`}
              >
                {genesisStats.net_population_change >= 0 ? '+' : ''}
                {genesisStats.net_population_change}
              </div>
              <div className="text-xs text-text-muted">Net Change</div>
            </div>
          </div>

          {/* Fitness Trend */}
          <div className="p-3 bg-bg border border-border rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-mono text-text-muted">Avg Fitness Change (Recent)</span>
              <span
                className={`text-lg font-mono ${genesisStats.avg_fitness_change_recent >= 0 ? 'text-green-400' : 'text-red-400'}`}
              >
                {genesisStats.avg_fitness_change_recent >= 0 ? '+' : ''}
                {genesisStats.avg_fitness_change_recent.toFixed(4)}
              </span>
            </div>
            <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
              <div
                className={`h-full ${genesisStats.avg_fitness_change_recent >= 0 ? 'bg-green-400' : 'bg-red-400'}`}
                style={{ width: `${Math.min(100, Math.abs(genesisStats.avg_fitness_change_recent) * 500)}%` }}
              />
            </div>
          </div>

          {/* Event Breakdown */}
          {genesisStats.event_counts && Object.keys(genesisStats.event_counts).length > 0 && (
            <div className="p-3 bg-bg border border-border rounded-lg">
              <div className="text-sm font-mono text-text-muted mb-3">Event Types</div>
              <div className="space-y-2">
                {Object.entries(genesisStats.event_counts)
                  .filter(([, count]) => count > 0)
                  .sort(([, a], [, b]) => b - a)
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-xs font-mono">
                      <span className="text-text-muted">{type.replace(/_/g, ' ')}</span>
                      <span className="text-yellow-400">{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Integrity Status */}
          <div className="flex items-center justify-between p-2 bg-bg border border-border rounded-lg text-xs font-mono">
            <span className="text-text-muted">Ledger Integrity</span>
            <span className={genesisStats.integrity_verified ? 'text-green-400' : 'text-red-400'}>
              {genesisStats.integrity_verified ? 'VERIFIED' : 'UNVERIFIED'}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
