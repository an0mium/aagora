'use client';

import { useState, useEffect, useCallback, useMemo, memo, useRef } from 'react';
import { AgentMomentsModal } from '../AgentMomentsModal';
import { LeaderboardSkeleton } from '../Skeleton';
import { TabNavigation } from '../shared';
import { RankingsTab } from './RankingsTab';
import { MatchesTab } from './MatchesTab';
import { ReputationTab } from './ReputationTab';
import { TeamsTab } from './TeamsTab';
import { StatsTab } from './StatsTab';
import { MindsTab } from './MindsTab';
import { DomainFilter } from './DomainFilter';
import type {
  AgentRanking,
  Match,
  AgentReputation,
  TeamCombination,
  RankingStats,
  AgentIntrospection,
  LeaderboardPanelProps,
  LeaderboardTab,
} from './types';
import type { StreamEvent } from '@/types/events';

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.aragora.ai';

const TABS = [
  { id: 'rankings', label: 'Rankings' },
  { id: 'matches', label: 'Matches' },
  { id: 'reputation', label: 'Reputation' },
  { id: 'teams', label: 'Teams' },
  { id: 'stats', label: 'Stats' },
  { id: 'minds', label: 'Minds' },
] as const;

function LeaderboardPanelComponent({ wsMessages = [], loopId, apiBase = DEFAULT_API_BASE }: LeaderboardPanelProps) {
  const [agents, setAgents] = useState<AgentRanking[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [reputations, setReputations] = useState<AgentReputation[]>([]);
  const [teams, setTeams] = useState<TeamCombination[]>([]);
  const [stats, setStats] = useState<RankingStats | null>(null);
  const [introspections, setIntrospections] = useState<AgentIntrospection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [endpointErrors, setEndpointErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<LeaderboardTab>('rankings');
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [availableDomains, setAvailableDomains] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);

    // Build query params for consolidated endpoint
    const params = new URLSearchParams({ limit: '10' });
    if (loopId) params.set('loop_id', loopId);
    if (selectedDomain) params.set('domain', selectedDomain);

    try {
      // Single consolidated request instead of 6 separate calls
      const res = await fetch(`${apiBase}/api/leaderboard-view?${params}`);

      if (!res.ok) {
        const errorText = await res.text().catch(() => 'Unknown error');
        throw new Error(`${res.status}: ${errorText.slice(0, 100)}`);
      }

      const response = await res.json();
      const { data, errors: apiErrors } = response;

      // Update state from consolidated response
      if (data.rankings) {
        const agentsList: AgentRanking[] = data.rankings.agents || [];
        setAgents(agentsList);
      }

      if (data.matches) {
        setMatches(data.matches.matches || []);
        const domainSet = new Set<string>(
          (data.matches.matches || []).map((m: Match) => m.domain).filter(Boolean)
        );
        const matchDomains = Array.from(domainSet);
        if (matchDomains.length > 0) {
          setAvailableDomains(prev => Array.from(new Set([...prev, ...matchDomains])));
        }
      }

      if (data.reputation) {
        setReputations(data.reputation.reputations || []);
      }

      if (data.teams) {
        setTeams(data.teams.combinations || []);
      }

      if (data.stats) {
        setStats(data.stats);
      }

      if (data.introspection) {
        // Convert object to array for compatibility
        const introArray = Object.values(data.introspection.agents || {}) as AgentIntrospection[];
        setIntrospections(introArray);
      }

      // Handle partial failures from consolidated endpoint
      if (apiErrors?.partial_failure) {
        setEndpointErrors(apiErrors.messages || {});
        setError(`${apiErrors.failed_sections?.length || 0} section(s) unavailable`);
      } else {
        setEndpointErrors({});
        setError(null);
      }
    } catch (err) {
      // Fallback: consolidated endpoint failed, try legacy endpoints
      console.warn('Consolidated endpoint failed, falling back to legacy:', err);
      const errors: Record<string, string> = {};
      const endpoints = [
        { key: 'rankings', url: `${apiBase}/api/leaderboard?limit=10${loopId ? `&loop_id=${loopId}` : ''}${selectedDomain ? `&domain=${selectedDomain}` : ''}` },
        { key: 'matches', url: `${apiBase}/api/matches/recent?limit=5${loopId ? `&loop_id=${loopId}` : ''}` },
        { key: 'reputation', url: `${apiBase}/api/reputation/all` },
        { key: 'teams', url: `${apiBase}/api/routing/best-teams?min_debates=3&limit=10` },
        { key: 'stats', url: `${apiBase}/api/ranking/stats` },
        { key: 'minds', url: `${apiBase}/api/introspection/all` },
      ];
      const results = await Promise.allSettled(
        endpoints.map(async ({ key, url }) => {
          const r = await fetch(url);
          if (!r.ok) throw new Error(`${r.status}`);
          return { key, data: await r.json() };
        })
      );
      results.forEach((result, idx) => {
        const { key } = endpoints[idx];
        if (result.status === 'rejected') { errors[key] = result.reason?.message || 'Failed'; return; }
        const { data } = result.value;
        switch (key) {
          case 'rankings': setAgents(data.agents || data.rankings || []); break;
          case 'matches': setMatches(data.matches || []); break;
          case 'reputation': setReputations(data.reputations || []); break;
          case 'teams': setTeams(data.combinations || []); break;
          case 'stats': setStats(data); break;
          case 'minds': setIntrospections(Object.values(data.agents || {}) as AgentIntrospection[]); break;
        }
      });
      setEndpointErrors(errors);
      if (Object.keys(errors).length === endpoints.length) {
        setError('All endpoints failed.');
      } else if (Object.keys(errors).length > 0) {
        setError(`${Object.keys(errors).length} endpoint(s) unavailable`);
      }
    }

    setLoading(false);
  }, [apiBase, loopId, selectedDomain]);

  // Use ref to store latest fetchData to avoid interval recreation on dependency changes
  const fetchDataRef = useRef(fetchData);
  fetchDataRef.current = fetchData;

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Separate effect for interval - runs once, uses ref to call latest fetchData
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDataRef.current();
    }, 30000);
    return () => clearInterval(interval);
  }, []); // Empty deps - interval created once

  // Memoize filtered match events to avoid recalculating on every render
  const matchEvents = useMemo(() => {
    return wsMessages.filter((msg) => {
      if (msg.type !== 'match_recorded') return false;
      const msgData = msg.data as Record<string, unknown>;
      const msgLoopId = msgData?.loop_id as string | undefined;
      if (loopId && msgLoopId && msgLoopId !== loopId) return false;
      return true;
    });
  }, [wsMessages, loopId]);

  // Listen for match_recorded WebSocket events for real-time updates (debate consensus feature)
  useEffect(() => {
    if (matchEvents.length > 0) {
      const latestEvent = matchEvents[matchEvents.length - 1];
      const eventData = latestEvent.data as Record<string, unknown>;
      const eventId = eventData?.debate_id as string | undefined;

      // Only refresh if this is a new match event
      if (eventId && eventId !== lastEventId) {
        setLastEventId(eventId);
        fetchData(); // Refresh leaderboard when a match is recorded

        // Track new domains from match events
        const eventDomain = eventData?.domain as string | undefined;
        if (eventDomain && !availableDomains.includes(eventDomain)) {
          setAvailableDomains(prev => [...prev, eventDomain]);
        }
      }
    }
  }, [matchEvents, lastEventId, fetchData, availableDomains]);

  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId as LeaderboardTab);
  }, []);

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text">Agent Leaderboard</h3>
        <button
          onClick={fetchData}
          className="px-2 py-1 bg-surface border border-border rounded text-sm text-text hover:bg-surface-hover"
        >
          Refresh
        </button>
      </div>

      {/* Domain Filter */}
      <div className="mb-3">
        <DomainFilter
          domains={availableDomains}
          selectedDomain={selectedDomain}
          onDomainChange={setSelectedDomain}
        />
      </div>

      {/* Tab Navigation */}
      <TabNavigation
        tabs={TABS as unknown as { id: string; label: string }[]}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      {/* Per-tab endpoint error indicator (for non-rankings tabs) */}
      {activeTab !== 'rankings' && endpointErrors[activeTab] && !error?.includes('All endpoints') && (
        <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-2 mb-2 text-xs text-yellow-400">
          This tab&apos;s data is unavailable: {endpointErrors[activeTab]}
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'rankings' && (
        <RankingsTab
          agents={agents}
          loading={loading}
          error={error}
          endpointErrors={endpointErrors}
        />
      )}

      {activeTab === 'matches' && (
        <MatchesTab matches={matches} loading={loading} />
      )}

      {activeTab === 'reputation' && (
        <ReputationTab reputations={reputations} loading={loading} />
      )}

      {activeTab === 'teams' && (
        <TeamsTab teams={teams} loading={loading} />
      )}

      {activeTab === 'stats' && (
        <StatsTab stats={stats} loading={loading} />
      )}

      {activeTab === 'minds' && (
        <MindsTab introspections={introspections} loading={loading} />
      )}

      {/* Agent Moments Modal */}
      {selectedAgent && (
        <AgentMomentsModal
          agentName={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          apiBase={apiBase}
        />
      )}
    </div>
  );
}

// Memoize the component to prevent re-renders when parent re-renders with same props
export const LeaderboardPanel = memo(LeaderboardPanelComponent);
