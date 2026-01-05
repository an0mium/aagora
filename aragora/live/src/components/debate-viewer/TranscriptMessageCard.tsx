'use client';

import { getAgentColors } from '@/utils/agentColors';
import type { TranscriptMessageCardProps } from './types';

export function TranscriptMessageCard({ message }: TranscriptMessageCardProps) {
  const colors = getAgentColors(message.agent || 'system');
  return (
    <div className={`${colors.bg} border ${colors.border} p-4`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`font-mono font-bold text-sm ${colors.text}`}>
            {(message.agent || 'SYSTEM').toUpperCase()}
          </span>
          {message.role && (
            <span className="text-xs text-text-muted border border-text-muted/30 px-1">{message.role}</span>
          )}
          {message.round !== undefined && message.round > 0 && (
            <span className="text-xs text-text-muted">R{message.round}</span>
          )}
        </div>
        {message.timestamp && (
          <span className="text-[10px] text-text-muted font-mono">
            {new Date(message.timestamp * 1000).toLocaleTimeString()}
          </span>
        )}
      </div>
      <div className="text-sm text-text whitespace-pre-wrap">{message.content}</div>
    </div>
  );
}
