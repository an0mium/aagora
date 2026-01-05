/**
 * Tests for DebateViewer component
 *
 * Tests cover:
 * - WebSocket connection lifecycle
 * - Message rendering and scrolling
 * - Phase transitions
 * - User participation integration
 * - Error handling
 *
 * Note: The DebateViewer uses WebSocket only for debate IDs starting with 'adhoc_'.
 * For other IDs, it fetches from Supabase.
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { DebateViewer } from '../src/components/DebateViewer';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

// Mock Supabase fetch
jest.mock('../src/utils/supabase', () => ({
  fetchDebateById: jest.fn(),
}));

// Mock scrollIntoView (not available in jsdom)
Element.prototype.scrollIntoView = jest.fn();

// Mock WebSocket with synchronous connection for test reliability
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Error) => void) | null = null;
  private connectionTimeout: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url;
    // Store timeout so it can be controlled in tests
    this.connectionTimeout = setTimeout(() => {
      if (this.readyState === MockWebSocket.CONNECTING) {
        this.readyState = MockWebSocket.OPEN;
        if (this.onopen) this.onopen();
      }
    }, 0);
  }

  send = jest.fn();
  close = jest.fn(() => {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose();
  });

  // Helper to simulate incoming messages
  simulateMessage(data: object) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  // Helper to manually open connection (for test control)
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) this.onopen();
  }
}

let mockWsInstance: MockWebSocket | null = null;

// @ts-expect-error - mocking global WebSocket
global.WebSocket = jest.fn((url: string) => {
  mockWsInstance = new MockWebSocket(url);
  return mockWsInstance;
});

describe('DebateViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockWsInstance = null;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // Use adhoc_ prefix to enable WebSocket mode
  const LIVE_DEBATE_ID = 'adhoc_test-123';

  it('renders connecting state initially for live debates', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
    });
    expect(screen.getByText(/Connecting/i)).toBeInTheDocument();
  });

  it('establishes WebSocket connection with correct URL', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
    });

    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost:3001')
    );
  });

  it('displays connection status when connected', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
    });

    // Flush the setTimeout(0) in MockWebSocket constructor
    await act(async () => {
      jest.runAllTimers();
    });

    expect(mockWsInstance?.readyState).toBe(MockWebSocket.OPEN);
    // After connection opens, should show LIVE DEBATE state
    expect(screen.getByText(/LIVE DEBATE/i)).toBeInTheDocument();
  });

  it('renders agent messages from WebSocket', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    await act(async () => {
      mockWsInstance?.simulateMessage({
        type: 'agent_message',
        data: {
          agent: 'claude-3-opus',
          role: 'proposer',
          content: 'I propose we implement feature X because it would improve user experience.',
        },
        timestamp: Date.now(),
        round: 1,
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/I propose we implement feature X/)).toBeInTheDocument();
    });
  });

  it('handles debate_start events', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    await act(async () => {
      mockWsInstance?.simulateMessage({
        type: 'debate_start',
        data: {
          task: 'Discuss the best approach for feature X',
          agents: ['claude-3-opus', 'gemini-2.0-flash'],
        },
        timestamp: Date.now(),
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/Discuss the best approach for feature X/)).toBeInTheDocument();
    });
    expect(screen.getByText('claude-3-opus')).toBeInTheDocument();
    expect(screen.getByText('gemini-2.0-flash')).toBeInTheDocument();
  });

  it('displays agent names when messages arrive', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    await act(async () => {
      mockWsInstance?.simulateMessage({
        type: 'agent_message',
        data: {
          agent: 'claude-3-opus',
          role: 'proposer',
          content: 'Test message',
        },
        timestamp: Date.now(),
        round: 1,
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/CLAUDE-3-OPUS/)).toBeInTheDocument();
    });
  });

  it('auto-scrolls to new messages', async () => {
    const scrollIntoViewMock = jest.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock;

    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    await act(async () => {
      mockWsInstance?.simulateMessage({
        type: 'agent_message',
        data: {
          agent: 'claude-3-opus',
          content: 'New message that should trigger scroll',
        },
        timestamp: Date.now(),
      });
    });

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });

  it('cleans up WebSocket on unmount', async () => {
    let unmount: () => void;
    await act(async () => {
      const result = render(
        <DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />
      );
      unmount = result.unmount;
      jest.runAllTimers();
    });

    expect(mockWsInstance?.readyState).toBe(MockWebSocket.OPEN);

    await act(async () => {
      unmount();
    });

    expect(mockWsInstance?.close).toHaveBeenCalled();
  });

  it('sends subscription message on connection', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    expect(mockWsInstance?.send).toHaveBeenCalledWith(
      expect.stringContaining('subscribe')
    );
  });

  it('displays debate ID correctly', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
      jest.runAllTimers();
    });

    // Debate ID should be visible somewhere in the UI
    expect(screen.getByText(new RegExp(LIVE_DEBATE_ID, 'i'))).toBeInTheDocument();
  });
});

describe('DebateViewer error states', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockWsInstance = null;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const LIVE_DEBATE_ID = 'adhoc_error-test';

  it('shows error message on WebSocket failure', async () => {
    await act(async () => {
      render(<DebateViewer debateId={LIVE_DEBATE_ID} wsUrl="ws://localhost:3001" />);
    });

    // Simulate WebSocket error
    await act(async () => {
      if (mockWsInstance?.onerror) {
        mockWsInstance.onerror(new Error('Connection refused'));
      }
      if (mockWsInstance) {
        mockWsInstance.readyState = MockWebSocket.CLOSED;
        if (mockWsInstance.onclose) mockWsInstance.onclose();
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/CONNECTION ERROR/i)).toBeInTheDocument();
    });
  });
});

describe('DebateViewer archived debates', () => {
  const { fetchDebateById } = jest.requireMock('../src/utils/supabase');

  beforeEach(() => {
    jest.clearAllMocks();
    mockWsInstance = null;
  });

  it('fetches debate from Supabase for non-live debates', async () => {
    const mockDebate = {
      id: 'archived-debate-123',
      loop_id: 'loop-1',
      cycle_number: 1,
      task: 'Archived debate task',
      agents: ['agent-1', 'agent-2'],
      transcript: [
        { agent: 'agent-1', content: 'First message', role: 'proposer' },
      ],
      phase: 'complete',
      consensus_reached: true,
      confidence: 0.85,
      winning_proposal: 'The winning proposal',
      vote_tally: { 'agent-1': 2, 'agent-2': 1 },
      created_at: '2024-01-15T10:00:00Z',
    };

    fetchDebateById.mockResolvedValue(mockDebate);

    await act(async () => {
      render(<DebateViewer debateId="archived-debate-123" wsUrl="ws://localhost:3001" />);
    });

    // WebSocket should NOT be called for non-adhoc debates
    expect(global.WebSocket).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByText('Archived debate task')).toBeInTheDocument();
    });
  });

  it('shows error for non-existent archived debate', async () => {
    fetchDebateById.mockResolvedValue(null);

    await act(async () => {
      render(<DebateViewer debateId="non-existent" wsUrl="ws://localhost:3001" />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Debate not found/i)).toBeInTheDocument();
    });
  });
});
