import type { StreamEvent } from '@/types/events';

export interface AgentRanking {
  name: string;
  elo: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  games: number;
  consistency?: number; // 0-1 consistency score from FlipDetector
  consistency_class?: string; // "high" | "medium" | "low"
}

export interface Match {
  debate_id: string;
  winner: string;
  participants: string[];
  domain: string;
  elo_changes: Record<string, number>;
  created_at: string;
}

export interface AgentReputation {
  agent: string;
  score: number;
  vote_weight: number;
  proposal_acceptance_rate: number;
  critique_value: number;
  debates_participated: number;
}

export interface TeamCombination {
  agents: string[];
  success_rate: number;
  total_debates: number;
  wins: number;
}

export interface RankingStats {
  mean_elo: number;
  median_elo: number;
  total_agents: number;
  total_matches: number;
  rating_distribution: Record<string, number>;
  trending_up: string[];
  trending_down: string[];
}

export interface AgentIntrospection {
  agent: string;
  self_model: {
    strengths: string[];
    weaknesses: string[];
    biases: string[];
  };
  confidence_calibration: number;
  recent_performance_assessment: string;
  improvement_focus: string[];
  last_updated: string;
}

export interface LeaderboardPanelProps {
  wsMessages?: StreamEvent[];
  loopId?: string | null;
  apiBase?: string;
}

export type LeaderboardTab = 'rankings' | 'matches' | 'reputation' | 'teams' | 'stats' | 'minds';
