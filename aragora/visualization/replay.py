"""
Replay Theater: Interactive HTML visualizations for aragora debates.

Generates self-contained HTML files with timelines and verdict cards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import html as html_module
from aragora.core import DebateResult, Message, Vote

# Optional imports for trace support
try:
    from aragora.debate.traces import DebateTrace, EventType
    HAS_TRACE_SUPPORT = True
except ImportError:
    HAS_TRACE_SUPPORT = False
    DebateTrace = None


@dataclass
class ReplayScene:
    """A single scene (round) in the debate replay."""
    round_number: int
    timestamp: datetime
    messages: List[Message] = field(default_factory=list)
    consensus_indicators: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization with HTML escaping."""
        return {
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat(),
            "messages": [
                {
                    "role": html_module.escape(str(getattr(msg, 'role', 'unknown'))),
                    "agent": html_module.escape(str(getattr(msg, 'agent', 'unknown'))),
                    "content": html_module.escape(str(getattr(msg, 'content', ''))),
                    "timestamp": getattr(msg, 'timestamp', datetime.now()).isoformat(),
                    "round": getattr(msg, 'round', 0),
                }
                for msg in self.messages
            ],
            "consensus_indicators": self.consensus_indicators,
        }


@dataclass
class ReplayArtifact:
    """Complete debate data for HTML generation."""
    debate_id: str
    task: str
    scenes: List[ReplayScene] = field(default_factory=list)
    verdict: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for JSON embedding in HTML."""
        return {
            "debate_id": self.debate_id,
            "task": self.task,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "verdict": self.verdict,
            "metadata": self.metadata,
        }


class ReplayGenerator:
    """Generates HTML replay artifacts from debate results."""

    def __init__(self):
        self.html_template = self._get_html_template()

    def generate(self, debate_result: DebateResult, trace: Optional["DebateTrace"] = None) -> str:
        """Generate HTML replay from a DebateResult.

        Args:
            debate_result: The DebateResult from orchestrator
            trace: Optional DebateTrace for accurate consensus markers

        Returns:
            Complete HTML document as string
        """
        artifact = self._create_artifact(debate_result, trace)
        return self._render_html(artifact)

    def _create_artifact(self, debate_result: DebateResult, trace: Optional["DebateTrace"] = None) -> ReplayArtifact:
        """Transform DebateResult into ReplayArtifact."""
        # Group messages by round
        scenes = self._extract_scenes(debate_result.messages, trace)

        # Create verdict card data
        verdict = self._create_verdict_card(debate_result)

        # Metadata
        metadata = {
            "duration_seconds": debate_result.duration_seconds,
            "rounds_used": debate_result.rounds_used,
            "consensus_reached": debate_result.consensus_reached,
            "confidence": debate_result.confidence,
            "convergence_status": debate_result.convergence_status,
            "consensus_strength": debate_result.consensus_strength,
            "generated_at": datetime.now().isoformat(),
        }

        return ReplayArtifact(
            debate_id=debate_result.id,
            task=debate_result.task,
            scenes=scenes,
            verdict=verdict,
            metadata=metadata,
        )

    def _extract_scenes(self, messages: List[Message], trace: Optional["DebateTrace"] = None) -> List[ReplayScene]:
        """Extract scenes (rounds) from messages with consensus indicators."""
        scenes = []
        round_groups = {}

        # Group messages by round
        for msg in messages:
            if msg.round not in round_groups:
                round_groups[msg.round] = []
            round_groups[msg.round].append(msg)

        # Build consensus event map from trace (if available)
        consensus_events = {}
        if trace and HAS_TRACE_SUPPORT:
            for event in trace.events:
                if event.type == EventType.CONSENSUS_CHECK:
                    consensus_events[event.round_num] = event.data

        # Create scenes
        for round_num in sorted(round_groups.keys()):
            msgs = round_groups[round_num]
            # Use timestamp of first message in round
            timestamp = msgs[0].timestamp if msgs else datetime.now()

            # Determine consensus indicator for this scene (default: not reached)
            consensus_indicators = {"reached": False, "source": "default"}
            if round_num in consensus_events:
                # Use actual trace data
                event_data = consensus_events[round_num]
                consensus_indicators = {
                    "reached": event_data.get("reached", False),
                    "confidence": event_data.get("confidence", 0),
                    "source": "trace",
                    "description": event_data.get("description", "Consensus check"),
                }
            elif round_num == max(round_groups.keys()) and getattr(msgs[0], 'role', '') == 'synthesizer':
                # Fallback: mark final round if consensus_reached in debate result
                # This will be overridden by verdict logic, but provides basic indication
                consensus_indicators = {
                    "reached": True,
                    "source": "fallback",
                    "description": "Final round (potential consensus)",
                }

            scene = ReplayScene(
                round_number=round_num,
                timestamp=timestamp,
                messages=msgs,
                consensus_indicators=consensus_indicators,
            )
            scenes.append(scene)

        return scenes

    def _create_verdict_card(self, debate_result: DebateResult) -> Dict[str, Any]:
        """Create verdict card data from debate result with proper tie handling."""
        votes = getattr(debate_result, 'votes', []) or []
        consensus = getattr(debate_result, 'consensus_reached', False)

        # Build vote breakdown
        vote_counts: Dict[str, List[Vote]] = {}
        for v in votes:
            choice = str(v.choice)
            vote_counts.setdefault(choice, []).append(v)

        vote_breakdown = []
        for choice, choice_votes in vote_counts.items():
            avg_conf = sum(v.confidence for v in choice_votes) / len(choice_votes)
            vote_breakdown.append({
                "choice": choice,
                "count": len(choice_votes),
                "avg_confidence": round(avg_conf, 2),
            })

        # Determine winner with tie handling
        winner_label = "No winner"
        winner = None

        if consensus and vote_breakdown:
            # Sort by count descending
            sorted_votes = sorted(vote_breakdown, key=lambda x: x["count"], reverse=True)

            if len(sorted_votes) >= 2 and sorted_votes[0]["count"] == sorted_votes[1]["count"]:
                winner_label = "Tie"
            else:
                winner = sorted_votes[0]["choice"]
                winner_label = winner

        # Build evidence list (HTML-escaped for security)
        evidence = []
        if debate_result.winning_patterns:
            evidence.extend([html_module.escape(str(p)) for p in debate_result.winning_patterns])
        if debate_result.critiques:
            # Add key critique insights (limited and escaped)
            for critique in debate_result.critiques[:3]:  # Top 3
                evidence.append(html_module.escape(f"Critique from {critique.agent}: {critique.reasoning[:100]}..."))

        return {
            "final_answer": html_module.escape(str(getattr(debate_result, 'final_answer', '') or '')),
            "confidence": getattr(debate_result, 'confidence', 0),
            "consensus_reached": consensus,
            "winner": winner,
            "winner_label": winner_label,
            "evidence": evidence[:5],  # Limit to 5 items
            "rounds_used": getattr(debate_result, 'rounds_used', 0),
            "duration_seconds": getattr(debate_result, 'duration_seconds', 0),
            "dissenting_views": getattr(debate_result, 'dissenting_views', []),
            "vote_breakdown": vote_breakdown,
            "convergence_status": getattr(debate_result, 'convergence_status', None),
        }

    def _render_html(self, artifact: ReplayArtifact) -> str:
        """Render HTML using the template with security measures."""
        # Safe JSON embedding: escape </script> to prevent tag termination
        data_json = json.dumps(artifact.to_dict(), indent=2)
        safe_json = data_json.replace("</script>", "</\\script>")

        html = self.html_template.replace("{{DATA}}", safe_json)
        debate_id_escaped = html_module.escape(str(artifact.debate_id)[:8]) if artifact.debate_id else "unknown"
        html = html.replace("{{DEBATE_ID}}", debate_id_escaped)
        return html

    def _get_html_template(self) -> str:
        """Get the HTML template with embedded CSS/JS."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aragora Debate Replay - {{DEBATE_ID}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .verdict-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }

        .verdict-title {
            font-size: 2em;
            margin-bottom: 20px;
            text-align: center;
        }

        .verdict-content {
            font-size: 1.2em;
            line-height: 1.8;
            margin-bottom: 20px;
        }

        .evidence-list {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 20px;
        }

        .evidence-item {
            margin-bottom: 10px;
            padding-left: 20px;
            position: relative;
        }

        .evidence-item:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #4CAF50;
        }

        .timeline {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .timeline-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }

        .timeline-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
            gap: 20px;
        }

        .timeline-bar {
            flex: 1;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            cursor: pointer;
            position: relative;
        }

        .timeline-progress {
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            border-radius: 4px;
            width: 0%;
            transition: width 0.3s ease;
        }

        .timeline-markers {
            position: absolute;
            top: -5px;
            left: 0;
            right: 0;
            height: 18px;
        }

        .consensus-marker {
            position: absolute;
            width: 12px;
            height: 12px;
            background: #4CAF50;
            border-radius: 50%;
            border: 2px solid white;
            cursor: pointer;
            transform: translateX(-50%);
        }

        .round-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        .round-btn:hover {
            background: #5a67d8;
        }

        .scene-view {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
        }

        .message {
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .message-role {
            font-weight: bold;
            color: #667eea;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .message-agent {
            font-weight: bold;
            color: #2d3748;
        }

        .message-timestamp {
            color: #718096;
            font-size: 0.8em;
        }

        .message-content {
            line-height: 1.6;
        }

        .consensus-indicator {
            background: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
            text-align: center;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Aragora Debate Replay</h1>
            <p>Interactive timeline of an AI debate</p>
        </div>

        <div class="verdict-card" id="verdictCard">
            <div class="verdict-title">Verdict</div>
            <div class="verdict-content" id="verdictContent"></div>
            <div class="evidence-list" id="evidenceList"></div>
        </div>

        <div class="timeline">
            <div class="timeline-title">Debate Timeline</div>
            <div class="timeline-controls">
                <button class="round-btn" id="prevBtn">Previous</button>
                <div class="timeline-bar" id="timelineBar">
                    <div class="timeline-progress" id="timelineProgress"></div>
                    <div class="timeline-markers" id="timelineMarkers"></div>
                </div>
                <button class="round-btn" id="nextBtn">Next</button>
            </div>
            <div class="scene-view" id="sceneView"></div>
        </div>

        <div class="footer">
            <p>Generated by Aragora - Self-improving AI Debate System</p>
        </div>
    </div>

    <script>
        const data = {{DATA}};

        let currentRound = 0;
        const scenes = data.scenes;
        const verdict = data.verdict;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            renderVerdict();
            renderTimelineMarkers();
            showRound(0);
            updateControls();
        });

        // Handle single scene case
        const hasMultipleScenes = scenes.length > 1;
        if (!hasMultipleScenes) {
            // Disable timeline controls for single scene
            document.getElementById('timelineBar').style.opacity = '0.5';
            document.getElementById('prevBtn').disabled = true;
            document.getElementById('nextBtn').disabled = true;
        }

        function renderVerdict() {
            const content = document.getElementById('verdictContent');
            const evidence = document.getElementById('evidenceList');

            let status = verdict.consensus_reached ? '✅ Consensus Reached' : '❌ No Consensus';
            let confidence = verdict.confidence ? ` (Confidence: ${(verdict.confidence * 100).toFixed(1)}%)` : '';

            // Use textContent for safe content insertion
            content.innerHTML = `
                <strong>Status:</strong> ${status}${confidence}<br>
                <strong>Rounds:</strong> ${verdict.rounds_used}<br>
                <strong>Duration:</strong> ${Math.round(verdict.duration_seconds)}s<br>
                <strong>Winner:</strong> ${verdict.winner_label || 'None'}<br><br>
                <strong>Final Answer:</strong><br>
                <span>${verdict.final_answer}</span>
            `;

            if (verdict.evidence && verdict.evidence.length > 0) {
                evidence.innerHTML = '<h4>Key Evidence:</h4>' +
                    verdict.evidence.map(item => `<div class="evidence-item">${item}</div>`).join('');
            }
        }

        function renderTimelineMarkers() {
            const markers = document.getElementById('timelineMarkers');
            const bar = document.getElementById('timelineBar');

            // Guard against single/empty scenes
            if (scenes.length <= 1) return;

            scenes.forEach((scene, index) => {
                if (scene.consensus_indicators && scene.consensus_indicators.reached) {
                    const marker = document.createElement('div');
                    marker.className = 'consensus-marker';
                    marker.style.left = `${(index / (scenes.length - 1)) * 100}%`;
                    marker.title = `Round ${scene.round_number}: ${scene.consensus_indicators.description || 'Consensus reached'}`;
                    marker.addEventListener('click', () => showRound(index));
                    markers.appendChild(marker);
                }
            });
        }

        function showRound(roundIndex) {
            currentRound = roundIndex;
            const scene = scenes[roundIndex];
            const view = document.getElementById('sceneView');

            if (!scene) return;

            // Clear previous content
            view.innerHTML = '';

            // Add round header
            const header = document.createElement('h3');
            header.textContent = `Round ${scene.round_number}`;
            view.appendChild(header);

            // Add consensus indicator if present
            if (scene.consensus_indicators && scene.consensus_indicators.reached) {
                const indicator = document.createElement('div');
                indicator.className = 'consensus-indicator';
                indicator.textContent = scene.consensus_indicators.description;
                view.appendChild(indicator);
            }

            // Add messages safely
            scene.messages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message';

                const headerDiv = document.createElement('div');
                headerDiv.className = 'message-header';

                const roleSpan = document.createElement('span');
                roleSpan.className = 'message-role';
                roleSpan.textContent = msg.role;
                headerDiv.appendChild(roleSpan);

                const agentSpan = document.createElement('span');
                agentSpan.className = 'message-agent';
                agentSpan.textContent = msg.agent;
                headerDiv.appendChild(agentSpan);

                const timeSpan = document.createElement('span');
                timeSpan.className = 'message-timestamp';
                timeSpan.textContent = new Date(msg.timestamp).toLocaleTimeString();
                headerDiv.appendChild(timeSpan);

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.innerHTML = formatContent(msg.content); // Safe: formatContent escapes

                msgDiv.appendChild(headerDiv);
                msgDiv.appendChild(contentDiv);
                view.appendChild(msgDiv);
            });

            updateProgress();
        }

        function formatContent(content) {
            // Escape HTML entities and add line breaks
            const escaped = content
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#x27;')
                .replace(/\//g, '&#x2F;');
            return escaped.replace(/\\n/g, '<br>');
        }

        function updateProgress() {
            const progress = document.getElementById('timelineProgress');
            const percentage = scenes.length <= 1 ? 100 : (currentRound / (scenes.length - 1)) * 100;
            progress.style.width = `${percentage}%`;
        }

        function updateControls() {
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');

            prevBtn.disabled = currentRound === 0;
            nextBtn.disabled = currentRound === scenes.length - 1;

            prevBtn.onclick = () => showRound(Math.max(0, currentRound - 1));
            nextBtn.onclick = () => showRound(Math.min(scenes.length - 1, currentRound + 1));
        }

        // Timeline bar click (guarded for single scene)
        document.getElementById('timelineBar').addEventListener('click', function(e) {
            if (scenes.length <= 1) return;

            const rect = this.getBoundingClientRect();
            const percentage = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
            const roundIndex = Math.round(percentage * (scenes.length - 1));
            showRound(roundIndex);
        });

        // Update controls when round changes
        const originalShowRound = showRound;
        showRound = function(roundIndex) {
            originalShowRound(roundIndex);
            updateControls();
        };
    </script>
</body>
</html>"""