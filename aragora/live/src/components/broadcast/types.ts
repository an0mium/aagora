export interface BroadcastStatus {
  hasAudio: boolean;
  audioUrl: string | null;
  isGenerating: boolean;
  error: string | null;
}

export interface BroadcastResult {
  broadcast_id: string;
  audio_url: string;
  status: 'generating' | 'complete' | 'error';
  duration_seconds?: number;
}

export interface PublishResult {
  success: boolean;
  url?: string;
  error?: string;
}

export interface BroadcastPanelProps {
  debateId: string;
  debateTitle?: string;
}

export interface AudioPlayerProps {
  url: string;
}

export interface PublishDropdownProps {
  debateId: string;
  title?: string;
}
