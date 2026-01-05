import type { StreamEvent } from '@/types/events';

export interface AgentTabsProps {
  events: StreamEvent[];
  apiBase?: string;
}

export interface PositionEntry {
  topic: string;
  position: string;
  confidence: number;
  evidence_count: number;
  last_updated: string;
}

export interface AgentData {
  name: string;
  latestContent: string;
  role: string;
  cognitiveRole?: string;
  round: number;
  confidence?: number;
  citations?: string[];
  timestamp: number;
  allMessages: Array<{ content: string; round: number; role: string; timestamp: number }>;
}

export interface TimelineMessage {
  agent: string;
  content: string;
  role: string;
  cognitiveRole?: string;
  round: number;
  timestamp: number;
}

// Special tab ID for unified "All Agents" view
export const ALL_AGENTS_TAB = '__all__';

// Terminal-style role indicators
export const ROLE_ICONS: Record<string, string> = {
  proposer: '💡',
  critic: '🔍',
  synthesizer: '🔄',
  judge: '⚖️',
  reviewer: '📋',
  implementer: '🛠️',
  default: '▶',
};
