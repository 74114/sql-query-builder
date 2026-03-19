import mysql.connector
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# dynamic config set by connect button
_db_config = {}


def set_connection_config(host, port, user, password, database):
    """Called by /api/db/connect and /api/db/disconnect."""
    global _db_config
    if host is None:
        _db_config = {}
    else:
        _db_config = {
            "host":     host,
            "port":     port,
            "user":     user,
            "password": password,
            "database": database,
        }


def get_connection():
    """
    Create a fresh connection.
    Uses dynamic config if set (via connect button),
    otherwise falls back to .env config.
    """
    if _db_config:
        cfg = _db_config
    else:
        c   = current_app.config
        cfg = {
            "host":     c["MYSQL_HOST"],
            "port":     c["MYSQL_PORT"],
            "user":     c["MYSQL_USER"],
            "password": c["MYSQL_PASSWORD"],
            "database": c["MYSQL_DATABASE"],
        }

    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        autocommit=True,
        connection_timeout=10,
    )


def init_db():
    """Create query_history table on first run."""
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                question      TEXT        NOT NULL,
                dialect       VARCHAR(50) DEFAULT 'MySQL',
                generated_sql LONGTEXT,
                explanation   TEXT,
                executed      TINYINT(1)  DEFAULT 0,
                row_count     INT         DEFAULT 0,
                created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("DB ready.")
    except Exception as e:
        logger.error(f"init_db error: {e}")


def run_select(sql: str, max_rows: int = 500):
    """Run a SELECT safely. Returns (columns, rows, error)."""
    clean = sql.strip().lstrip(";").strip()
    if not clean.upper().startswith("SELECT"):
        return None, None, "Only SELECT queries can be executed."
    if "LIMIT" not in clean.upper():
        clean += f" LIMIT {max_rows}"
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(clean)
        rows    = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        cursor.close()
        return columns, rows, None
    except mysql.connector.Error as e:
        return None, None, str(e)
    finally:
        if conn and conn.is_connected():
            conn.close()


def save_history(question, dialect, sql, explanation):
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_history (question, dialect, generated_sql, explanation)
            VALUES (%s, %s, %s, %s)
        """, (question, dialect, sql, explanation))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id
    except Exception as e:
        logger.error(f"save_history error: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_history(limit=50, offset=0):
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, question, dialect, generated_sql, explanation,
                   executed, row_count, created_at
            FROM query_history
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        rows = cursor.fetchall()
        cursor.close()
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return rows
    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_history_item(record_id):
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM query_history WHERE id = %s", (record_id,))
        row = cursor.fetchone()
        cursor.close()
        if row and row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()
        return row
    except Exception as e:
        logger.error(f"get_history_item error: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()


def delete_history_item(record_id):
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history WHERE id = %s", (record_id,))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"delete_history_item error: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()


def clear_all_history():
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history")
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"clear_all_history error: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()


def mark_executed(record_id, row_count):
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE query_history SET executed=1, row_count=%s WHERE id=%s",
            (row_count, record_id)
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"mark_executed error: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()