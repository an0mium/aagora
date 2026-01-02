'use client';

import type { StreamEvent } from '@/types/events';

interface PhaseProgressProps {
  events: StreamEvent[];
  currentPhase: string;
}

const PHASES = ['debate', 'design', 'implement', 'verify', 'commit'];

export function PhaseProgress({ events, currentPhase }: PhaseProgressProps) {
  type PhaseStatusType = 'pending' | 'active' | 'complete' | 'failed';

  // Get phase statuses from events
  const phaseStatuses: { phase: string; status: PhaseStatusType }[] = PHASES.map((phase) => {
    const startEvent = events.find(
      (e) => e.type === 'phase_start' && e.data.phase === phase
    );
    const endEvent = events.find(
      (e) => e.type === 'phase_end' && e.data.phase === phase
    );

    if (endEvent) {
      return {
        phase,
        status: (endEvent.data.success ? 'complete' : 'failed') as PhaseStatusType,
      };
    }
    if (startEvent || currentPhase === phase) {
      return { phase, status: 'active' as PhaseStatusType };
    }
    return { phase, status: 'pending' as PhaseStatusType };
  });

  return (
    <div className="card p-4">
      <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">
        Phase Progress
      </h2>
      <div className="flex items-center gap-2">
        {phaseStatuses.map(({ phase, status }, index) => (
          <div key={phase} className="flex items-center">
            <PhaseBlock phase={phase} status={status} />
            {index < phaseStatuses.length - 1 && (
              <div className="w-4 h-0.5 bg-border" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

interface PhaseBlockProps {
  phase: string;
  status: 'pending' | 'active' | 'complete' | 'failed';
}

function PhaseBlock({ phase, status }: PhaseBlockProps) {
  const baseClasses = 'px-3 py-2 rounded-lg text-sm font-medium transition-all';

  const statusClasses: Record<string, string> = {
    pending: 'bg-surface border border-border text-text-muted',
    active: 'bg-accent/20 border border-accent text-accent animate-pulse',
    complete: 'bg-success/20 border border-success text-success',
    failed: 'bg-warning/20 border border-warning text-warning',
  };

  return (
    <div className={`${baseClasses} ${statusClasses[status]}`}>
      {phase.charAt(0).toUpperCase() + phase.slice(1)}
    </div>
  );
}
