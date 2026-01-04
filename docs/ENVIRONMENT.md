# Environment Variable Reference

Complete reference for all environment variables used by Aragora.

## Quick Start

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

## AI Provider Keys

At least one AI provider key is required.

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | One required | Anthropic Claude API key | - |
| `OPENAI_API_KEY` | One required | OpenAI API key | - |
| `GEMINI_API_KEY` | Optional | Google Gemini API key | - |
| `XAI_API_KEY` | Optional | Grok/XAI API key | - |
| `GROK_API_KEY` | Optional | Alias for XAI_API_KEY | - |
| `OPENROUTER_API_KEY` | Optional | OpenRouter for multi-model access | - |
| `DEEPSEEK_API_KEY` | Optional | DeepSeek API key | - |

**Note:** Never commit your `.env` file. It's gitignored for security.

## Persistence (Supabase)

Optional but recommended for production.

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SUPABASE_URL` | Optional | Supabase project URL | - |
| `SUPABASE_KEY` | Optional | Supabase service key | - |

Enables:
- Historical debate storage
- Cross-session learning
- Live dashboard at live.aragora.ai

## Server Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `API_PORT` | Optional | HTTP server port | `8080` |
| `API_HOST` | Optional | Bind address | `0.0.0.0` |
| `ARAGORA_API_TOKEN` | Optional | Enable token auth | Disabled |
| `ARAGORA_TOKEN_TTL` | Optional | Token lifetime (seconds) | `3600` |
| `ARAGORA_WS_MAX_SIZE` | Optional | Max WebSocket message size | `65536` |

## CORS Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ARAGORA_ALLOWED_ORIGINS` | Optional | Comma-separated allowed origins | See below |

Default origins:
```
http://localhost:3000,http://localhost:8080,
http://127.0.0.1:3000,http://127.0.0.1:8080,
https://aragora.ai,https://www.aragora.ai,
https://live.aragora.ai,https://api.aragora.ai
```

Example:
```bash
ARAGORA_ALLOWED_ORIGINS=https://myapp.com,https://staging.myapp.com
```

## Webhook Integration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `WEBHOOK_URL` | Optional | External webhook endpoint | - |
| `WEBHOOK_SECRET` | Optional | HMAC secret for signing | - |
| `ARAGORA_WEBHOOK_QUEUE_SIZE` | Optional | Max queued events | `1000` |

## Rate Limiting

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `RATE_LIMIT_PER_MINUTE` | Optional | Requests per minute per token | `60` |
| `IP_RATE_LIMIT_PER_MINUTE` | Optional | Requests per minute per IP | `120` |

## Embedding Providers

For semantic search and memory retrieval.

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `EMBEDDING_PROVIDER` | Optional | Provider to use | `auto` |
| `OPENAI_EMBEDDING_MODEL` | Optional | OpenAI embedding model | `text-embedding-3-small` |

Supported providers: `openai`, `gemini`, `sentence-transformers`, `auto`

## Formal Verification

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `Z3_TIMEOUT` | Optional | Z3 solver timeout (seconds) | `30` |
| `LEAN_PATH` | Optional | Path to Lean 4 installation | Auto-detect |

## Debug & Logging

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ARAGORA_DEBUG` | Optional | Enable debug logging | `false` |
| `ARAGORA_LOG_LEVEL` | Optional | Log level (DEBUG/INFO/WARN/ERROR) | `INFO` |

## Validation Rules

### API Keys
- Must be non-empty strings
- Validated on first API call
- Keys are not logged (security)

### Ports
- Must be integers 1-65535
- Common ports: 8080 (HTTP), 8765 (legacy WebSocket)

### URLs
- Must be valid HTTPS URLs (for production)
- HTTP allowed for localhost development

## Example .env File

```bash
# Required: At least one AI provider
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Optional: Additional providers
GEMINI_API_KEY=AIzaSy...
XAI_API_KEY=xai-xxx

# Optional: Persistence
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# Optional: Server config
API_PORT=8080
ARAGORA_API_TOKEN=my-secret-token

# Optional: Webhooks
WEBHOOK_URL=https://myserver.com/aragora-events
WEBHOOK_SECRET=hmac-secret
```

## Troubleshooting

### "No API key found"
- Set at least one of: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- Verify `.env` file is in project root

### "CORS blocked"
- Add your domain to `ARAGORA_ALLOWED_ORIGINS`
- Check for typos in origin URLs

### "WebSocket connection failed"
- Verify `API_PORT` matches your client config
- Check firewall/proxy settings

### "Rate limit exceeded"
- Increase `RATE_LIMIT_PER_MINUTE`
- Or wait for rate limit window to reset
