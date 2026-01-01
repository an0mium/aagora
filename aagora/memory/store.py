"""
SQLite-based critique pattern store for self-improvement.

Stores successful critique patterns so future debates can learn from past successes.
"""

import sqlite3
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from aagora.core import Critique, DebateResult


@dataclass
class Pattern:
    """A reusable critique pattern."""

    id: str
    issue_type: str  # categorized issue type
    issue_text: str
    suggestion_text: str
    success_count: int
    failure_count: int
    avg_severity: float
    example_task: str
    created_at: str
    updated_at: str

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5


class CritiqueStore:
    """
    SQLite-based storage for critique patterns.

    Enables self-improvement by:
    1. Storing successful critique -> fix patterns
    2. Retrieving similar patterns for new critiques
    3. Tracking which patterns lead to consensus
    """

    def __init__(self, db_path: str = "agora_memory.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Debates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debates (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                final_answer TEXT,
                consensus_reached INTEGER,
                confidence REAL,
                rounds_used INTEGER,
                duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Critiques table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critiques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id TEXT,
                agent TEXT NOT NULL,
                target_agent TEXT,
                issues TEXT,  -- JSON array
                suggestions TEXT,  -- JSON array
                severity REAL,
                reasoning TEXT,
                led_to_improvement INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (debate_id) REFERENCES debates(id)
            )
        """)

        # Patterns table - aggregated successful patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                issue_type TEXT NOT NULL,
                issue_text TEXT NOT NULL,
                suggestion_text TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_severity REAL DEFAULT 0.5,
                example_task TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pattern embeddings for semantic search (optional, for future)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_embeddings (
                pattern_id TEXT PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_critiques_debate ON critiques(debate_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(issue_type)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_patterns_success ON patterns(success_count DESC)"
        )

        conn.commit()
        conn.close()

    def store_debate(self, result: DebateResult):
        """Store a complete debate result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store debate
        cursor.execute(
            """
            INSERT OR REPLACE INTO debates
            (id, task, final_answer, consensus_reached, confidence, rounds_used, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.id,
                result.task,
                result.final_answer,
                1 if result.consensus_reached else 0,
                result.confidence,
                result.rounds_used,
                result.duration_seconds,
            ),
        )

        # Store critiques
        for critique in result.critiques:
            cursor.execute(
                """
                INSERT INTO critiques
                (debate_id, agent, target_agent, issues, suggestions, severity, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.id,
                    critique.agent,
                    critique.target_agent,
                    json.dumps(critique.issues),
                    json.dumps(critique.suggestions),
                    critique.severity,
                    critique.reasoning,
                ),
            )

        conn.commit()
        conn.close()

    def store_pattern(self, critique: Critique, successful_fix: str):
        """Store a successful critique pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for issue in critique.issues:
            # Create pattern ID from issue hash
            pattern_id = hashlib.md5(issue.lower().encode()).hexdigest()[:12]

            # Categorize issue type (simple heuristic)
            issue_type = self._categorize_issue(issue)

            # Get matching suggestion
            suggestion = critique.suggestions[0] if critique.suggestions else ""

            # Check if pattern exists
            cursor.execute("SELECT success_count, avg_severity FROM patterns WHERE id = ?", (pattern_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                new_count = existing[0] + 1
                new_avg = (existing[1] * existing[0] + critique.severity) / new_count
                cursor.execute(
                    """
                    UPDATE patterns
                    SET success_count = ?, avg_severity = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (new_count, new_avg, datetime.now().isoformat(), pattern_id),
                )
            else:
                # Insert new pattern
                cursor.execute(
                    """
                    INSERT INTO patterns
                    (id, issue_type, issue_text, suggestion_text, success_count, avg_severity, example_task)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                    (pattern_id, issue_type, issue, suggestion, critique.severity, successful_fix[:500]),
                )

        conn.commit()
        conn.close()

    def _categorize_issue(self, issue: str) -> str:
        """Simple issue categorization."""
        issue_lower = issue.lower()

        categories = {
            "performance": ["slow", "performance", "efficient", "optimize", "speed", "latency"],
            "security": ["security", "vulnerab", "injection", "auth", "permission", "xss", "csrf"],
            "correctness": ["bug", "error", "incorrect", "wrong", "fail", "break", "crash"],
            "clarity": ["unclear", "confusing", "readab", "document", "comment", "naming"],
            "architecture": ["design", "structure", "pattern", "modular", "coupling", "cohesion"],
            "completeness": ["missing", "incomplete", "todo", "edge case", "handle"],
            "testing": ["test", "coverage", "assert", "mock", "unit", "integration"],
        }

        for category, keywords in categories.items():
            if any(kw in issue_lower for kw in keywords):
                return category

        return "general"

    def retrieve_patterns(
        self,
        issue_type: Optional[str] = None,
        min_success: int = 2,
        limit: int = 10,
    ) -> list[Pattern]:
        """Retrieve successful patterns, optionally filtered by type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if issue_type:
            cursor.execute(
                """
                SELECT id, issue_type, issue_text, suggestion_text, success_count,
                       failure_count, avg_severity, example_task, created_at, updated_at
                FROM patterns
                WHERE issue_type = ? AND success_count >= ?
                ORDER BY success_count DESC
                LIMIT ?
            """,
                (issue_type, min_success, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, issue_type, issue_text, suggestion_text, success_count,
                       failure_count, avg_severity, example_task, created_at, updated_at
                FROM patterns
                WHERE success_count >= ?
                ORDER BY success_count DESC
                LIMIT ?
            """,
                (min_success, limit),
            )

        patterns = [
            Pattern(
                id=row[0],
                issue_type=row[1],
                issue_text=row[2],
                suggestion_text=row[3],
                success_count=row[4],
                failure_count=row[5],
                avg_severity=row[6],
                example_task=row[7],
                created_at=row[8],
                updated_at=row[9],
            )
            for row in cursor.fetchall()
        ]

        conn.close()
        return patterns

    def get_stats(self) -> dict:
        """Get statistics about stored patterns and debates."""
        # Ensure tables exist
        self._init_db()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM debates")
        stats["total_debates"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM debates WHERE consensus_reached = 1")
        stats["consensus_debates"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM critiques")
        stats["total_critiques"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM patterns")
        stats["total_patterns"] = cursor.fetchone()[0]

        cursor.execute("SELECT issue_type, COUNT(*) FROM patterns GROUP BY issue_type")
        stats["patterns_by_type"] = dict(cursor.fetchall())

        cursor.execute("SELECT AVG(confidence) FROM debates WHERE consensus_reached = 1")
        avg_conf = cursor.fetchone()[0]
        stats["avg_consensus_confidence"] = avg_conf if avg_conf else 0.0

        conn.close()
        return stats

    def export_for_training(self) -> list[dict]:
        """Export successful patterns for potential fine-tuning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT d.task, c.issues, c.suggestions, d.final_answer, d.consensus_reached
            FROM critiques c
            JOIN debates d ON c.debate_id = d.id
            WHERE d.consensus_reached = 1
        """
        )

        training_data = []
        for row in cursor.fetchall():
            training_data.append(
                {
                    "task": row[0],
                    "issues": json.loads(row[1]) if row[1] else [],
                    "suggestions": json.loads(row[2]) if row[2] else [],
                    "successful_answer": row[3],
                }
            )

        conn.close()
        return training_data
