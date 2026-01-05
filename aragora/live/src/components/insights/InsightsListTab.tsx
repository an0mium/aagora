'use client';

import { ErrorWithRetry } from '../RetryButton';
import { getInsightTypeColor, getConfidenceColor } from '@/utils/colors';
import type { Insight } from './types';

interface InsightsListTabProps {
  insights: Insight[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function InsightsListTab({ insights, loading, error, onRetry }: InsightsListTabProps) {
  return (
    <div
      id="insights-panel"
      role="tabpanel"
      aria-labelledby="insights-tab"
      className="space-y-3 max-h-96 overflow-y-auto"
    >
      {loading && (
        <div className="text-center text-text-muted py-4">Loading insights...</div>
      )}

      {error && <ErrorWithRetry error={error} onRetry={onRetry} />}

      {!loading && !error && insights.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No insights extracted yet. Run a debate cycle to generate insights.
        </div>
      )}

      {insights.map((insight) => (
        <div
          key={insight.id}
          className="p-3 bg-bg border border-border rounded-lg hover:border-accent/50 transition-colors"
        >
          <div className="flex items-start justify-between gap-2">
            <span
              className={`px-2 py-0.5 text-xs rounded border ${getInsightTypeColor(insight.type)}`}
            >
              {insight.type}
            </span>
            <span
              className={`text-xs font-mono ${getConfidenceColor(insight.confidence)}`}
            >
              {(insight.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <h4 className="text-sm font-medium text-text mt-2">{insight.title}</h4>

          <p className="text-xs text-text-muted mt-1">{insight.description}</p>

          {insight.agents_involved?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {insight.agents_involved.map((agent, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-xs bg-surface rounded text-text-muted"
                >
                  {agent}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
