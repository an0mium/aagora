"""
Database abstraction for the evolution module.

Provides thread-safe database access by inheriting from BaseDatabase,
which delegates to DatabaseManager with per-operation connections
for concurrent access patterns.
"""

from aragora.storage import BaseDatabase


class EvolutionDatabase(BaseDatabase):
    """
    Database wrapper for evolution system operations.

    Inherits thread-safe access via BaseDatabase, which uses
    DatabaseManager.fresh_connection() for per-operation connections.
    Uses WAL mode for better concurrent read/write performance.

    Usage:
        db = EvolutionDatabase("/path/to/evolution.db")

        # Context manager with auto-commit/rollback
        with db.connection() as conn:
            conn.execute("INSERT INTO ...")

        # Convenience methods
        row = db.fetch_one("SELECT * FROM strategies WHERE id = ?", ("123",))
        rows = db.fetch_all("SELECT * FROM strategies ORDER BY fitness DESC")
    """

    pass
