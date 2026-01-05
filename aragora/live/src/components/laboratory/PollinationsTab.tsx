'use client';

import type { CrossPollination } from './types';

interface PollinationsTabProps {
  pollinations: CrossPollination[];
  loading: boolean;
}

export function PollinationsTab({ pollinations, loading }: PollinationsTabProps) {
  return (
    <div className="space-y-3 max-h-80 overflow-y-auto">
      {loading && pollinations.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          Analyzing cross-pollination opportunities...
        </div>
      )}

      {!loading && pollinations.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          No cross-pollination suggestions yet. Lab needs more trait data.
        </div>
      )}

      {pollinations.map((pollination, index) => (
        <div
          key={`${pollination.source_agent}-${pollination.target_agent}-${index}`}
          className="p-3 bg-bg border border-border rounded-lg hover:border-acid-green/50 transition-colors"
        >
          <div className="flex items-center gap-2 mb-2 font-mono text-sm">
            <span className="text-acid-cyan">{pollination.source_agent}</span>
            <span className="text-text-muted">-&gt;</span>
            <span className="text-acid-green">{pollination.target_agent}</span>
          </div>

          <p className="text-sm text-text font-medium mb-1">
            Transfer: {pollination.trait}
          </p>

          <p className="text-xs text-text-muted mb-2">{pollination.rationale}</p>

          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-muted">Expected improvement:</span>
            <span className="text-acid-green">
              +{(pollination.expected_improvement * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
