export interface EmergentTrait {
  agent: string;
  trait: string;
  domain: string;
  confidence: number;
  evidence: string[];
  detected_at: string;
}

export interface CrossPollination {
  source_agent: string;
  target_agent: string;
  trait: string;
  expected_improvement: number;
  rationale: string;
}

export interface GenesisStats {
  total_events: number;
  total_births: number;
  total_deaths: number;
  net_population_change: number;
  avg_fitness_change_recent: number;
  integrity_verified: boolean;
  event_counts: Record<string, number>;
}

export interface CritiquePattern {
  pattern: string;
  issue_type: string;
  suggested_rebuttal: string;
  success_rate: number;
  usage_count: number;
}

export interface LaboratoryPanelProps {
  apiBase?: string;
}

export type LaboratoryTab = 'traits' | 'pollinations' | 'evolution' | 'patterns';
