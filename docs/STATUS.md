# Aragora Project Status

*Last updated: January 4, 2026*

## Current State

### Nomic Loop
- **Cycle**: 1
- **Phase**: Implement
- **Progress**: 6/9 tasks completed (67%)
- **Feature**: Flip Detection (position reversal tracking)

### Pending Tasks
1. `task-7`: Add tests for /api/insights/flips endpoint
2. `task-8`: Implement 'Flips' tab in InsightsPanel UI
3. `task-9`: Add frontend tests for Flips tab

## Feature Integration Status

### Fully Integrated (6)
| Feature | Status | Location |
|---------|--------|----------|
| FlipDetector | Active | `aragora/insights/flip_detector.py` |
| ELO Rankings | Active | `aragora/ranking/elo.py` |
| Insight Extraction | Active | `aragora/insights/extractor.py` |
| Citation Tracking | Active | `aragora/reasoning/citations.py` |
| Convergence Detection | Active | `aragora/debate/convergence.py` |
| Audience Participation | Active | `aragora/audience/suggestions.py` |

### Implemented but Underutilized (4)
| Feature | Issue | Quick Fix |
|---------|-------|-----------|
| Persona System | Not injected into prompts | Add persona context to `_build_proposal_prompt()` |
| Historical Memory | Never initialized | Initialize `debate_embeddings` in API handlers |
| Relationship Tracking | Not exposed in API/UI | Add `/api/agent/{name}/relationships` endpoint |
| Role Rotation | Now enabled by default | *(Fixed in commit 272c347)* |

### Missing UI/API (2)
| Feature | Issue |
|---------|-------|
| Audience Inbox | No dedicated UI component for browsing suggestions |
| Research Phase | `enable_research` defaults to False |

## Recent Improvements

### Commit 272c347 (2026-01-04)
- Enabled cognitive role rotation by default for diverse perspectives
- Added `ALLOWED_AGENT_TYPES` allowlist for security
- Fixed test signature mismatch in auth tests

### Security Enhancements
- Agent type validation prevents arbitrary agent injection
- Prompt injection filtering in audience suggestions
- Safe integer parsing with bounds checking

## Recommendations

### High Priority
1. **Complete Flip Detection** - 3 tasks remaining, unblocks personas
2. **Add Persona Context** - Inject persona into debate prompts for agent specialization
3. **Initialize Historical Memory** - Enable learning from past debates by default

### Medium Priority
1. Create Audience Inbox Panel - Display clustered suggestions with voting
2. Add agent consistency metrics to leaderboard
3. Track verification failures for design feedback loop

### Nomic Loop Improvements
1. **Verification Feedback**: Store failure patterns to inform next design phase
2. **Dissent Tracking**: Weight agents by historical dissent accuracy
3. **Staged Rollout**: For low-consensus designs, commit to branch first
4. **Test Coverage Gates**: Require minimum coverage for new code

## Architecture Notes

The codebase is well-structured with optional features using lazy loading:
- Optional parameters prevent circular imports
- Feature flags in `DebateProtocol` enable/disable features cleanly
- Server gracefully handles missing databases

Key insight: Many powerful features are "sleeping" - implemented but not activated. Enabling opt-in features by default would immediately increase system capability.
