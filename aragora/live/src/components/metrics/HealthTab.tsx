'use client';

import { getStatusColor } from '@/utils/colors';
import type { HealthData } from './types';

interface HealthTabProps {
  health: HealthData | null;
  loading: boolean;
}

export function HealthTab({ health, loading }: HealthTabProps) {
  return (
    <div className="space-y-3 max-h-80 overflow-y-auto">
      {loading && !health && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">Checking health...</div>
      )}

      {health && (
        <>
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(health.checks).map(([name, check]) => (
              <div key={name} className="p-3 bg-bg border border-border rounded-lg text-center">
                <div className={`text-lg font-mono ${getStatusColor(check.status)}`}>
                  {check.status === 'healthy' ? 'OK' : check.status === 'unavailable' ? 'N/A' : 'ERR'}
                </div>
                <div className="text-xs text-text-muted capitalize">{name.replace('_', ' ')}</div>
                {check.error && (
                  <div className="text-xs text-red-400 mt-1 truncate" title={check.error}>
                    {check.error.slice(0, 20)}...
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between p-2 bg-bg border border-border rounded-lg text-xs font-mono">
            <span className="text-text-muted">Overall Status</span>
            <span className={getStatusColor(health.status)}>{health.status.toUpperCase()}</span>
          </div>
        </>
      )}
    </div>
  );
}
