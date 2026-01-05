"""
Debate-related endpoint handlers.

Endpoints:
- GET /api/debates - List all debates
- GET /api/debates/{slug} - Get debate by slug
- GET /api/debates/slug/{slug} - Get debate by slug (alternative)
- GET /api/debates/{id}/export/{format} - Export debate
- GET /api/debates/{id}/impasse - Detect debate impasse
- GET /api/debates/{id}/convergence - Get convergence status
- GET /api/debates/{id}/citations - Get evidence citations for debate
"""

from typing import Optional
from .base import BaseHandler, HandlerResult, json_response, error_response, get_int_param


class DebatesHandler(BaseHandler):
    """Handler for debate-related endpoints."""

    # Route patterns this handler manages
    ROUTES = [
        "/api/debates",
        "/api/debates/",  # With trailing slash
        "/api/debates/slug/",
        "/api/debates/*/export/",
        "/api/debates/*/impasse",
        "/api/debates/*/convergence",
        "/api/debates/*/citations",
    ]

    def can_handle(self, path: str) -> bool:
        """Check if this handler can process the given path."""
        if path == "/api/debates":
            return True
        if path.startswith("/api/debates/"):
            return True
        return False

    def handle(self, path: str, query_params: dict, handler) -> Optional[HandlerResult]:
        """
        Route debate requests to appropriate handler methods.

        Note: This delegates to the unified server's existing methods
        to maintain backward compatibility.
        """
        if path == "/api/debates":
            limit = get_int_param(query_params, 'limit', 20)
            limit = min(limit, 100)  # Cap at 100
            return self._list_debates(handler, limit)

        if path.startswith("/api/debates/slug/"):
            slug = path.split("/")[-1]
            return self._get_debate_by_slug(handler, slug)

        if path.endswith("/impasse"):
            debate_id = self._extract_debate_id(path)
            if debate_id:
                return self._get_impasse(handler, debate_id)

        if path.endswith("/convergence"):
            debate_id = self._extract_debate_id(path)
            if debate_id:
                return self._get_convergence(handler, debate_id)

        if path.endswith("/citations"):
            debate_id = self._extract_debate_id(path)
            if debate_id:
                return self._get_citations(handler, debate_id)

        if "/export/" in path:
            parts = path.split("/")
            if len(parts) >= 6:
                debate_id = parts[3]
                export_format = parts[5]
                table = query_params.get('table', 'summary')
                return self._export_debate(handler, debate_id, export_format, table)

        # Default: treat as slug lookup
        if path.startswith("/api/debates/"):
            slug = path.split("/")[-1]
            if slug and slug not in ("impasse", "convergence"):
                return self._get_debate_by_slug(handler, slug)

        return None

    def _extract_debate_id(self, path: str) -> Optional[str]:
        """Extract debate ID from path like /api/debates/{id}/impasse."""
        parts = path.split("/")
        if len(parts) >= 4:
            return parts[3]
        return None

    def _list_debates(self, handler, limit: int) -> HandlerResult:
        """List recent debates."""
        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debates = storage.list_debates(limit=limit)
            return json_response({"debates": debates, "count": len(debates)})
        except Exception as e:
            return error_response(f"Failed to list debates: {e}", 500)

    def _get_debate_by_slug(self, handler, slug: str) -> HandlerResult:
        """Get a debate by slug."""
        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debate = storage.get_debate(slug)
            if debate:
                return json_response(debate)
            return error_response(f"Debate not found: {slug}", 404)
        except Exception as e:
            return error_response(f"Failed to get debate: {e}", 500)

    def _get_impasse(self, handler, debate_id: str) -> HandlerResult:
        """Detect impasse in a debate."""
        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debate = storage.get_debate(debate_id)
            if not debate:
                return error_response(f"Debate not found: {debate_id}", 404)

            # Analyze for impasse indicators
            messages = debate.get("messages", [])
            critiques = debate.get("critiques", [])

            # Simple impasse detection: repetitive critiques without progress
            impasse_indicators = {
                "repeated_critiques": False,
                "no_convergence": not debate.get("consensus_reached", False),
                "high_severity_critiques": any(c.get("severity", 0) > 0.7 for c in critiques),
            }

            is_impasse = sum(impasse_indicators.values()) >= 2

            return json_response({
                "debate_id": debate_id,
                "is_impasse": is_impasse,
                "indicators": impasse_indicators,
            })
        except Exception as e:
            return error_response(f"Impasse detection failed: {e}", 500)

    def _get_convergence(self, handler, debate_id: str) -> HandlerResult:
        """Get convergence status for a debate."""
        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debate = storage.get_debate(debate_id)
            if not debate:
                return error_response(f"Debate not found: {debate_id}", 404)

            return json_response({
                "debate_id": debate_id,
                "convergence_status": debate.get("convergence_status", "unknown"),
                "convergence_similarity": debate.get("convergence_similarity", 0.0),
                "consensus_reached": debate.get("consensus_reached", False),
                "rounds_used": debate.get("rounds_used", 0),
            })
        except Exception as e:
            return error_response(f"Convergence check failed: {e}", 500)

    def _export_debate(self, handler, debate_id: str, format: str, table: str) -> HandlerResult:
        """Export debate in specified format."""
        valid_formats = {"json", "csv", "html"}
        if format not in valid_formats:
            return error_response(f"Invalid format: {format}. Valid: {valid_formats}", 400)

        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debate = storage.get_debate(debate_id)
            if not debate:
                return error_response(f"Debate not found: {debate_id}", 404)

            if format == "json":
                return json_response(debate)
            elif format == "csv":
                return self._format_csv(debate, table)
            elif format == "html":
                return self._format_html(debate)

        except Exception as e:
            return error_response(f"Export failed: {e}", 500)

    def _format_csv(self, debate: dict, table: str) -> HandlerResult:
        """Format debate as CSV for the specified table type."""
        import csv
        import io

        valid_tables = {"messages", "critiques", "votes", "summary"}
        if table not in valid_tables:
            table = "summary"

        output = io.StringIO()
        writer = csv.writer(output)

        if table == "messages":
            # Export messages timeline
            writer.writerow(["round", "agent", "role", "content", "timestamp"])
            for msg in debate.get("messages", []):
                writer.writerow([
                    msg.get("round", ""),
                    msg.get("agent", ""),
                    msg.get("role", ""),
                    msg.get("content", "")[:1000],  # Truncate for CSV
                    msg.get("timestamp", ""),
                ])

        elif table == "critiques":
            # Export critiques
            writer.writerow(["round", "critic", "target", "severity", "summary", "timestamp"])
            for critique in debate.get("critiques", []):
                writer.writerow([
                    critique.get("round", ""),
                    critique.get("critic", ""),
                    critique.get("target", ""),
                    critique.get("severity", ""),
                    critique.get("summary", "")[:500],
                    critique.get("timestamp", ""),
                ])

        elif table == "votes":
            # Export votes
            writer.writerow(["round", "voter", "choice", "reason", "timestamp"])
            for vote in debate.get("votes", []):
                writer.writerow([
                    vote.get("round", ""),
                    vote.get("voter", ""),
                    vote.get("choice", ""),
                    vote.get("reason", "")[:500],
                    vote.get("timestamp", ""),
                ])

        else:  # summary
            # Export summary statistics
            writer.writerow(["field", "value"])
            writer.writerow(["debate_id", debate.get("slug", debate.get("id", ""))])
            writer.writerow(["topic", debate.get("topic", "")])
            writer.writerow(["started_at", debate.get("started_at", "")])
            writer.writerow(["ended_at", debate.get("ended_at", "")])
            writer.writerow(["rounds_used", debate.get("rounds_used", 0)])
            writer.writerow(["consensus_reached", debate.get("consensus_reached", False)])
            writer.writerow(["final_answer", debate.get("final_answer", "")[:1000]])
            writer.writerow(["message_count", len(debate.get("messages", []))])
            writer.writerow(["critique_count", len(debate.get("critiques", []))])
            writer.writerow(["vote_count", len(debate.get("votes", []))])

        csv_content = output.getvalue()
        return (
            csv_content.encode("utf-8"),
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": f'attachment; filename="debate-{debate.get("slug", "export")}-{table}.csv"',
            }
        )

    def _format_html(self, debate: dict) -> HandlerResult:
        """Format debate as standalone HTML page."""
        import html

        debate_id = debate.get("slug", debate.get("id", "export"))
        topic = html.escape(debate.get("topic", "Untitled Debate"))
        messages = debate.get("messages", [])
        critiques = debate.get("critiques", [])
        consensus = debate.get("consensus_reached", False)
        final_answer = html.escape(debate.get("final_answer", "")[:2000])

        # Build message timeline HTML
        messages_html = ""
        for msg in messages[:50]:  # Limit to 50 messages for performance
            agent = html.escape(msg.get("agent", "unknown"))
            content = html.escape(msg.get("content", "")[:500])
            role = msg.get("role", "speaker")
            round_num = msg.get("round", 0)
            messages_html += f'''
            <div class="message {role}">
                <div class="message-header">
                    <span class="agent">{agent}</span>
                    <span class="round">Round {round_num}</span>
                </div>
                <div class="message-content">{content}</div>
            </div>'''

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aragora Debate: {topic}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .stat {{
            background: #16213e;
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid #0f3460;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        .timeline {{
            margin-top: 20px;
        }}
        .message {{
            background: #16213e;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .message.critic {{
            border-left-color: #FF5722;
        }}
        .message.judge {{
            border-left-color: #2196F3;
        }}
        .message-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }}
        .agent {{
            font-weight: bold;
            color: #4CAF50;
        }}
        .round {{
            color: #888;
            font-size: 12px;
        }}
        .message-content {{
            line-height: 1.5;
            white-space: pre-wrap;
        }}
        .consensus {{
            background: #1b4d3e;
            border: 2px solid #4CAF50;
            padding: 20px;
            margin-top: 20px;
            border-radius: 8px;
        }}
        .consensus h2 {{
            color: #4CAF50;
            margin-top: 0;
        }}
        .no-consensus {{
            background: #4d1b1b;
            border-color: #FF5722;
        }}
        .no-consensus h2 {{
            color: #FF5722;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ {topic}</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(messages)}</div>
                <div class="stat-label">Messages</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(critiques)}</div>
                <div class="stat-label">Critiques</div>
            </div>
            <div class="stat">
                <div class="stat-value">{debate.get("rounds_used", 0)}</div>
                <div class="stat-label">Rounds</div>
            </div>
            <div class="stat">
                <div class="stat-value">{"✓" if consensus else "✗"}</div>
                <div class="stat-label">Consensus</div>
            </div>
        </div>

        <div class="timeline">
            <h2>Debate Timeline</h2>
            {messages_html if messages_html else "<p>No messages recorded.</p>"}
        </div>

        <div class="consensus {"" if consensus else "no-consensus"}">
            <h2>{"Final Consensus" if consensus else "No Consensus Reached"}</h2>
            <p>{final_answer if final_answer else "No final answer recorded."}</p>
        </div>

        <p style="color: #666; text-align: center; margin-top: 40px;">
            Exported from Aragora • {debate.get("ended_at", "")[:10] if debate.get("ended_at") else "In progress"}
        </p>
    </div>
</body>
</html>'''

        return (
            html_content.encode("utf-8"),
            200,
            {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Disposition": f'attachment; filename="debate-{debate_id}.html"',
            }
        )

    def _get_citations(self, handler, debate_id: str) -> HandlerResult:
        """Get evidence citations for a debate.

        Returns the grounded verdict including:
        - Claims extracted from final answer
        - Evidence snippets linked to each claim
        - Overall grounding score
        - Full citation list with sources
        """
        import json as json_module

        storage = self.get_storage()
        if not storage:
            return error_response("Storage not available", 503)

        try:
            debate = storage.get_debate(debate_id)
            if not debate:
                return error_response(f"Debate not found: {debate_id}", 404)

            # Check if grounded_verdict is stored
            grounded_verdict_raw = debate.get("grounded_verdict")

            if not grounded_verdict_raw:
                return json_response({
                    "debate_id": debate_id,
                    "has_citations": False,
                    "message": "No evidence citations available for this debate",
                    "grounded_verdict": None,
                })

            # Parse grounded_verdict JSON if it's a string
            if isinstance(grounded_verdict_raw, str):
                try:
                    grounded_verdict = json_module.loads(grounded_verdict_raw)
                except json_module.JSONDecodeError:
                    grounded_verdict = None
            else:
                grounded_verdict = grounded_verdict_raw

            if not grounded_verdict:
                return json_response({
                    "debate_id": debate_id,
                    "has_citations": False,
                    "message": "Evidence citations could not be parsed",
                    "grounded_verdict": None,
                })

            return json_response({
                "debate_id": debate_id,
                "has_citations": True,
                "grounding_score": grounded_verdict.get("grounding_score", 0),
                "confidence": grounded_verdict.get("confidence", 0),
                "claims": grounded_verdict.get("claims", []),
                "all_citations": grounded_verdict.get("all_citations", []),
                "verdict": grounded_verdict.get("verdict", ""),
            })

        except Exception as e:
            return error_response(f"Failed to get citations: {e}", 500)
