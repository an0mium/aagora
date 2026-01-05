# Aragora Quick Start Guide

Get your first multi-agent debate running in 5 minutes.

## 1. Install

```bash
git clone https://github.com/an0mium/aragora.git
cd aragora
pip install -e .
```

## 2. Set API Key

You need at least one AI provider key. Create a `.env` file:

```bash
cp .env.example .env
```

Add your key:

```bash
# Pick one (or more):
ANTHROPIC_API_KEY=sk-ant-xxx     # Claude
OPENAI_API_KEY=sk-xxx            # GPT-4
GEMINI_API_KEY=AIzaSy...         # Gemini
XAI_API_KEY=xai-xxx              # Grok
```

## 3. Run Your First Debate

```bash
python -m aragora.debate "Should we use microservices or monolith?" \
  --agents anthropic-api openai-api
```

Expected output:
```
DEBATE: Should we use microservices or monolith?
Agents: anthropic-api, openai-api
Round 1/3...
  [anthropic-api] Proposing...
  [openai-api] Critiquing...
...
CONSENSUS REACHED (75% agreement)
Final Answer: [synthesized recommendation]
```

## 4. Explore Results

### View in Terminal
Results are printed directly. For longer debates, pipe to a file:
```bash
python -m aragora.debate "..." --agents ... > debate.log
```

### Start Live Dashboard
```bash
python -m aragora.server
# Open http://localhost:8080
```

### View Recorded Replays
```bash
ls .nomic/replays/
python -m aragora.replay view <debate-id>
```

## Common Options

```bash
# More agents
--agents anthropic-api openai-api gemini-api grok

# More rounds (deeper debate)
--rounds 5

# Different consensus
--consensus majority   # Default: 60% agreement
--consensus unanimous  # All agents agree
--consensus judge      # One agent decides

# Add web research
--research

# Verbose output
--verbose
```

## Example Debates

```bash
# Technical architecture
python -m aragora.debate "Design a caching strategy for 10M users" \
  --agents anthropic-api openai-api gemini-api --rounds 4

# Code review
python -m aragora.debate "Review this code for security issues: $(cat myfile.py)" \
  --agents anthropic-api openai-api --consensus unanimous

# Decision making
python -m aragora.debate "React vs Vue vs Svelte for our new project" \
  --agents anthropic-api openai-api gemini-api grok --research
```

## Next Steps

- **Run the Nomic Loop:** Self-improving debates - see `docs/NOMIC_LOOP.md`
- **API Integration:** Build on Aragora - see `docs/API_REFERENCE.md`
- **Configuration:** All options - see `docs/ENVIRONMENT.md`
- **Architecture:** How it works - see `docs/ARCHITECTURE.md`

## Troubleshooting

### "No API key found"
Set at least one key in `.env` or environment:
```bash
export ANTHROPIC_API_KEY=your-key
```

### "Agent timed out"
Increase timeout:
```bash
--timeout 120  # 2 minutes per agent response
```

### "Rate limit exceeded"
Wait a moment or use fewer agents. API providers have rate limits.

### "Connection refused on port 8080"
Another service is using that port. Use a different port:
```bash
python -m aragora.server --port 8081
```
