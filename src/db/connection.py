"""
Database Connection Manager

Handles SQLite connections for the Billy Walters Sports Analyzer.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from dotenv import load_dotenv

# Load .env file at module import time
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "walters.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DatabaseConnection:
    """Manages SQLite database connection."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQLite database connection.

        Args:
            db_path: Path to SQLite database file (default: data/walters.db)
        """
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_pool(self) -> None:
        """Initialize database schema if needed."""
        if not self.db_path.exists():
            self._initialize_schema()
        else:
            print(f"[OK] Database exists: {self.db_path}")

    def _initialize_schema(self) -> None:
        """Initialize database with schema."""
        try:
            with open(SCHEMA_PATH) as f:
                schema = f.read()

            conn = sqlite3.connect(str(self.db_path))
            conn.executescript(schema)
            conn.commit()
            conn.close()
            print(f"[OK] Database initialized: {self.db_path}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            SQLite database connection

        Raises:
            Exception: If connection fails
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to get connection: {e}")
            raise

    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for database cursor.

        Args:
            commit: Whether to commit after cursor closes

        Yields:
            Database cursor

        Example:
            with db.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO edges ...")
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Database operation failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def execute_query(
        self, query: str, params: Optional[tuple] = None, fetch: bool = True
    ) -> Optional[list]:
        """
        Execute SQL query and optionally fetch results.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE)

        Returns:
            Query results if fetch=True, None otherwise

        Example:
            results = db.execute_query(
                "SELECT * FROM edges WHERE league_id = ?",
                (1,)
            )
        """
        with self.get_cursor(commit=not fetch) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                return cursor.fetchall()
            return None

    def execute_many(self, query: str, data: list) -> None:
        """
        Execute query with multiple parameter sets (bulk insert).

        Args:
            query: SQL query with ? placeholders
            data: List of tuples containing parameter values

        Example:
            db.execute_many(
                "INSERT INTO edges (game_id, edge, classification) VALUES (?, ?, ?)",
                [("123", 5.5, "STRONG"), ("124", 3.2, "MODERATE")]
            )
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.executemany(query, data)

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM leagues;")
                result = cursor.fetchone()
                if result:
                    print(f"[OK] Connected to SQLite: {self.db_path}")
                    return True
            return False
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection(db_path: Optional[Path] = None) -> DatabaseConnection:
    """
    Get or create global database connection instance.

    Args:
        db_path: Path to SQLite database file (default: data/walters.db)

    Returns:
        DatabaseConnection instance

    Example:
        from src.db import get_db_connection

        db = get_db_connection()
        edges = db.execute_query("SELECT * FROM edges WHERE week = 13")
    """
    global _db_connection

    if _db_connection is None:
        _db_connection = DatabaseConnection(db_path=db_path)
        _db_connection.create_pool()

    return _db_connection


def close_db_connection() -> None:
    """Close global database connection."""
    global _db_connection
    _db_connection = None
