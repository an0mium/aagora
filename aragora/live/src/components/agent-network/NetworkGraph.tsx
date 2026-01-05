'use client';

import { useMemo } from 'react';
import type { NetworkGraphProps, NetworkNode, NetworkEdge } from './types';
import { NODE_COLORS, EDGE_COLORS } from './types';

const WIDTH = 400;
const HEIGHT = 300;
const CENTER_X = WIDTH / 2;
const CENTER_Y = HEIGHT / 2;
const RADIUS = 100;

export function NetworkGraph({ network, onNodeClick }: NetworkGraphProps) {
  const { nodes, edges } = useMemo(() => {
    const nodeList: NetworkNode[] = [];
    const edgeList: NetworkEdge[] = [];
    const seenAgents = new Set<string>();

    nodeList.push({
      id: network.agent,
      x: CENTER_X,
      y: CENTER_Y,
      type: 'center',
    });
    seenAgents.add(network.agent);

    const relatedAgents: { agent: string; type: NetworkEdge['type']; score: number }[] = [];

    network.rivals?.forEach((r) => {
      if (!seenAgents.has(r.agent)) {
        relatedAgents.push({ agent: r.agent, type: 'rival', score: r.score });
        seenAgents.add(r.agent);
      }
    });
    network.allies?.forEach((a) => {
      if (!seenAgents.has(a.agent)) {
        relatedAgents.push({ agent: a.agent, type: 'ally', score: a.score });
        seenAgents.add(a.agent);
      }
    });
    network.influences?.forEach((i) => {
      if (!seenAgents.has(i.agent)) {
        relatedAgents.push({ agent: i.agent, type: 'influence', score: i.score });
        seenAgents.add(i.agent);
      }
    });
    network.influenced_by?.forEach((i) => {
      if (!seenAgents.has(i.agent)) {
        relatedAgents.push({ agent: i.agent, type: 'influenced_by', score: i.score });
        seenAgents.add(i.agent);
      }
    });

    const angleStep = (2 * Math.PI) / Math.max(relatedAgents.length, 1);
    relatedAgents.forEach((rel, idx) => {
      const angle = idx * angleStep - Math.PI / 2;
      nodeList.push({
        id: rel.agent,
        x: CENTER_X + RADIUS * Math.cos(angle),
        y: CENTER_Y + RADIUS * Math.sin(angle),
        type: rel.type,
      });
      edgeList.push({
        source: network.agent,
        target: rel.agent,
        type: rel.type,
        strength: rel.score,
      });
    });

    return { nodes: nodeList, edges: edgeList };
  }, [network]);

  const nodeById = useMemo(() => {
    const map: Record<string, NetworkNode> = {};
    nodes.forEach((n) => {
      map[n.id] = n;
    });
    return map;
  }, [nodes]);

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full h-64 bg-zinc-900/50 rounded-lg">
      {/* Edges */}
      {edges.map((edge, idx) => {
        const source = nodeById[edge.source];
        const target = nodeById[edge.target];
        if (!source || !target) return null;
        return (
          <line
            key={idx}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            stroke={EDGE_COLORS[edge.type]}
            strokeWidth={Math.max(1, edge.strength * 3)}
            strokeDasharray={edge.type === 'rival' ? '4,2' : undefined}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <g
          key={node.id}
          transform={`translate(${node.x}, ${node.y})`}
          className="cursor-pointer"
          onClick={() => onNodeClick?.(node.id)}
        >
          <circle
            r={node.type === 'center' ? 20 : 15}
            fill={NODE_COLORS[node.type]}
            stroke={node.type === 'center' ? '#fff' : 'transparent'}
            strokeWidth={node.type === 'center' ? 2 : 0}
            className="hover:opacity-80 transition-opacity"
          />
          <text textAnchor="middle" dy={node.type === 'center' ? 35 : 28} className="text-[10px] fill-zinc-400">
            {node.id.length > 12 ? node.id.slice(0, 10) + '...' : node.id}
          </text>
        </g>
      ))}

      {/* Legend */}
      <g transform="translate(10, 10)">
        <circle cx="6" cy="6" r="4" fill="#ef4444" />
        <text x="14" y="9" className="text-[8px] fill-zinc-500">
          Rival
        </text>
        <circle cx="6" cy="20" r="4" fill="#22c55e" />
        <text x="14" y="23" className="text-[8px] fill-zinc-500">
          Ally
        </text>
        <circle cx="56" cy="6" r="4" fill="#3b82f6" />
        <text x="64" y="9" className="text-[8px] fill-zinc-500">
          Influences
        </text>
        <circle cx="56" cy="20" r="4" fill="#a855f7" />
        <text x="64" y="23" className="text-[8px] fill-zinc-500">
          Influenced By
        </text>
      </g>
    </svg>
  );
}
