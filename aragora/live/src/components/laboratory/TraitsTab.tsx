'use client';

import { getConfidenceColor, getDomainColor } from '@/utils/colors';
import type { EmergentTrait } from './types';

interface TraitsTabProps {
  traits: EmergentTrait[];
  loading: boolean;
}

export function TraitsTab({ traits, loading }: TraitsTabProps) {
  return (
    <div className="space-y-3 max-h-80 overflow-y-auto">
      {loading && traits.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          Detecting emergent traits...
        </div>
      )}

      {!loading && traits.length === 0 && (
        <div className="text-center text-text-muted py-4 font-mono text-sm">
          No emergent traits detected yet. Run more debates to discover agent specializations.
        </div>
      )}

      {traits.map((trait, index) => (
        <div
          key={`${trait.agent}-${trait.trait}-${index}`}
          className="p-3 bg-bg border border-border rounded-lg hover:border-acid-cyan/50 transition-colors"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-acid-cyan font-bold">
                {trait.agent}
              </span>
              <span className={`px-2 py-0.5 text-xs rounded border ${getDomainColor(trait.domain)}`}>
                {trait.domain}
              </span>
            </div>
            <span className={`text-xs font-mono ${getConfidenceColor(trait.confidence)}`}>
              {(trait.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <p className="text-sm text-text font-medium mb-2">{trait.trait}</p>

          {trait.evidence && trait.evidence.length > 0 && (
            <div className="space-y-1">
              {trait.evidence.slice(0, 2).map((e, i) => (
                <p key={i} className="text-xs text-text-muted line-clamp-1">
                  {e}
                </p>
              ))}
              {trait.evidence.length > 2 && (
                <p className="text-xs text-text-muted">
                  +{trait.evidence.length - 2} more evidence
                </p>
              )}
            </div>
          )}

          <div className="mt-2 text-xs text-text-muted font-mono">
            Detected: {new Date(trait.detected_at).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  );
}
