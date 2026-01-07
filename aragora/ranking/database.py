"""
Database abstraction for the ELO ranking system.

Provides centralized connection management to eliminate repeated
sqlite3.connect() boilerplate throughout elo.py.

Note: This uses per-operation connections (not connection pooling) to
maintain thread safety for concurrent access patterns in elo.py.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from aragora.storage.schema import get_wal_connection
from aragora.config import DB_TIMEOUT_SECONDS


class EloDatabase:
    """
    Database wrapper for ELO system operations.

    Creates fresh connections per operation for thread safety (SQLite
    connections cannot be shared across threads). Uses WAL mode for
    better concurrent read/write performance.

    Usage:
        db = EloDatabase("/path/to/elo.db")

        # Context manager with auto-commit/rollback
        with db.connection() as conn:
            conn.execute("INSERT INTO ...")

        # Convenience methods
        row = db.fetch_one("SELECT * FROM ratings WHERE agent_name = ?", ("claude",))
        rows = db.fetch_all("SELECT * FROM ratings ORDER BY elo DESC LIMIT ?", (10,))
    """

    def __init__(self, db_path: Union[str, Path], timeout: float = DB_TIMEOUT_SECONDS):
        """Initialize the EloDatabase wrapper.

        Args:
            db_path: Path to the SQLite database file
            timeout: Connection timeout in seconds
        """
        self.db_path = Path(db_path)
        self._timeout = timeout

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database operations with automatic commit/rollback.

        Creates a fresh connection per operation for thread safety.
        Commits on success, rolls back on exception.

        Yields:
            sqlite3.Connection for database operations
        """
        conn = get_wal_connection(str(self.db_path), self._timeout)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Explicit transaction context manager.

        Same as connection() but uses explicit BEGIN/COMMIT for clarity.

        Yields:
            sqlite3.Connection within a transaction
        """
        conn = get_wal_connection(str(self.db_path), self._timeout)
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        """Execute query and fetch single row.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            Single row as tuple, or None if no results
        """
        with self.connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def fetch_all(self, sql: str, params: tuple = ()) -> list[tuple]:
        """Execute query and fetch all rows.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            List of rows as tuples
        """
        with self.connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def execute_write(self, sql: str, params: tuple = ()) -> None:
        """Execute a write operation with auto-commit.

        Args:
            sql: SQL statement to execute
            params: Statement parameters
        """
        with self.connection() as conn:
            conn.execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> None:
        """Execute a SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples
        """
        with self.connection() as conn:
            conn.executemany(sql, params_list)

    def __repr__(self) -> str:
        return f"EloDatabase({self.db_path!r})"
