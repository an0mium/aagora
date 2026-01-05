'use client';

import type { MemoryRecall } from './types';

interface MemoryTabProps {
  memoryRecalls: MemoryRecall[];
}

export function MemoryTab({ memoryRecalls }: MemoryTabProps) {
  return (
    <div
      id="memory-panel"
      role="tabpanel"
      aria-labelledby="memory-tab"
      className="space-y-3 max-h-96 overflow-y-auto"
    >
      {memoryRecalls.length === 0 && (
        <div className="text-center text-text-muted py-4">
          No memory recalls yet. Historical context will appear here during debates.
        </div>
      )}

      {memoryRecalls.map((recall, index) => (
        <div
          key={`${recall.timestamp}-${index}`}
          className="p-3 bg-bg border border-border rounded-lg"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded">
              Memory Recall
            </span>
            <span className="text-xs text-text-muted">
              {new Date(recall.timestamp).toLocaleTimeString()}
            </span>
          </div>

          <p className="text-sm text-text-muted mb-2">Query: {recall.query}</p>

          <div className="space-y-1">
            {recall.hits?.map((hit, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span className="text-text flex-1 mr-2">{hit.topic}</span>
                <span className="text-text-muted font-mono">
                  {(hit.similarity * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>

          {recall.count > 3 && (
            <div className="text-xs text-text-muted mt-1">
              +{recall.count - 3} more matches
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
