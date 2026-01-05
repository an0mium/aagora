'use client';

import { getFlipTypeColor } from '@/utils/colors';
import type { FlipEvent, FlipSummary } from './types';

interface FlipsTabProps {
  flips: FlipEvent[];
  flipSummary: FlipSummary | null;
}

export function FlipsTab({ flips, flipSummary }: FlipsTabProps) {
  return (
    <div
      id="flips-panel"
      role="tabpanel"
      aria-labelledby="flips-tab"
      className="space-y-3 max-h-96 overflow-y-auto"
    >
      {/* Summary Header */}
      {flipSummary && flipSummary.total_flips > 0 && (
        <div className="p-3 bg-bg border border-border rounded-lg mb-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text">Position Reversals</span>
            <span className="text-xs text-text-muted">
              {flipSummary.recent_24h} in 24h
            </span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            {flipSummary.by_type.contradiction > 0 && (
              <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                {flipSummary.by_type.contradiction} contradictions
              </span>
            )}
            {flipSummary.by_type.retraction > 0 && (
              <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded">
                {flipSummary.by_type.retraction} retractions
              </span>
            )}
            {flipSummary.by_type.qualification > 0 && (
              <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded">
                {flipSummary.by_type.qualification} qualifications
              </span>
            )}
            {flipSummary.by_type.refinement > 0 && (
              <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded">
                {flipSummary.by_type.refinement} refinements
              </span>
            )}
          </div>
        </div>
      )}

      {flips.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No position flips detected yet. Flips are tracked when agents reverse their positions.
        </div>
      )}

      {flips.map((flip) => (
        <div
          key={flip.id}
          className="p-3 bg-bg border border-border rounded-lg hover:border-accent/50 transition-colors"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 text-xs rounded border ${getFlipTypeColor(flip.type)}`}
              >
                {flip.type_emoji} {flip.type}
              </span>
              <span className="text-xs text-text-muted font-mono">{flip.agent}</span>
            </div>
            <span className="text-xs text-text-muted">{flip.similarity} similar</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
              <div className="flex items-center justify-between mb-1">
                <span className="text-red-400 font-medium">Before</span>
                <span className="text-text-muted">{flip.before.confidence}</span>
              </div>
              <p className="text-text-muted">{flip.before.claim}</p>
            </div>

            <div className="p-2 bg-green-500/10 border border-green-500/20 rounded">
              <div className="flex items-center justify-between mb-1">
                <span className="text-green-400 font-medium">After</span>
                <span className="text-text-muted">{flip.after.confidence}</span>
              </div>
              <p className="text-text-muted">{flip.after.claim}</p>
            </div>
          </div>

          {flip.domain && (
            <div className="mt-2">
              <span className="px-1.5 py-0.5 text-xs bg-surface rounded text-text-muted">
                {flip.domain}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
