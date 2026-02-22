import logging

from services.db import DB_DIALECT, get_connection


def ensure_users_password_hash_column() -> None:
    """Ensure `users.password_hash` can store modern password hashes.

    Older schemas used VARCHAR(64) for SHA256 hashes. Werkzeug's
    `generate_password_hash()` outputs much longer strings, so we must expand.

    Safe to run on every startup (idempotent).
    """

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if DB_DIALECT == "postgres":
            cur.execute(
                """
                SELECT data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='users'
                  AND column_name='password_hash'
                """
            )
            row = cur.fetchone() or {}
            data_type = (row.get("data_type") or "").lower()
            max_len = row.get("character_maximum_length")

            # If it's a short VARCHAR (e.g., 64), expand to TEXT.
            if data_type in {"character varying", "varchar"} and (max_len or 0) < 128:
                cur.execute("ALTER TABLE users ALTER COLUMN password_hash TYPE TEXT")
                conn.commit()
                return

            return

        # MySQL
        cur.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
        row = cur.fetchone() or {}
        col_type = (row.get("Type") or row.get("type") or "").lower()
        if "varchar(64" in col_type:
            cur.execute("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NOT NULL")
            conn.commit()

    except Exception:
        logging.getLogger(__name__).exception("Schema migration failed (users.password_hash)")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
