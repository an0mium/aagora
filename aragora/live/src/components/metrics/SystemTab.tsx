'use client';

import type { SystemData } from './types';

interface SystemTabProps {
  system: SystemData | null;
  loading: boolean;
}

export function SystemTab({ system, loading }: SystemTabProps) {
  return (
    <div className="space-y-4 max-h-80 overflow-y-auto">
      {loading && !system && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">Loading system info...</div>
      )}

      {system && (
        <>
          {/* Memory Usage */}
          {system.memory && 'rss_mb' in system.memory && (
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-bg border border-border rounded-lg text-center">
                <div className="text-2xl font-mono text-acid-cyan">{system.memory.rss_mb}</div>
                <div className="text-xs text-text-muted">RSS (MB)</div>
              </div>
              <div className="p-3 bg-bg border border-border rounded-lg text-center">
                <div className="text-2xl font-mono text-yellow-400">{system.memory.vms_mb}</div>
                <div className="text-xs text-text-muted">VMS (MB)</div>
              </div>
            </div>
          )}

          <div className="p-3 bg-bg border border-border rounded-lg space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-text-muted">Python</span>
              <span className="text-text truncate max-w-[200px]">{system.python_version.split(' ')[0]}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-text-muted">Platform</span>
              <span className="text-text truncate max-w-[200px]">{system.platform}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-text-muted">Machine</span>
              <span className="text-text">{system.machine}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-text-muted">PID</span>
              <span className="text-acid-green">{system.pid}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
