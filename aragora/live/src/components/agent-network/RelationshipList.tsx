'use client';

import type { RelationshipListProps } from './types';

export function RelationshipList({ title, items, icon, colorClass, onAgentClick }: RelationshipListProps) {
  if (!items || items.length === 0) {
    return <div className="text-zinc-500 text-sm">No {title.toLowerCase()} data</div>;
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-2">
        <span>{icon}</span> {title}
      </h4>
      <div className="space-y-1">
        {items.map((item) => (
          <div
            key={item.agent}
            className={`flex items-center justify-between p-2 rounded ${colorClass} cursor-pointer hover:opacity-80`}
            onClick={() => onAgentClick(item.agent)}
          >
            <span className="font-medium">{item.agent}</span>
            <div className="flex items-center gap-2 text-xs">
              <span className="opacity-75">Score: {(item.score * 100).toFixed(0)}%</span>
              {item.debate_count !== undefined && (
                <span className="opacity-50">({item.debate_count} debates)</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
