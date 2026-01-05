'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchWithRetry } from '@/utils/retry';
import { TabNavigation } from '../shared';
import { InsightsListTab } from './InsightsListTab';
import { MemoryTab } from './MemoryTab';
import { FlipsTab } from './FlipsTab';
import { LearningTab } from './LearningTab';
import type {
  Insight,
  MemoryRecall,
  FlipEvent,
  FlipSummary,
  InsightsPanelProps,
  InsightsTab as InsightsTabType,
} from './types';

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.aragora.ai';

const FLIP_TYPE_EMOJIS: Record<string, string> = {
  contradiction: '🔄',
  retraction: '↩️',
  qualification: '⚖️',
  refinement: '✨',
};

export function InsightsPanel({ wsMessages = [], apiBase = DEFAULT_API_BASE }: InsightsPanelProps) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [memoryRecalls, setMemoryRecalls] = useState<MemoryRecall[]>([]);
  const [flips, setFlips] = useState<FlipEvent[]>([]);
  const [flipSummary, setFlipSummary] = useState<FlipSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<InsightsTabType>('insights');

  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetchWithRetry(
        `${apiBase}/api/insights/recent?limit=10`,
        undefined,
        { maxRetries: 2 }
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setInsights(data.insights || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch insights');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  const fetchFlips = useCallback(async () => {
    // Use allSettled to handle partial failures gracefully
    const [flipsResult, summaryResult] = await Promise.allSettled([
      fetchWithRetry(`${apiBase}/api/flips/recent?limit=15`, undefined, { maxRetries: 2 }),
      fetchWithRetry(`${apiBase}/api/flips/summary`, undefined, { maxRetries: 2 }),
    ]);

    if (flipsResult.status === 'fulfilled' && flipsResult.value.ok) {
      const flipsData = await flipsResult.value.json();
      setFlips(flipsData.flips || []);
    }

    if (summaryResult.status === 'fulfilled' && summaryResult.value.ok) {
      const summaryData = await summaryResult.value.json();
      setFlipSummary(summaryData.summary || null);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchInsights();
    fetchFlips();
  }, [fetchInsights, fetchFlips]);

  // Listen for memory_recall WebSocket events
  useEffect(() => {
    const recallMessages: MemoryRecall[] = wsMessages
      .filter((msg) => msg.type === 'memory_recall')
      .map((msg) => {
        const data = msg.data as Record<string, unknown>;
        return {
          query: (data.query as string) || '',
          hits: (data.hits as Array<{ topic: string; similarity: number }>) || [],
          count: (data.count as number) || 0,
          timestamp: msg.timestamp ? new Date(msg.timestamp).toISOString() : new Date().toISOString(),
        };
      });

    if (recallMessages.length > 0) {
      setMemoryRecalls((prev) => {
        const newRecalls = [...recallMessages, ...prev].slice(0, 20);
        return newRecalls;
      });
    }
  }, [wsMessages]);

  // Listen for flip_detected WebSocket events for real-time flip updates
  useEffect(() => {
    const flipMessages: FlipEvent[] = wsMessages
      .filter((msg) => msg.type === 'flip_detected')
      .map((msg) => {
        const data = (msg.data || {}) as Record<string, unknown>;
        const beforeData = data.before as Record<string, unknown> | undefined;
        const afterData = data.after as Record<string, unknown> | undefined;
        const flipType = String(data.flip_type || data.type || 'unknown');
        const origConf = data.original_confidence as number | undefined;
        const newConf = data.new_confidence as number | undefined;
        const simScore = data.similarity_score as number | undefined;

        return {
          id: String(data.id || `flip-${Date.now()}-${Math.random().toString(36).slice(2)}`),
          agent: String(data.agent_name || data.agent || 'unknown'),
          type: flipType as FlipEvent['type'],
          type_emoji: FLIP_TYPE_EMOJIS[flipType] || '❓',
          before: {
            claim: String(data.original_claim || beforeData?.claim || ''),
            confidence: origConf ? `${(origConf * 100).toFixed(0)}%` : String(beforeData?.confidence || 'N/A'),
          },
          after: {
            claim: String(data.new_claim || afterData?.claim || ''),
            confidence: newConf ? `${(newConf * 100).toFixed(0)}%` : String(afterData?.confidence || 'N/A'),
          },
          similarity: simScore ? `${(simScore * 100).toFixed(0)}%` : String(data.similarity || 'N/A'),
          domain: data.domain ? String(data.domain) : null,
          timestamp: msg.timestamp
            ? new Date(msg.timestamp).toISOString()
            : String(data.detected_at || new Date().toISOString()),
        };
      });

    if (flipMessages.length > 0) {
      setFlips((prev) => {
        // Deduplicate by ID and keep newest first
        const existingIds = new Set(prev.map((f) => f.id));
        const newFlips = flipMessages.filter((f) => !existingIds.has(f.id));
        return [...newFlips, ...prev].slice(0, 50);
      });
      // Auto-switch to flips tab when new flip detected
      if (activeTab !== 'flips') {
        setActiveTab('flips');
      }
    }
  }, [wsMessages, activeTab]);

  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId as InsightsTabType);
  }, []);

  // Dynamic tabs with counts
  const tabs = [
    { id: 'insights', label: `Insights (${insights.length})` },
    { id: 'memory', label: `Memory (${memoryRecalls.length})` },
    { id: 'flips', label: `Flips (${flips.length})` },
    { id: 'learning', label: 'Learning' },
  ];

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text">Debate Insights</h3>
        <button
          onClick={fetchInsights}
          className="px-2 py-1 bg-surface border border-border rounded text-sm text-text hover:bg-surface-hover"
        >
          Refresh
        </button>
      </div>

      {/* Tab Navigation */}
      <TabNavigation
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      {/* Tab Content */}
      {activeTab === 'insights' && (
        <InsightsListTab
          insights={insights}
          loading={loading}
          error={error}
          onRetry={fetchInsights}
        />
      )}

      {activeTab === 'memory' && <MemoryTab memoryRecalls={memoryRecalls} />}

      {activeTab === 'flips' && <FlipsTab flips={flips} flipSummary={flipSummary} />}

      {activeTab === 'learning' && <LearningTab />}
    </div>
  );
}
