"""
Database Connection Manager

Handles PostgreSQL connections using psycopg2 with connection pooling.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load .env file at module import time
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class DatabaseConnection:
    """Manages PostgreSQL database connections with connection pooling."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10,
    ):
        """
        Initialize database connection pool.

        Args:
            host: Database host (default from env: DB_HOST or localhost)
            port: Database port (default from env: DB_PORT or 5432)
            database: Database name (default from env: DB_NAME or billy_walters_analytics)
            user: Database user (default from env: DB_USER or postgres)
            password: Database password (from env: DB_PASSWORD)
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "5432"))
        self.database = database or os.getenv("DB_NAME", "billy_walters_analytics")
        self.user = user or os.getenv("DB_USER", "postgres")
        self.password = password or os.getenv("DB_PASSWORD", "")

        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self.min_connections = min_connections
        self.max_connections = max_connections

    def create_pool(self) -> None:
        """Create connection pool."""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                cursor_factory=DictCursor,
            )
            print(f"[OK] Connection pool created: {self.database}@{self.host}")
        except psycopg2.Error as e:
            print(f"[ERROR] Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """
        Get connection from pool.

        Returns:
            Database connection

        Raises:
            Exception: If pool not initialized or no connections available
        """
        if self.connection_pool is None:
            self.create_pool()

        try:
            return self.connection_pool.getconn()
        except psycopg2.pool.PoolError as e:
            print(f"[ERROR] Failed to get connection from pool: {e}")
            raise

    def return_connection(self, connection) -> None:
        """
        Return connection to pool.

        Args:
            connection: Database connection to return
        """
        if self.connection_pool:
            self.connection_pool.putconn(connection)

    def close_all_connections(self) -> None:
        """Close all connections in pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("[OK] All database connections closed")

    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[DictCursor, None, None]:
        """
        Context manager for database cursor.

        Args:
            commit: Whether to commit after cursor closes

        Yields:
            Database cursor

        Example:
            with db.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO games ...")
        """
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            yield cursor
            if commit:
                connection.commit()
        except Exception as e:
            connection.rollback()
            print(f"[ERROR] Database operation failed: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(connection)

    def execute_query(
        self, query: str, params: Optional[tuple] = None, fetch: bool = True
    ) -> Optional[list]:
        """
        Execute SQL query and optionally fetch results.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE)

        Returns:
            Query results if fetch=True, None otherwise

        Example:
            results = db.execute_query(
                "SELECT * FROM games WHERE week = %s",
                (12,)
            )
        """
        with self.get_cursor(commit=not fetch) as cursor:
            cursor.execute(query, params)

            if fetch:
                return cursor.fetchall()
            return None

    def execute_many(self, query: str, data: list) -> None:
        """
        Execute query with multiple parameter sets (bulk insert).

        Args:
            query: SQL query with placeholders
            data: List of tuples containing parameter values

        Example:
            db.execute_many(
                "INSERT INTO power_ratings (team, rating) VALUES (%s, %s)",
                [("Kansas City", 92.5), ("Buffalo", 91.2)]
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
            result = self.execute_query("SELECT version();")
            if result:
                version = result[0][0]
                print(f"[OK] Connected to PostgreSQL: {version}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> DatabaseConnection:
    """
    Get or create global database connection instance.

    Args:
        host: Database host (default from env)
        port: Database port (default from env)
        database: Database name (default from env)
        user: Database user (default from env)
        password: Database password (default from env)

    Returns:
        DatabaseConnection instance

    Example:
        from db import get_db_connection

        db = get_db_connection()
        games = db.execute_query("SELECT * FROM games WHERE week = 12")
    """
    global _db_connection

    if _db_connection is None:
        _db_connection = DatabaseConnection(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        _db_connection.create_pool()

    return _db_connection


def close_db_connection() -> None:
    """Close global database connection."""
    global _db_connection

    if _db_connection:
        _db_connection.close_all_connections()
        _db_connection = None
