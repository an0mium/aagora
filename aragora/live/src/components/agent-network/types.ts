export interface RelationshipEntry {
  agent: string;
  score: number;
  debate_count?: number;
}

export interface NetworkNode {
  id: string;
  x: number;
  y: number;
  type: 'center' | 'rival' | 'ally' | 'influence' | 'influenced_by';
}

export interface NetworkEdge {
  source: string;
  target: string;
  type: 'rival' | 'ally' | 'influence' | 'influenced_by';
  strength: number;
}

export interface AgentNetwork {
  agent: string;
  influences: RelationshipEntry[];
  influenced_by: RelationshipEntry[];
  rivals: RelationshipEntry[];
  allies: RelationshipEntry[];
}

export interface SignificantMoment {
  type: string;
  description: string;
  significance: number;
  debate_id?: string;
  timestamp?: string;
}

export interface AgentNetworkPanelProps {
  selectedAgent?: string;
  apiBase?: string;
  onAgentSelect?: (agent: string) => void;
}

export interface NetworkGraphProps {
  network: AgentNetwork;
  onNodeClick?: (agent: string) => void;
}

export interface RelationshipListProps {
  title: string;
  items: RelationshipEntry[];
  icon: string;
  colorClass: string;
  onAgentClick: (agent: string) => void;
}

export interface AgentSelectorProps {
  value: string;
  onChange: (value: string) => void;
  onFetch: () => void;
  availableAgents: string[];
  loading: boolean;
}

export const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.aragora.ai';

export const NODE_COLORS: Record<NetworkNode['type'], string> = {
  center: '#22d3ee',
  rival: '#ef4444',
  ally: '#22c55e',
  influence: '#3b82f6',
  influenced_by: '#a855f7',
};

export const EDGE_COLORS: Record<NetworkEdge['type'], string> = {
  rival: 'rgba(239, 68, 68, 0.5)',
  ally: 'rgba(34, 197, 94, 0.5)',
  influence: 'rgba(59, 130, 246, 0.5)',
  influenced_by: 'rgba(168, 85, 247, 0.5)',
};
