'use client';

import type { AgentSelectorProps } from './types';

export function AgentSelector({ value, onChange, onFetch, availableAgents, loading }: AgentSelectorProps) {
  return (
    <div className="flex gap-2 mb-4">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-zinc-300"
      >
        <option value="">Select an agent...</option>
        {availableAgents.map((agent) => (
          <option key={agent} value={agent}>
            {agent}
          </option>
        ))}
      </select>
      <button
        onClick={onFetch}
        disabled={!value || loading}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded"
      >
        {loading ? 'Loading...' : 'View Network'}
      </button>
    </div>
  );
}
