import os
import logging
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/inventory")
POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN", "2"))
POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX", "20"))

_pool: ThreadedConnectionPool | None = None


def init_pool():
    global _pool
    if _pool is None:
        logger.info("Initializing database connection pool (min=%d, max=%d)", POOL_MIN_CONN, POOL_MAX_CONN)
        _pool = ThreadedConnectionPool(
            minconn=POOL_MIN_CONN,
            maxconn=POOL_MAX_CONN,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor
        )


def close_pool():
    global _pool
    if _pool is not None:
        logger.info("Closing database connection pool")
        _pool.closeall()
        _pool = None


def get_connection():
    if _pool is None:
        init_pool()
    return _pool.getconn()


def return_connection(conn):
    if _pool is not None:
        _pool.putconn(conn)


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        return_connection(conn)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(255) NOT NULL UNIQUE,
                    ip_address VARCHAR(45) NOT NULL,
                    datacenter VARCHAR(255) NOT NULL,
                    state VARCHAR(20) NOT NULL CHECK (state IN ('active', 'offline', 'retired')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_servers_datacenter ON servers(datacenter)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_servers_state ON servers(state)
            """)
            logger.info("Database initialized successfully")


def create_server(hostname: str, ip_address: str, datacenter: str, state: str) -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO servers (hostname, ip_address, datacenter, state)
                VALUES (%s, %s, %s, %s)
                RETURNING id, hostname, ip_address, datacenter, state, created_at, updated_at
                """,
                (hostname, ip_address, datacenter, state)
            )
            return dict(cur.fetchone())


def get_all_servers(skip: int = 0, limit: int = 100) -> list:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, hostname, ip_address, datacenter, state, created_at, updated_at FROM servers ORDER BY id LIMIT %s OFFSET %s",
                (limit, skip)
            )
            return [dict(row) for row in cur.fetchall()]


def get_server_count() -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM servers")
            return cur.fetchone()["count"]


def get_server_by_id(server_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, hostname, ip_address, datacenter, state, created_at, updated_at FROM servers WHERE id = %s",
                (server_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None


def update_server(server_id: int, hostname: str, ip_address: str, datacenter: str, state: str) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE servers
                SET hostname = %s, ip_address = %s, datacenter = %s, state = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, hostname, ip_address, datacenter, state, created_at, updated_at
                """,
                (hostname, ip_address, datacenter, state, server_id)
            )
            row = cur.fetchone()
            return dict(row) if row else None


def delete_server(server_id: int) -> bool:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM servers WHERE id = %s", (server_id,))
            return cur.rowcount > 0


def patch_server(server_id: int, **kwargs) -> dict | None:
    """Update only the provided fields for a server."""
    if not kwargs:
        return get_server_by_id(server_id)

    with get_db() as conn:
        with conn.cursor() as cur:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)

            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(server_id)

            query = f"""
                UPDATE servers
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id, hostname, ip_address, datacenter, state, created_at, updated_at
            """
            cur.execute(query, tuple(values))
            row = cur.fetchone()
            return dict(row) if row else None
