"""
Database abstraction for the audience feedback module.

Provides thread-safe database access by inheriting from BaseDatabase,
which delegates to DatabaseManager with per-operation connections
for concurrent access patterns.
"""

from aragora.storage import BaseDatabase


class AudienceDatabase(BaseDatabase):
    """
    Database wrapper for audience feedback operations.

    Inherits thread-safe access via BaseDatabase, which uses
    DatabaseManager.fresh_connection() for per-operation connections.
    Uses WAL mode for better concurrent read/write performance.

    Usage:
        db = AudienceDatabase("/path/to/audience.db")

        # Context manager with auto-commit/rollback
        with db.connection() as conn:
            conn.execute("INSERT INTO ...")

        # Convenience methods
        row = db.fetch_one("SELECT * FROM feedback WHERE id = ?", ("123",))
        rows = db.fetch_all("SELECT * FROM feedback ORDER BY timestamp DESC")
    """

    pass
