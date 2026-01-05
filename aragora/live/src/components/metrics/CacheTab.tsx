'use client';

import { formatAge } from '@/utils/formatters';
import type { CacheData } from './types';

interface CacheTabProps {
  cache: CacheData | null;
  loading: boolean;
}

export function CacheTab({ cache, loading }: CacheTabProps) {
  return (
    <div className="space-y-4 max-h-80 overflow-y-auto">
      {loading && !cache && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">Loading cache stats...</div>
      )}

      {cache && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div className="text-2xl font-mono text-purple-400">{(cache.hit_rate * 100).toFixed(1)}%</div>
              <div className="text-xs text-text-muted">Hit Rate</div>
            </div>
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div className="text-2xl font-mono text-green-400">{cache.hits}</div>
              <div className="text-xs text-text-muted">Hits</div>
            </div>
            <div className="p-3 bg-bg border border-border rounded-lg text-center">
              <div className="text-2xl font-mono text-red-400">{cache.misses}</div>
              <div className="text-xs text-text-muted">Misses</div>
            </div>
          </div>

          <div className="p-3 bg-bg border border-border rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-mono text-text-muted">Entries</span>
              <span className="text-sm font-mono text-acid-cyan">
                {cache.total_entries} / {cache.max_entries}
              </span>
            </div>
            <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-400"
                style={{ width: `${(cache.total_entries / cache.max_entries) * 100}%` }}
              />
            </div>
          </div>

          {Object.keys(cache.entries_by_prefix).length > 0 && (
            <div className="p-3 bg-bg border border-border rounded-lg">
              <div className="text-sm font-mono text-text-muted mb-3">Entries by Type</div>
              <div className="space-y-2">
                {Object.entries(cache.entries_by_prefix)
                  .sort(([, a], [, b]) => b - a)
                  .map(([prefix, count]) => (
                    <div key={prefix} className="flex items-center justify-between text-xs font-mono">
                      <span className="text-text">{prefix}</span>
                      <span className="text-purple-400">{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between p-2 bg-bg border border-border rounded-lg text-xs font-mono">
            <span className="text-text-muted">Entry Age Range</span>
            <span className="text-text">
              {formatAge(cache.newest_entry_age_seconds)} - {formatAge(cache.oldest_entry_age_seconds)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
