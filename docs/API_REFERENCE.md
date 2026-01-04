# Aragora API Reference

This document describes the HTTP and WebSocket APIs for the Aragora debate platform.

## Server Configuration

The unified server runs on port 8080 by default and serves both HTTP API and static files.

```bash
python -m aragora.server --port 8080 --nomic-dir .nomic
```

## Authentication

API requests may include an `Authorization` header with a bearer token:
```
Authorization: Bearer <token>
```

Rate limiting: 60 requests per minute per token (sliding window).

## HTTP API Endpoints

### Health & Status

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T12:00:00Z"
}
```

#### GET /api/nomic/state
Get current nomic loop state.

**Response:**
```json
{
  "phase": "debate",
  "stage": "executing",
  "cycle": 5,
  "total_tasks": 9,
  "completed_tasks": 3
}
```

#### GET /api/nomic/log
Get recent nomic loop log lines.

**Parameters:**
- `lines` (int, default=100, max=1000): Number of log lines to return

---

### Debates

#### GET /api/debates
List recent debates.

**Parameters:**
- `limit` (int, default=20, max=100): Maximum debates to return

**Response:**
```json
{
  "debates": [
    {
      "id": "debate-123",
      "topic": "Rate limiter implementation",
      "consensus_reached": true,
      "confidence": 0.85,
      "timestamp": "2026-01-04T12:00:00Z"
    }
  ]
}
```

#### GET /api/debates/:slug
Get a specific debate by slug/ID.

---

### History (Supabase)

#### GET /api/history/cycles
Get cycle history.

**Parameters:**
- `loop_id` (string, optional): Filter by loop ID
- `limit` (int, default=50, max=200): Maximum cycles to return

#### GET /api/history/events
Get event history.

**Parameters:**
- `loop_id` (string, optional): Filter by loop ID
- `limit` (int, default=100, max=500): Maximum events to return

#### GET /api/history/debates
Get debate history.

**Parameters:**
- `loop_id` (string, optional): Filter by loop ID
- `limit` (int, default=50, max=200): Maximum debates to return

#### GET /api/history/summary
Get summary statistics.

**Parameters:**
- `loop_id` (string, optional): Filter by loop ID

---

### Leaderboard & ELO

#### GET /api/leaderboard
Get agent rankings by ELO.

**Parameters:**
- `limit` (int, default=20, max=50): Maximum agents to return
- `domain` (string, optional): Filter by domain

**Response:**
```json
{
  "rankings": [
    {
      "agent": "claude",
      "elo": 1523,
      "wins": 45,
      "losses": 12,
      "domain": "general"
    }
  ]
}
```

#### GET /api/matches/recent
Get recent ELO matches.

**Parameters:**
- `limit` (int, default=10, max=50): Maximum matches to return
- `loop_id` (string, optional): Filter by loop ID

#### GET /api/agent/:name/history
Get an agent's match history.

**Parameters:**
- `limit` (int, default=30, max=100): Maximum matches to return

---

### Insights

#### GET /api/insights/recent
Get recent debate insights.

**Parameters:**
- `limit` (int, default=20, max=100): Maximum insights to return

**Response:**
```json
{
  "insights": [
    {
      "type": "pattern",
      "content": "Agents prefer incremental implementations",
      "confidence": 0.78,
      "source_debate": "debate-123"
    }
  ]
}
```

---

### Flip Detection

Position reversal detection API for tracking agent consistency.

#### GET /api/flips/recent
Get recent position flips across all agents.

**Parameters:**
- `limit` (int, default=20, max=100): Maximum flips to return

**Response:**
```json
{
  "flips": [
    {
      "id": "flip-abc123",
      "agent_name": "gemini",
      "original_claim": "X is optimal",
      "new_claim": "Y is optimal",
      "flip_type": "contradiction",
      "similarity_score": 0.82,
      "detected_at": "2026-01-04T12:00:00Z"
    }
  ],
  "count": 15
}
```

#### GET /api/flips/summary
Get aggregate flip statistics.

**Response:**
```json
{
  "total_flips": 42,
  "by_type": {
    "contradiction": 10,
    "refinement": 25,
    "retraction": 5,
    "qualification": 2
  },
  "by_agent": {
    "gemini": 15,
    "claude": 12,
    "codex": 10,
    "grok": 5
  },
  "recent_24h": 8
}
```

#### GET /api/agent/:name/consistency
Get consistency score for an agent.

**Response:**
```json
{
  "agent_name": "claude",
  "total_positions": 150,
  "total_flips": 12,
  "consistency_score": 0.92,
  "contradictions": 2,
  "refinements": 8,
  "retractions": 1,
  "qualifications": 1
}
```

#### GET /api/agent/:name/flips
Get flips for a specific agent.

**Parameters:**
- `limit` (int, default=20, max=100): Maximum flips to return

---

### Replays

#### GET /api/replays
List available debate replays.

**Response:**
```json
{
  "replays": [
    {
      "id": "nomic-cycle-1",
      "name": "Nomic Cycle 1",
      "event_count": 245,
      "created_at": "2026-01-03T10:00:00Z"
    }
  ]
}
```

#### GET /api/replays/:id
Get a specific replay by ID.

---

### Documents

#### GET /api/documents
List uploaded documents.

#### POST /api/documents/upload
Upload a document for processing.

**Headers:**
- `Content-Type: multipart/form-data`
- `X-Filename: document.pdf`

**Supported formats:** PDF, Markdown, Python, JavaScript, TypeScript, Jupyter notebooks

**Max size:** 10MB

---

### Learning Evolution

#### GET /api/learning/evolution
Get learning evolution patterns.

---

## WebSocket API

Connect to the WebSocket server for real-time streaming:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.payload);
};
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `phase_start` | A nomic phase has started |
| `phase_end` | A nomic phase has completed |
| `agent_message` | An agent has sent a message |
| `debate_round` | A debate round has completed |
| `consensus` | Consensus has been reached |
| `elo_update` | ELO ratings have been updated |
| `flip_detected` | A position flip was detected |

### Event Format

```json
{
  "type": "agent_message",
  "timestamp": "2026-01-04T12:00:00Z",
  "loop_id": "loop-abc123",
  "payload": {
    "agent": "claude",
    "role": "critic",
    "content": "I disagree with this approach because..."
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Description of the error"
}
```

Common HTTP status codes:
- `400` - Bad request (invalid parameters)
- `403` - Forbidden (access denied)
- `404` - Not found
- `500` - Internal server error

---

## CORS Policy

The API allows cross-origin requests from:
- `http://localhost:3000`
- `http://localhost:8080`
- `https://aragora.ai`
- `https://www.aragora.ai`

Other origins are blocked by the browser.

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| General API | 60 req/min per token |
| Document upload | 10 req/min |
| WebSocket | Unlimited messages |

---

## Security Notes

1. **Path traversal protection**: All file paths are validated to prevent directory traversal attacks
2. **Input validation**: All integer parameters have bounds checking
3. **Error sanitization**: Internal errors are not exposed to clients
4. **Origin validation**: CORS uses allowlist instead of wildcard
