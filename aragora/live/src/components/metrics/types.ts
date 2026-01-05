export interface MetricsData {
  uptime_seconds: number;
  uptime_human: string;
  requests: {
    total: number;
    errors: number;
    error_rate: number;
    top_endpoints: { endpoint: string; count: number }[];
  };
  cache: {
    entries: number;
  };
  databases: Record<string, { bytes: number; human: string }>;
  timestamp: string;
}

export interface HealthData {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, { status: string; error?: string; path?: string }>;
}

export interface CacheData {
  total_entries: number;
  max_entries: number;
  hit_rate: number;
  hits: number;
  misses: number;
  entries_by_prefix: Record<string, number>;
  oldest_entry_age_seconds: number;
  newest_entry_age_seconds: number;
}

export interface SystemData {
  python_version: string;
  platform: string;
  machine: string;
  processor: string;
  pid: number;
  memory?:
    | {
        rss_mb: number;
        vms_mb: number;
      }
    | { available: false; reason: string };
}

export interface MetricsPanelProps {
  apiBase?: string;
}

export type MetricsTab = 'overview' | 'health' | 'cache' | 'system';
