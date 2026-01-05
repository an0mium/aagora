'use client';

import { useState, useMemo } from 'react';
import type { StreamEvent, AuditFinding } from '@/types/events';
import { RoleBadge } from './RoleBadge';
import { CitationBadge } from './CitationsPanel';

interface DeepAuditViewProps {
  events: StreamEvent[];
  isActive: boolean;
  onToggle: () => void;
}

// Deep Audit rounds (Heavy3-inspired 6-round protocol)
const AUDIT_ROUNDS = [
  { round: 1, name: 'Initial Analysis', icon: '🔬', description: 'Agents present initial assessments' },
  { round: 2, name: 'Skeptical Review', icon: '🤔', description: 'Challenge assumptions and identify gaps' },
  { round: 3, name: 'Lateral Exploration', icon: '💡', description: 'Explore alternative perspectives' },
  { round: 4, name: 'Devil\'s Advocacy', icon: '😈', description: 'Argue against the emerging consensus' },
  { round: 5, name: 'Synthesis', icon: '⚖️', description: 'Integrate insights into recommendations' },
  { round: 6, name: 'Cross-Examination', icon: '🎯', description: 'Final probing of conclusions' },
];

interface RoundData {
  round: number;
  name?: string;
  cognitiveRole?: string;
  messages: Array<{
    agent: string;
    content: string;
    role: string;
    cognitiveRole?: string;
    confidence?: number;
    citations?: number;
    timestamp: number;
  }>;
  status: 'pending' | 'active' | 'complete';
  durationMs?: number;
}

interface AuditState {
  auditId?: string;
  task?: string;
  agents?: string[];
  findings: AuditFinding[];
  crossExamNotes?: string;
  verdict?: {
    recommendation: string;
    confidence: number;
    unanimousIssues: string[];
    splitOpinions: string[];
    riskAreas: string[];
  };
}

