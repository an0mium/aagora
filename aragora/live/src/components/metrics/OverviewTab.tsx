'use client';

import type { MetricsData } from './types';

interface OverviewTabProps {
  metrics: MetricsData | null;
  loading: boolean;
}

export function OverviewTab({ metrics, loading }: OverviewTabProps) {
  return (
    <div className="space-y-4 max-h-80 overflow-y-auto">
      {loading && !metrics && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">Loading metrics...</div>
      )}

      {metrics && (
        <>
          {/* Top Endpoints */}
          {metrics.requests.top_endpoints.length > 0 && (
            <div className="p-3 bg-bg border border-border rounded-lg">
              <div className="text-sm font-mono text-text-muted mb-3">Top Endpoints</div>
              <div className="space-y-2">
                {metrics.requests.top_endpoints.slice(0, 5).map((ep) => (
                  <div key={ep.endpoint} className="flex items-center justify-between text-xs font-mono">
                    <span className="text-text truncate max-w-[200px]">{ep.endpoint}</span>
                    <span className="text-acid-cyan">{ep.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Database Sizes */}
          {Object.keys(metrics.databases).length > 0 && (
            <div className="p-3 bg-bg border border-border rounded-lg">
              <div className="text-sm font-mono text-text-muted mb-3">Database Sizes</div>
              <div className="space-y-2">
                {Object.entries(metrics.databases).map(([name, info]) => (
                  <div key={name} className="flex items-center justify-between text-xs font-mono">
                    <span className="text-text">{name.replace('.db', '')}</span>
                    <span className="text-yellow-400">{info.human}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
