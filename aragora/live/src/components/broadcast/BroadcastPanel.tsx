'use client';

import { useEffect, useCallback } from 'react';
import { useBroadcast } from '@/hooks/useBroadcast';
import { AudioPlayer } from './AudioPlayer';
import { PublishDropdown } from './PublishDropdown';
import type { BroadcastPanelProps } from './types';

/**
 * Panel for generating audio broadcasts and publishing to social media
 *
 * Displays:
 * - Generate Audio button (when no audio exists)
 * - Audio player (when audio exists)
 * - Publish dropdown (when audio exists)
 */
export function BroadcastPanel({ debateId, debateTitle }: BroadcastPanelProps) {
  const { hasAudio, audioUrl, isGenerating, error, checkAudioExists, generateBroadcast } =
    useBroadcast(debateId);

  // Check if audio already exists on mount
  useEffect(() => {
    checkAudioExists();
  }, [checkAudioExists]);

  const handleGenerate = useCallback(async () => {
    try {
      await generateBroadcast();
    } catch {
      // Error is already captured in state
    }
  }, [generateBroadcast]);

  return (
    <div className="border border-accent/30 bg-surface/50 mt-6">
      <div className="px-4 py-3 border-b border-accent/20 bg-bg/50 flex items-center justify-between">
        <span className="text-xs font-mono text-accent uppercase tracking-wider">
          {'>'} BROADCAST
        </span>
        {hasAudio && <PublishDropdown debateId={debateId} title={debateTitle} />}
      </div>

      <div className="p-4 space-y-4">
        {!hasAudio && !isGenerating && (
          <div className="space-y-3">
            <p className="text-xs font-mono text-text-muted">
              Generate an audio version of this debate using text-to-speech.
            </p>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full px-3 py-2 text-xs font-mono border border-accent/40 hover:bg-accent/10 disabled:opacity-50 transition-colors"
            >
              [GENERATE AUDIO]
            </button>
          </div>
        )}

        {isGenerating && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-acid-green/40 border-t-acid-green rounded-full animate-spin" />
            <span className="text-xs font-mono text-acid-green animate-pulse">
              GENERATING AUDIO...
            </span>
          </div>
        )}

        {error && (
          <div className="p-3 text-xs font-mono text-warning bg-warning/10 border border-warning/30">
            {'>'} ERROR: {error}
          </div>
        )}

        {hasAudio && audioUrl && (
          <div className="space-y-3">
            <AudioPlayer url={audioUrl} />
          </div>
        )}
      </div>
    </div>
  );
}
