import os
import threading
from queue import Empty, Queue

import pymysql
from pymysql.cursors import DictCursor

from config import MYSQL_DB, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_DIALECT = "postgres" if DATABASE_URL.lower().startswith(("postgres://", "postgresql://")) else "mysql"

MYSQL_DB_CONFIG = {
    "host": MYSQL_HOST,
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "database": MYSQL_DB,
    "port": MYSQL_PORT,
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}

# Simple Connection Pool Implementation
class SimpleConnectionPool:
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)

    def get_connection(self):
        try:
            conn = self.pool.get(block=False)
        except Empty:
            conn = None

        if conn is not None:
            if DB_DIALECT == "mysql":
                try:
                    conn.ping(reconnect=True)
                    return conn
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
            else:
                try:
                    if getattr(conn, "closed", 1) == 0:
                        return conn
                except Exception:
                    pass

        return _create_connection()

    def return_connection(self, conn):
        try:
            self.pool.put(conn, block=False)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

def _create_connection():
    if DB_DIALECT == "postgres":
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except Exception as exc:
            raise RuntimeError(
                "PostgreSQL DATABASE_URL is set but psycopg2 is not installed. "
                "Add psycopg2-binary to requirements.txt"
            ) from exc

        # Render commonly provides DATABASE_URL.
        # psycopg2 accepts both postgres:// and postgresql://
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    return pymysql.connect(**MYSQL_DB_CONFIG)


try:
    pool_size = int(os.getenv("DB_POOL_SIZE", 5))
    connection_pool = SimpleConnectionPool(pool_size=pool_size)
    POOL_ENABLED = True
    print(f"✅ Database connection pool created (dialect={DB_DIALECT}, size={pool_size})")
except Exception as e:
    print(f"⚠️  Connection pool failed: {e}. Using direct connections.")
    connection_pool = None
    POOL_ENABLED = False


def get_connection():
    """
    Returns a DB-API connection.

    - MySQL: PyMySQL with DictCursor
    - Postgres: psycopg2 with RealDictCursor

    Close connection after use (no-op pool return in most routes).
    """
    if POOL_ENABLED and connection_pool:
        try:
            return connection_pool.get_connection()
        except Exception as e:
            print(f"⚠️  Pool connection failed: {e}. Creating direct connection.")
    
    return _create_connection()
