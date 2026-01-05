'use client';

import type { ReactNode } from 'react';
import { RefreshButton } from './RefreshButton';
import { ExpandToggle } from './ExpandToggle';

export interface PanelHeaderProps {
  title: string;
  loading?: boolean;
  onRefresh?: () => void;
  expanded?: boolean;
  onToggleExpand?: () => void;
  children?: ReactNode;
  className?: string;
}

export function PanelHeader({
  title,
  loading,
  onRefresh,
  expanded,
  onToggleExpand,
  children,
  className = '',
}: PanelHeaderProps) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <h3 className="text-lg font-semibold text-text">{title}</h3>
      <div className="flex items-center gap-2">
        {children}
        {onRefresh && <RefreshButton onClick={onRefresh} loading={loading} />}
        {onToggleExpand !== undefined && expanded !== undefined && (
          <ExpandToggle expanded={expanded} onToggle={onToggleExpand} />
        )}
      </div>
    </div>
  );
}
