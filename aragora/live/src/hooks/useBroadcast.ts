'use client';

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.aragora.ai';

interface BroadcastStatus {
  hasAudio: boolean;
  audioUrl: string | null;
  isGenerating: boolean;
  error: string | null;
}

interface BroadcastResult {
  broadcast_id: string;
  audio_url: string;
  status: 'generating' | 'complete' | 'error';
  duration_seconds?: number;
}

interface PublishResult {
  success: boolean;
  url?: string;
  error?: string;
}

/**
 * Hook for managing broadcast generation and social publishing
 *
 * @example
 * const { hasAudio, generateBroadcast, publishToTwitter } = useBroadcast(debateId);
 */
export function useBroadcast(debateId: string) {
  const [status, setStatus] = useState<BroadcastStatus>({
    hasAudio: false,
    audioUrl: null,
    isGenerating: false,
    error: null,
  });

  const checkAudioExists = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/audio/${debateId}.mp3`, {
        method: 'HEAD',
      });
      if (response.ok) {
        setStatus((s) => ({
          ...s,
          hasAudio: true,
          audioUrl: `${API_BASE}/audio/${debateId}.mp3`,
        }));
        return true;
      }
      return false;
    } catch {
      // Audio doesn't exist yet
      return false;
    }
  }, [debateId]);

  const generateBroadcast = useCallback(async (): Promise<BroadcastResult> => {
    setStatus((s) => ({ ...s, isGenerating: true, error: null }));
    try {
      const response = await fetch(`${API_BASE}/api/debates/${debateId}/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format: 'mp3' }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const result: BroadcastResult = await response.json();
      setStatus({
        hasAudio: true,
        audioUrl: result.audio_url || `${API_BASE}/audio/${debateId}.mp3`,
        isGenerating: false,
        error: null,
      });
      return result;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to generate broadcast';
      setStatus((s) => ({
        ...s,
        isGenerating: false,
        error: errorMessage,
      }));
      throw e;
    }
  }, [debateId]);

  const publishToTwitter = useCallback(
    async (text: string): Promise<PublishResult> => {
      const response = await fetch(`${API_BASE}/api/debates/${debateId}/publish/twitter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, debate_id: debateId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { success: false, error: errorData.error || `HTTP ${response.status}` };
      }

      return response.json();
    },
    [debateId]
  );

  const publishToYouTube = useCallback(
    async (title: string, description: string): Promise<PublishResult> => {
      const response = await fetch(`${API_BASE}/api/debates/${debateId}/publish/youtube`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, debate_id: debateId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { success: false, error: errorData.error || `HTTP ${response.status}` };
      }

      return response.json();
    },
    [debateId]
  );

  return {
    ...status,
    checkAudioExists,
    generateBroadcast,
    publishToTwitter,
    publishToYouTube,
  };
}
