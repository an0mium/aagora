'use client';

import type { SignificantMoment } from './types';

interface MomentsSectionProps {
  moments: SignificantMoment[];
}

export function MomentsSection({ moments }: MomentsSectionProps) {
  if (moments.length === 0) return null;

  return (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
      <h4 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
        <span>⭐</span> Significant Moments
      </h4>
      <div className="space-y-2">
        {moments.map((moment, idx) => (
          <div key={idx} className="p-3 rounded bg-yellow-900/20 border border-yellow-800/30">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-yellow-400 uppercase">
                {moment.type.replace(/_/g, ' ')}
              </span>
              <span className="text-xs text-zinc-500">
                {(moment.significance * 100).toFixed(0)}% significance
              </span>
            </div>
            <p className="text-sm text-zinc-300">{moment.description}</p>
            {moment.debate_id && (
              <span className="text-xs text-zinc-500 mt-1 block">
                Debate: {moment.debate_id.slice(0, 8)}...
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
