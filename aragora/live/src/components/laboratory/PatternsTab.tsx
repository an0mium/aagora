'use client';

import { getScoreColor } from '@/utils/colors';
import type { CritiquePattern } from './types';

interface PatternsTabProps {
  patterns: CritiquePattern[];
  loading: boolean;
}

export function PatternsTab({ patterns, loading }: PatternsTabProps) {
  return (
    <div className="space-y-3 max-h-80 overflow-y-auto">
      {loading && patterns.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          Discovering critique patterns...
        </div>
      )}

      {!loading && patterns.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          No critique patterns yet. Run more debates to discover effective arguments.
        </div>
      )}

      {patterns.map((pattern, index) => (
        <div
          key={`${pattern.pattern.slice(0, 20)}-${index}`}
          className="p-3 bg-bg border border-border rounded-lg hover:border-purple-500/50 transition-colors"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <span className="px-2 py-0.5 text-xs rounded border bg-purple-500/20 text-purple-400 border-purple-500/30">
              {pattern.issue_type || 'general'}
            </span>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className={getScoreColor(pattern.success_rate)}>
                {(pattern.success_rate * 100).toFixed(0)}% success
              </span>
              <span className="text-text-muted">{pattern.usage_count} uses</span>
            </div>
          </div>

          <p className="text-sm text-text font-medium mb-2">{pattern.pattern}</p>

          {pattern.suggested_rebuttal && (
            <div className="text-xs text-text-muted p-2 bg-surface rounded border border-border">
              <span className="text-purple-400 font-mono">Rebuttal:</span> {pattern.suggested_rebuttal}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
