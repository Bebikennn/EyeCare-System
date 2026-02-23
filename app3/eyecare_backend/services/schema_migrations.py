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
                logging.getLogger(__name__).info(
                    "Expanded users.password_hash to TEXT (was %s(%s))",
                    data_type,
                    max_len,
                )
                return

            return

        # MySQL
        cur.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
        row = cur.fetchone() or {}
        col_type = (row.get("Type") or row.get("type") or "").lower()
        if "varchar(64" in col_type:
            cur.execute("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NOT NULL")
            conn.commit()
            logging.getLogger(__name__).info(
                "Expanded users.password_hash to VARCHAR(255) (was %s)",
                col_type,
            )

    except Exception:
        logging.getLogger(__name__).exception("Schema migration failed (users.password_hash)")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def ensure_core_tables() -> None:
    """Create core tables if missing.

    Render deployments often start with a fresh Postgres database. The app routes
    expect these tables to exist.

    Idempotent and safe to run on every startup.
    """

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if DB_DIALECT == "postgres":
            # Notifications
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info',
                    is_read INTEGER NOT NULL DEFAULT 0,
                    link TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Health records (minimal columns used by routes)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS health_records (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    bmi NUMERIC,
                    medical_history TEXT,
                    blood_pressure TEXT,
                    blood_sugar TEXT,
                    diabetes INTEGER,
                    hypertension INTEGER,
                    previous_eye_surgery INTEGER,
                    date_recorded DATE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Habit data
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS habit_data (
                    habit_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    screen_time_hours NUMERIC,
                    sleep_hours NUMERIC,
                    diet_quality INTEGER,
                    smoking_status TEXT,
                    alcohol_use INTEGER,
                    outdoor_activity_hours NUMERIC,
                    water_intake_liters NUMERIC,
                    physical_activity_level INTEGER,
                    glasses_usage INTEGER,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Eye symptoms
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS eye_symptoms (
                    symptom_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    eye_pain_frequency INTEGER,
                    blurry_vision_score INTEGER,
                    light_sensitivity TEXT,
                    eye_strains_per_day INTEGER,
                    family_history_eye_disease INTEGER,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Assessment results
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS assessment_results (
                    assessment_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    risk_level TEXT,
                    risk_score NUMERIC,
                    confidence_score NUMERIC,
                    predicted_disease TEXT,
                    assessment_data TEXT,
                    per_disease_scores TEXT,
                    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Recommendations
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    recommendation_text TEXT NOT NULL,
                    priority TEXT DEFAULT 'Medium',
                    category TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()
            return

        # MySQL (no-op if already created)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_notifications (
                notification_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(20) DEFAULT 'info',
                is_read TINYINT(1) DEFAULT 0,
                link VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (notification_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        conn.commit()

    except Exception:
        logging.getLogger(__name__).exception("Schema migration failed (core tables)")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def ensure_users_columns() -> None:
    """Ensure commonly-used columns exist on `users`.

    Some deployments have an older/minimal `users` table. Routes expect columns
    like address/profile_picture_url/status.
    """

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if DB_DIALECT == "postgres":
            # Safe in Postgres
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
            conn.commit()
            return

        # MySQL: check first (older MySQL doesn't support ADD COLUMN IF NOT EXISTS reliably)
        cur.execute("SHOW COLUMNS FROM users")
        rows = cur.fetchall() or []
        existing = {str(r.get('Field') or r.get('field') or '').lower() for r in rows}

        def _add(name: str, ddl: str) -> None:
            if name.lower() not in existing:
                cur.execute(ddl)

        _add('phone_number', "ALTER TABLE users ADD COLUMN phone_number VARCHAR(32) NULL")
        _add('full_name', "ALTER TABLE users ADD COLUMN full_name VARCHAR(255) NULL")
        _add('address', "ALTER TABLE users ADD COLUMN address TEXT NULL")
        _add('profile_picture_url', "ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR(500) NULL")
        _add('status', "ALTER TABLE users ADD COLUMN status VARCHAR(50) NULL")
        conn.commit()

    except Exception:
        logging.getLogger(__name__).exception("Schema migration failed (users columns)")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
