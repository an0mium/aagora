'use client';

import { useState, useCallback } from 'react';

interface DebateInputProps {
  apiBase: string;
  onDebateStarted?: (debateId: string, question: string) => void;
  onError?: (error: string) => void;
}

export function DebateInput({ apiBase, onDebateStarted, onError }: DebateInputProps) {
  const [question, setQuestion] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [agents, setAgents] = useState('claude,openai');
  const [rounds, setRounds] = useState(3);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isSubmitting) return;

    setIsSubmitting(true);

    try {
      const response = await fetch(`${apiBase}/api/debate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          agents,
          rounds,
        }),
      });

      const data = await response.json();

      if (data.success && data.debate_id) {
        onDebateStarted?.(data.debate_id, trimmedQuestion);
        setQuestion('');
      } else {
        onError?.(data.error || 'Failed to start debate');
      }
    } catch (err) {
      onError?.(err instanceof Error ? err.message : 'Network error');
    } finally {
      setIsSubmitting(false);
    }
  }, [question, agents, rounds, apiBase, isSubmitting, onDebateStarted, onError]);

  const placeholders = [
    'What are the tradeoffs between microservices and monoliths?',
    'Should we use TypeScript or JavaScript for this project?',
    'How should we implement rate limiting?',
    'What authentication strategy should we use?',
    'Is GraphQL or REST better for our API?',
  ];

  const [placeholder] = useState(() =>
    placeholders[Math.floor(Math.random() * placeholders.length)]
  );

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Input */}
        <div className="relative">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={placeholder}
            disabled={isSubmitting}
            rows={3}
            className="w-full bg-bg border-2 border-acid-green/50 focus:border-acid-green
                       px-4 py-3 font-mono text-lg text-text placeholder-text-muted/50
                       resize-none transition-colors focus:outline-none
                       disabled:opacity-50 disabled:cursor-not-allowed"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                handleSubmit(e);
              }
            }}
          />
          <div className="absolute bottom-2 right-2 text-xs text-text-muted font-mono">
            {question.length > 0 && `${question.length} chars`}
            {question.length === 0 && 'Cmd+Enter to submit'}
          </div>
        </div>

        {/* Advanced Options Toggle */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs font-mono text-acid-cyan hover:text-acid-green transition-colors"
          >
            {showAdvanced ? '[-] Hide options' : '[+] Show options'}
          </button>

          <button
            type="submit"
            disabled={!question.trim() || isSubmitting}
            className="px-6 py-2 bg-acid-green text-bg font-mono font-bold
                       hover:bg-acid-green/80 transition-colors
                       disabled:bg-text-muted disabled:cursor-not-allowed
                       flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <span className="animate-pulse">STARTING...</span>
              </>
            ) : (
              <>
                <span>[&gt;]</span>
                <span>START DEBATE</span>
              </>
            )}
          </button>
        </div>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="border border-acid-green/30 p-4 space-y-4 bg-surface/50">
            <div className="grid grid-cols-2 gap-4">
              {/* Agents */}
              <div>
                <label className="block text-xs font-mono text-text-muted mb-1">
                  AGENTS (comma-separated)
                </label>
                <input
                  type="text"
                  value={agents}
                  onChange={(e) => setAgents(e.target.value)}
                  className="w-full bg-bg border border-acid-green/30 px-3 py-2
                             font-mono text-sm text-text focus:border-acid-green
                             focus:outline-none"
                  placeholder="claude,openai"
                />
                <p className="text-[10px] text-text-muted mt-1">
                  Available: claude, openai, gemini, codex
                </p>
              </div>

              {/* Rounds */}
              <div>
                <label className="block text-xs font-mono text-text-muted mb-1">
                  DEBATE ROUNDS
                </label>
                <select
                  value={rounds}
                  onChange={(e) => setRounds(parseInt(e.target.value))}
                  className="w-full bg-bg border border-acid-green/30 px-3 py-2
                             font-mono text-sm text-text focus:border-acid-green
                             focus:outline-none"
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n} round{n !== 1 ? 's' : ''}
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-text-muted mt-1">
                  More rounds = deeper analysis
                </p>
              </div>
            </div>
          </div>
        )}
      </form>

      {/* Hint */}
      <p className="mt-4 text-center text-xs font-mono text-text-muted/60">
        AI agents will debate your question and reach a consensus
      </p>
    </div>
  );
}
