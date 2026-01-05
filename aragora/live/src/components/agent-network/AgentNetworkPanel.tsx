'use client';

import { useState, useEffect } from 'react';
import { useAgentNetwork } from './useAgentNetwork';
import { NetworkGraph } from './NetworkGraph';
import { RelationshipList } from './RelationshipList';
import { MomentsSection } from './MomentsSection';
import { AgentSelector } from './AgentSelector';
import type { AgentNetworkPanelProps } from './types';
import { DEFAULT_API_BASE } from './types';

export function AgentNetworkPanel({
  selectedAgent,
  apiBase = DEFAULT_API_BASE,
  onAgentSelect,
}: AgentNetworkPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [viewMode, setViewMode] = useState<'graph' | 'list'>('graph');
  const [agentInput, setAgentInput] = useState(selectedAgent || '');

  const { network, moments, loading, error, availableAgents, fetchNetwork } = useAgentNetwork(apiBase);

  useEffect(() => {
    if (!agentInput && availableAgents.length > 0) {
      setAgentInput(availableAgents[0]);
    }
  }, [availableAgents, agentInput]);

  useEffect(() => {
    if (selectedAgent) {
      setAgentInput(selectedAgent);
      fetchNetwork(selectedAgent);
    }
  }, [selectedAgent, fetchNetwork]);

  const handleFetch = () => {
    if (agentInput) {
      fetchNetwork(agentInput);
    }
  };

  const handleAgentClick = (agent: string) => {
    setAgentInput(agent);
    fetchNetwork(agent);
    onAgentSelect?.(agent);
  };

  // Collapsed view
  if (!isExpanded) {
    return (
      <div
        className="border border-blue-500/30 bg-surface/50 p-3 cursor-pointer hover:border-blue-500/50 transition-colors"
        onClick={() => setIsExpanded(true)}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono text-blue-400">
            {'>'} AGENT_NETWORK {network ? `[${network.agent}]` : ''}
          </h3>
          <div className="flex items-center gap-2">
            {network && (
              <span className="text-xs font-mono text-text-muted">
                {network.rivals?.length || 0} rivals, {network.allies?.length || 0} allies
              </span>
            )}
            <span className="text-xs text-text-muted">[EXPAND]</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-blue-500/30 bg-surface/50 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-mono text-blue-400">{'>'} AGENT_NETWORK</h3>
        <button onClick={() => setIsExpanded(false)} className="text-xs text-text-muted hover:text-blue-400">
          [COLLAPSE]
        </button>
      </div>

      <AgentSelector
        value={agentInput}
        onChange={setAgentInput}
        onFetch={handleFetch}
        availableAgents={availableAgents}
        loading={loading}
      />

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">{error}</div>
      )}

      {network && (
        <div className="space-y-4">
          {/* Agent Header with View Toggle */}
          <NetworkHeader network={network} viewMode={viewMode} onViewModeChange={setViewMode} />

          {/* Graph View */}
          {viewMode === 'graph' && (
            <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
              <NetworkGraph
                network={network}
                onNodeClick={(agent) => {
                  if (agent !== network.agent) handleAgentClick(agent);
                }}
              />
              <p className="text-xs text-zinc-500 mt-2 text-center">
                Click on a node to explore that agent&apos;s network
              </p>
            </div>
          )}

          {/* List View */}
          {viewMode === 'list' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
                <RelationshipList
                  title="Rivals"
                  items={network.rivals}
                  icon="⚔️"
                  colorClass="bg-red-900/20 border border-red-800/30 text-red-400"
                  onAgentClick={handleAgentClick}
                />
              </div>
              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
                <RelationshipList
                  title="Allies"
                  items={network.allies}
                  icon="🤝"
                  colorClass="bg-green-900/20 border border-green-800/30 text-green-400"
                  onAgentClick={handleAgentClick}
                />
              </div>
              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
                <RelationshipList
                  title="Influences"
                  items={network.influences}
                  icon="📤"
                  colorClass="bg-blue-900/20 border border-blue-800/30 text-blue-400"
                  onAgentClick={handleAgentClick}
                />
              </div>
              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
                <RelationshipList
                  title="Influenced By"
                  items={network.influenced_by}
                  icon="📥"
                  colorClass="bg-purple-900/20 border border-purple-800/30 text-purple-400"
                  onAgentClick={handleAgentClick}
                />
              </div>
            </div>
          )}

          <MomentsSection moments={moments} />
        </div>
      )}

      {!network && !loading && !error && (
        <div className="text-center py-8 text-zinc-500">Select an agent to view their relationship network</div>
      )}

      <div className="mt-3 text-[10px] text-text-muted font-mono">
        Agent rivalry and alliance relationship visualization
      </div>
    </div>
  );
}

interface NetworkHeaderProps {
  network: { agent: string; rivals?: unknown[]; allies?: unknown[]; influences?: unknown[]; influenced_by?: unknown[] };
  viewMode: 'graph' | 'list';
  onViewModeChange: (mode: 'graph' | 'list') => void;
}

function NetworkHeader({ network, viewMode, onViewModeChange }: NetworkHeaderProps) {
  return (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-lg font-medium text-white">{network.agent}&apos;s Relationship Network</h4>
        <div className="flex gap-1">
          <button
            onClick={() => onViewModeChange('graph')}
            className={`px-2 py-1 text-xs rounded ${
              viewMode === 'graph' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-400 hover:bg-zinc-600'
            }`}
          >
            Graph
          </button>
          <button
            onClick={() => onViewModeChange('list')}
            className={`px-2 py-1 text-xs rounded ${
              viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-zinc-700 text-zinc-400 hover:bg-zinc-600'
            }`}
          >
            List
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="text-zinc-400">
          <span className="text-white font-medium">{network.rivals?.length || 0}</span> rivals
        </div>
        <div className="text-zinc-400">
          <span className="text-white font-medium">{network.allies?.length || 0}</span> allies
        </div>
        <div className="text-zinc-400">
          <span className="text-white font-medium">{network.influences?.length || 0}</span> influenced
        </div>
        <div className="text-zinc-400">
          <span className="text-white font-medium">{network.influenced_by?.length || 0}</span> influencers
        </div>
      </div>
    </div>
  );
}

export default AgentNetworkPanel;