export function DeepAuditView({ events, isActive, onToggle }: DeepAuditViewProps) {
  const [expandedRound, setExpandedRound] = useState<number | null>(null);
  const [showFindings, setShowFindings] = useState(false);

  // Extract round data and audit state from events
  const { roundData, auditState } = useMemo(() => {
    const rounds: Record<number, RoundData> = {};
    let maxRound = 0;
    const state: AuditState = { findings: [] };

    // Initialize rounds
    AUDIT_ROUNDS.forEach((r) => {
      rounds[r.round] = {
        round: r.round,
        messages: [],
        status: 'pending',
      };
    });

    // Process all event types
    events.forEach((event) => {
      // Handle audit_start event
      if (event.type === 'audit_start') {
        state.auditId = event.data?.audit_id as string;
        state.task = event.data?.task as string;
        state.agents = event.data?.agents as string[];
      }

      // Handle audit_round event (from new Deep Audit streaming)
      if (event.type === 'audit_round') {
        const round = event.data?.round as number || event.round || 1;
        if (round > maxRound) maxRound = round;

        if (rounds[round]) {
          rounds[round].name = event.data?.name as string;
          rounds[round].cognitiveRole = event.data?.cognitive_role as string;
          rounds[round].durationMs = event.data?.duration_ms as number;
          rounds[round].status = 'complete';

          // Add messages from this round
          const messages = event.data?.messages as Array<{agent: string; content: string; confidence?: number}> || [];
          messages.forEach((msg) => {
            rounds[round].messages.push({
              agent: msg.agent,
              content: msg.content,
              role: 'analyst',
              cognitiveRole: event.data?.cognitive_role as string,
              confidence: msg.confidence,
              citations: 0,
              timestamp: event.timestamp,
            });
          });
        }
      }

      // Handle audit_finding event
      if (event.type === 'audit_finding') {
        state.findings.push({
          category: event.data?.category as 'unanimous' | 'split' | 'risk' | 'insight',
          summary: event.data?.summary as string || '',
          details: event.data?.details as string || '',
          agents_agree: event.data?.agents_agree as string[] || [],
          agents_disagree: event.data?.agents_disagree as string[] || [],
          confidence: event.data?.confidence as number || 0,
          citations: [],
          severity: event.data?.severity as number || 0,
        });
      }

      // Handle audit_cross_exam event
      if (event.type === 'audit_cross_exam') {
        state.crossExamNotes = event.data?.notes as string;
      }

      // Handle audit_verdict event
      if (event.type === 'audit_verdict') {
        state.verdict = {
          recommendation: event.data?.recommendation as string || '',
          confidence: event.data?.confidence as number || 0,
          unanimousIssues: event.data?.unanimous_issues as string[] || [],
          splitOpinions: event.data?.split_opinions as string[] || [],
          riskAreas: event.data?.risk_areas as string[] || [],
        };
      }

      // Also handle legacy agent_message events for backwards compatibility
      if (event.type === 'agent_message' && event.agent) {
        const round = event.round || 1;
        if (round > maxRound) maxRound = round;

        if (rounds[round]) {
          rounds[round].messages.push({
            agent: event.agent,
            content: event.data?.content as string || '',
            role: event.data?.role as string || 'proposer',
            cognitiveRole: event.data?.cognitive_role as string,
            confidence: event.data?.confidence as number,
            citations: (event.data?.citations as unknown[])?.length,
            timestamp: event.timestamp,
          });
        }
      }
    });

    // Update statuses based on maxRound
    AUDIT_ROUNDS.forEach((r) => {
      if (rounds[r.round].status !== 'complete') {
        if (r.round < maxRound) {
          rounds[r.round].status = 'complete';
        } else if (r.round === maxRound && rounds[r.round].messages.length > 0) {
          rounds[r.round].status = 'active';
        }
      }
    });

    return { roundData: Object.values(rounds), auditState: state };
  }, [events]);

  const completedRounds = roundData.filter((r) => r.status === 'complete').length;
  const activeRound = roundData.find((r) => r.status === 'active');

  if (!isActive) {
    return (
      <button
        onClick={onToggle}
        className="px-3 py-1.5 text-sm bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded hover:bg-purple-500/30 flex items-center gap-2"
      >
        <span>🔬</span>
        <span>Deep Audit Mode</span>
      </button>
    );
  }

  return (
    <div className="bg-gradient-to-br from-purple-500/5 to-indigo-500/5 border border-purple-500/30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-purple-500/10 px-4 py-3 border-b border-purple-500/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔬</span>
          <div>
            <h3 className="text-sm font-semibold text-purple-400">Deep Audit Mode</h3>
            <p className="text-xs text-text-muted">
              {completedRounds}/6 rounds complete
            </p>
          </div>
        </div>
        <button
          onClick={onToggle}
          className="px-2 py-1 text-xs bg-surface border border-border rounded hover:bg-surface-hover"
        >
          Exit
        </button>
      </div>

      {/* Round Timeline */}
      <div className="p-4">
        <div className="space-y-2">
          {AUDIT_ROUNDS.map((auditRound) => {
            const data = roundData.find((r) => r.round === auditRound.round);
            const isExpanded = expandedRound === auditRound.round;
            const status = data?.status || 'pending';

            const statusConfig = {
              pending: { bg: 'bg-surface', border: 'border-border', text: 'text-text-muted' },
              active: { bg: 'bg-accent/10', border: 'border-accent', text: 'text-accent' },
              complete: { bg: 'bg-success/10', border: 'border-success/50', text: 'text-success' },
            };

            const config = statusConfig[status];

            return (
              <div
                key={auditRound.round}
                className={`rounded-lg border transition-all ${config.bg} ${config.border}`}
              >
                <button
                  onClick={() => setExpandedRound(isExpanded ? null : auditRound.round)}
                  className="w-full p-3 text-left"
                  disabled={status === 'pending'}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{auditRound.icon}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-medium ${config.text}`}>
                            Round {auditRound.round}: {auditRound.name}
                          </span>
                          {status === 'active' && (
                            <span className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                          )}
                          {status === 'complete' && (
                            <span className="text-success text-xs">✓</span>
                          )}
                        </div>
                        <p className="text-xs text-text-muted">{auditRound.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {data && data.messages.length > 0 && (
                        <span className="text-xs text-text-muted">
                          {data.messages.length} response{data.messages.length !== 1 ? 's' : ''}
                        </span>
                      )}
                      {status !== 'pending' && (
                        <span className="text-text-muted text-xs">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      )}
                    </div>
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && data && data.messages.length > 0 && (
                  <div className="px-3 pb-3 space-y-2">
                    {data.messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-bg rounded border border-border"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-text">{msg.agent}</span>
                            <RoleBadge role={msg.role} cognitiveRole={msg.cognitiveRole} size="sm" />
                          </div>
                          <div className="flex items-center gap-2">
                            {msg.confidence !== undefined && (
                              <span className={`text-xs font-mono ${
                                msg.confidence >= 0.8 ? 'text-green-400' :
                                msg.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                              }`}>
                                {Math.round(msg.confidence * 100)}%
                              </span>
                            )}
                            {msg.citations !== undefined && msg.citations > 0 && (
                              <CitationBadge count={msg.citations} />
                            )}
                          </div>
                        </div>
                        <p className="agent-output text-text-muted whitespace-pre-wrap break-words max-h-32 overflow-y-auto">
                          {msg.content.slice(0, 500)}
                          {msg.content.length > 500 && '...'}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Round Summary */}
      {activeRound && (
        <div className="px-4 pb-4">
          <div className="p-3 bg-accent/10 border border-accent/30 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 bg-accent rounded-full animate-pulse" />
              <span className="text-sm font-medium text-accent">
                Currently: {AUDIT_ROUNDS.find((r) => r.round === activeRound.round)?.name}
              </span>
            </div>
            <p className="text-xs text-text-muted">
              {activeRound.messages.length} agents have responded in this round
            </p>
          </div>
        </div>
      )}

      {/* Findings Section */}
      {auditState.findings.length > 0 && (
        <div className="px-4 pb-4">
          <button
            onClick={() => setShowFindings(!showFindings)}
            className="w-full p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-left"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">📋</span>
                <span className="text-sm font-medium text-amber-400">
                  {auditState.findings.length} Finding{auditState.findings.length !== 1 ? 's' : ''} Detected
                </span>
              </div>
              <span className="text-text-muted text-xs">{showFindings ? '▼' : '▶'}</span>
            </div>
          </button>

          {showFindings && (
            <div className="mt-2 space-y-2">
              {auditState.findings.map((finding, idx) => {
                const categoryConfig = {
                  unanimous: { icon: '✅', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
                  split: { icon: '⚖️', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
                  risk: { icon: '⚠️', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
                  insight: { icon: '💡', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
                };
                const config = categoryConfig[finding.category] || categoryConfig.insight;

                return (
                  <div key={idx} className={`p-3 rounded ${config.bg} border ${config.border}`}>
                    <div className="flex items-start gap-2">
                      <span>{config.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-sm font-medium ${config.color}`}>
                            {finding.category.charAt(0).toUpperCase() + finding.category.slice(1)}
                          </span>
                          {finding.severity > 0 && (
                            <span className={`text-xs font-mono ${
                              finding.severity >= 0.7 ? 'text-red-400' :
                              finding.severity >= 0.4 ? 'text-yellow-400' : 'text-green-400'
                            }`}>
                              Severity: {Math.round(finding.severity * 100)}%
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-text">{finding.summary}</p>
                        {finding.details && (
                          <p className="text-xs text-text-muted mt-1">{finding.details.slice(0, 200)}...</p>
                        )}
                        <div className="flex gap-4 mt-2 text-xs">
                          {finding.agents_agree.length > 0 && (
                            <span className="text-green-400">
                              Agree: {finding.agents_agree.join(', ')}
                            </span>
                          )}
                          {finding.agents_disagree.length > 0 && (
                            <span className="text-red-400">
                              Disagree: {finding.agents_disagree.join(', ')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Verdict Section */}
      {auditState.verdict && (
        <div className="px-4 pb-4">
          <div className="p-4 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 border border-purple-500/40 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🎯</span>
              <span className="text-sm font-semibold text-purple-400">Final Audit Verdict</span>
              <span className={`ml-auto text-xs font-mono px-2 py-0.5 rounded ${
                auditState.verdict.confidence >= 0.8 ? 'bg-green-500/20 text-green-400' :
                auditState.verdict.confidence >= 0.6 ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {Math.round(auditState.verdict.confidence * 100)}% confidence
              </span>
            </div>

            <p className="text-sm text-text mb-4">{auditState.verdict.recommendation}</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              {auditState.verdict.unanimousIssues.length > 0 && (
                <div className="p-2 bg-green-500/10 border border-green-500/20 rounded">
                  <div className="text-green-400 font-medium mb-1">Unanimous Issues ({auditState.verdict.unanimousIssues.length})</div>
                  <ul className="text-text-muted space-y-0.5">
                    {auditState.verdict.unanimousIssues.slice(0, 3).map((issue, idx) => (
                      <li key={idx}>• {issue.slice(0, 50)}...</li>
                    ))}
                  </ul>
                </div>
              )}

              {auditState.verdict.splitOpinions.length > 0 && (
                <div className="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded">
                  <div className="text-yellow-400 font-medium mb-1">Split Opinions ({auditState.verdict.splitOpinions.length})</div>
                  <ul className="text-text-muted space-y-0.5">
                    {auditState.verdict.splitOpinions.slice(0, 3).map((opinion, idx) => (
                      <li key={idx}>• {opinion.slice(0, 50)}...</li>
                    ))}
                  </ul>
                </div>
              )}

              {auditState.verdict.riskAreas.length > 0 && (
                <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
                  <div className="text-red-400 font-medium mb-1">Risk Areas ({auditState.verdict.riskAreas.length})</div>
                  <ul className="text-text-muted space-y-0.5">
                    {auditState.verdict.riskAreas.slice(0, 3).map((risk, idx) => (
                      <li key={idx}>• {risk.slice(0, 50)}...</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cross-Examination Notes */}
      {auditState.crossExamNotes && (
        <div className="px-4 pb-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span>🔍</span>
              <span className="text-sm font-medium text-indigo-400">Cross-Examination Notes</span>
            </div>
            <p className="text-xs text-text-muted whitespace-pre-wrap">
              {auditState.crossExamNotes.slice(0, 500)}
              {auditState.crossExamNotes.length > 500 && '...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Toggle button component
export function DeepAuditToggle({ isActive, onToggle }: { isActive: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className={`px-3 py-1.5 text-sm rounded flex items-center gap-2 transition-colors ${
        isActive
          ? 'bg-purple-500 text-white'
          : 'bg-purple-500/20 text-purple-400 border border-purple-500/30 hover:bg-purple-500/30'
      }`}
    >
      <span>🔬</span>
      <span>{isActive ? 'Deep Audit Active' : 'Deep Audit'}</span>
    </button>
  );
}
