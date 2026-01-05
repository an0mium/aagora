import type { StreamEvent } from '@/types/events';

export interface Insight {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  agents_involved: string[];
  evidence: string[];
}

export interface MemoryRecall {
  query: string;
  hits: Array<{ topic: string; similarity: number }>;
  count: number;
  timestamp: string;
}

export interface FlipEvent {
  id: string;
  agent: string;
  type: 'contradiction' | 'retraction' | 'qualification' | 'refinement';
  type_emoji: string;
  before: { claim: string; confidence: string };
  after: { claim: string; confidence: string };
  similarity: string;
  domain: string | null;
  timestamp: string;
}

export interface FlipSummary {
  total_flips: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
  recent_24h: number;
}

export interface InsightsPanelProps {
  wsMessages?: StreamEvent[];
  apiBase?: string;
}

export type InsightsTab = 'insights' | 'memory' | 'flips' | 'learning';
