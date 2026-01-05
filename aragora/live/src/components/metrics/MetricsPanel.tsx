'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { ErrorWithRetry } from '../RetryButton';
import { fetchWithRetry } from '@/utils/retry';
import { RefreshButton, ExpandToggle } from '../shared';
import { getStatusColor } from '@/utils/colors';
import { OverviewTab } from './OverviewTab';
import { HealthTab } from './HealthTab';
import { CacheTab } from './CacheTab';
import { SystemTab } from './SystemTab';
import type {
  MetricsData,
  HealthData,
  CacheData,
  SystemData,
  MetricsPanelProps,
  MetricsTab,
} from './types';

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.aragora.ai';

const TAB_STYLES: Record<MetricsTab, string> = {
  overview: 'bg-acid-cyan text-bg font-medium',
  health: 'bg-green-500 text-bg font-medium',
  cache: 'bg-purple-500 text-bg font-medium',
  system: 'bg-yellow-500 text-bg font-medium',
};

const TAB_LABELS: Record<MetricsTab, string> = {
  overview: 'OVERVIEW',
  health: 'HEALTH',
  cache: 'CACHE',
  system: 'SYSTEM',
};

export function MetricsPanel({ apiBase = DEFAULT_API_BASE }: MetricsPanelProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [cache, setCache] = useState<CacheData | null>(null);
  const [system, setSystem] = useState<SystemData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MetricsTab>('overview');
  const [expanded, setExpanded] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      fetchWithRetry(`${apiBase}/api/metrics`, undefined, { maxRetries: 2 }),
      fetchWithRetry(`${apiBase}/api/metrics/health`, undefined, { maxRetries: 2 }),
      fetchWithRetry(`${apiBase}/api/metrics/cache`, undefined, { maxRetries: 2 }),
      fetchWithRetry(`${apiBase}/api/metrics/system`, undefined, { maxRetries: 2 }),
    ]);

    const [metricsResult, healthResult, cacheResult, systemResult] = results;
    let hasError = false;

    if (metricsResult.status === 'fulfilled' && metricsResult.value.ok) {
      const data = await metricsResult.value.json();
      setMetrics(data);
    } else {
      hasError = true;
    }

    if (healthResult.status === 'fulfilled' && healthResult.value.ok) {
      const data = await healthResult.value.json();
      setHealth(data);
    } else {
      hasError = true;
    }

    if (cacheResult.status === 'fulfilled' && cacheResult.value.ok) {
      const data = await cacheResult.value.json();
      setCache(data);
    } else {
      hasError = true;
    }

    if (systemResult.status === 'fulfilled' && systemResult.value.ok) {
      const data = await systemResult.value.json();
      setSystem(data);
    } else {
      hasError = true;
    }

    if (hasError) {
      setError('Some metrics failed to load. Partial results shown.');
    }
    setLoading(false);
  }, [apiBase]);

  const fetchDataRef = useRef(fetchData);
  fetchDataRef.current = fetchData;

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchDataRef.current();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = useCallback((tabId: MetricsTab) => {
    setActiveTab(tabId);
  }, []);

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text font-mono">Server Metrics</h3>
        <div className="flex items-center gap-2">
          <RefreshButton onClick={fetchData} loading={loading} />
          <ExpandToggle expanded={expanded} onToggle={() => setExpanded(!expanded)} />
        </div>
      </div>

      {/* Summary Stats */}
      <div className="flex items-center gap-4 text-xs font-mono text-text-muted mb-4 border-b border-border pb-3 flex-wrap">
        <span>
          Uptime: <span className="text-acid-cyan">{metrics?.uptime_human || '-'}</span>
        </span>
        <span>
          Requests: <span className="text-acid-green">{metrics?.requests.total.toLocaleString() || 0}</span>
        </span>
        <span>
          Error Rate:{' '}
          <span
            className={metrics?.requests.error_rate && metrics.requests.error_rate > 0.01 ? 'text-red-400' : 'text-green-400'}
          >
            {((metrics?.requests.error_rate || 0) * 100).toFixed(2)}%
          </span>
        </span>
        <span>
          Cache: <span className="text-purple-400">{cache?.hit_rate ? `${(cache.hit_rate * 100).toFixed(1)}% hit` : '-'}</span>
        </span>
        {health && (
          <span>
            Health: <span className={getStatusColor(health.status)}>{health.status.toUpperCase()}</span>
          </span>
        )}
      </div>

      {error && <ErrorWithRetry error={error} onRetry={fetchData} className="mb-4" />}

      {expanded && (
        <>
          {/* Tab Navigation */}
          <div className="flex space-x-1 bg-bg border border-border rounded p-1 mb-4">
            {(Object.keys(TAB_LABELS) as MetricsTab[]).map((tabId) => (
              <button
                key={tabId}
                role="tab"
                aria-selected={activeTab === tabId}
                onClick={() => handleTabChange(tabId)}
                className={`px-3 py-1 rounded text-sm font-mono transition-colors flex-1 ${
                  activeTab === tabId ? TAB_STYLES[tabId] : 'text-text-muted hover:text-text'
                }`}
              >
                {TAB_LABELS[tabId]}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && <OverviewTab metrics={metrics} loading={loading} />}
          {activeTab === 'health' && <HealthTab health={health} loading={loading} />}
          {activeTab === 'cache' && <CacheTab cache={cache} loading={loading} />}
          {activeTab === 'system' && <SystemTab system={system} loading={loading} />}
        </>
      )}

      {/* Help text when collapsed */}
      {!expanded && (
        <div className="text-xs font-mono text-text-muted">
          <p>
            <span className="text-acid-cyan">Uptime:</span> {metrics?.uptime_human || '-'} |{' '}
            <span className="text-acid-green">Requests:</span> {metrics?.requests.total.toLocaleString() || 0} |{' '}
            <span className="text-purple-400">Cache:</span> {cache?.hit_rate ? `${(cache.hit_rate * 100).toFixed(1)}%` : '-'}
          </p>
        </div>
      )}
    </div>
  );
}
