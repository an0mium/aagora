import { useState, useEffect, useCallback } from 'react';
import type { AgentNetwork, SignificantMoment } from './types';
import { DEFAULT_API_BASE } from './types';

interface UseAgentNetworkResult {
  network: AgentNetwork | null;
  moments: SignificantMoment[];
  loading: boolean;
  error: string | null;
  availableAgents: string[];
  fetchNetwork: (agent: string) => Promise<void>;
}

export function useAgentNetwork(apiBase: string = DEFAULT_API_BASE): UseAgentNetworkResult {
  const [network, setNetwork] = useState<AgentNetwork | null>(null);
  const [moments, setMoments] = useState<SignificantMoment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${apiBase}/api/leaderboard?limit=20`)
      .then((res) => res.json())
      .then((data: { agents?: Array<{ name: string }> }) => {
        const agents = (data.agents || []).map((a) => a.name);
        setAvailableAgents(agents);
      })
      .catch(() => {});
  }, [apiBase]);

  const fetchNetwork = useCallback(
    async (agent: string) => {
      if (!agent) return;

      setLoading(true);
      setError(null);

      try {
        const [networkRes, momentsRes] = await Promise.all([
          fetch(`${apiBase}/api/agent/${encodeURIComponent(agent)}/network`),
          fetch(`${apiBase}/api/agent/${encodeURIComponent(agent)}/moments?limit=5`),
        ]);

        if (!networkRes.ok) {
          throw new Error(`Failed to fetch network: ${networkRes.statusText}`);
        }

        const networkData = await networkRes.json();
        setNetwork(networkData);

        if (momentsRes.ok) {
          const momentsData = await momentsRes.json();
          setMoments(momentsData.moments || []);
        } else {
          setMoments([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load network');
      } finally {
        setLoading(false);
      }
    },
    [apiBase]
  );

  return { network, moments, loading, error, availableAgents, fetchNetwork };
}
