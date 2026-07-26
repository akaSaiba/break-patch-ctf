import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "portal.db"
SEED_SQL_PATH = BASE_DIR / "seed.sql"

USER_COLUMNS = {
    "username",
    "password",
    "name",
    "bio",
    "user_id",
    "role",
    "uuid",
}


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection to portal.db with row-dict access enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Wipe and rebuild portal.db from seed.sql."""
    if not SEED_SQL_PATH.exists():
        raise FileNotFoundError(f"Missing editable seed file: {SEED_SQL_PATH}")

    if DB_PATH.exists():
        DB_PATH.unlink()

    seed_sql = SEED_SQL_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(seed_sql)
        conn.commit()
    finally:
        conn.close()


def _row_to_user(row: sqlite3.Row | None) -> dict | None:
    """Convert a users table row into a plain user dict, or None."""
    if row is None:
        return None
    return {
        "id": row["user_id"],
        "user_id": row["user_id"],
        "username": row["username"],
        "name": row["name"],
        "bio": row["bio"],
        "role": row["role"],
        "uuid": row["uuid"],
    }


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch a user by numeric user_id."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Fetch a user by username."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def verify_credentials(username: str, password: str) -> dict | None:
    """Return the user if username/password match, otherwise None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def make_session_token(user: dict) -> str:
    """Build a session cookie value (session_<user_id>) from a user record."""
    return f"session_{user['user_id']}"


def parse_session_token(session_token: str | None) -> int | None:
    """Parse user_id from a session cookie, or None if invalid."""
    if not session_token or not session_token.startswith("session_"):
        return None
    try:
        return int(session_token.split("_", 1)[1])
    except (IndexError, ValueError):
        return None

# ##############################################################################
#
#   FUNCTIONS THAT API ENDPOINTS CALL
#   Functions that are used in challenges can be found below
#
# ##############################################################################

def get_results_by_user_id(user_id: int) -> list[dict] | None:
    """Return assignment results for a user_id, or None if the user does not exist."""
    
    conn = get_connection()
    try:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if exists is None:
            return None

        rows = conn.execute(
            """
            SELECT assignment, score, grade, submitted
            FROM results
            WHERE user_id = ?
            ORDER BY submitted
            """,
            (user_id,),
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_exams() -> list[dict]:
    """Return exam paper contents from the exams table."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, course, title, content
            FROM exams
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_exam_solutions() -> list[dict]:
    """Return exam answer keys from the exam_solutions table."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, exam_id, title, solution
            FROM exam_solutions
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_classmates() -> list[dict]:
    """Return all students, including uuid (intentional info disclosure)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT user_id, name, uuid
            FROM users
            WHERE role = 'student'
            ORDER BY name
            """
        ).fetchall()
        return [
            {
                "id": row["user_id"],
                "user_id": row["user_id"],
                "name": row["name"],
                "uuid": row["uuid"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_notes_by_uuid(user_uuid: str) -> list[dict] | None:
    """Return notes for a user uuid, or None if that uuid is unknown."""
    conn = get_connection()
    try:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE uuid = ?",
            (user_uuid,),
        ).fetchone()
        if exists is None:
            return None

        rows = conn.execute(
            """
            SELECT title, content
            FROM notes
            WHERE user_uuid = ?
            ORDER BY id
            """,
            (user_uuid,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_user_profile(user_id: int, payload: dict) -> dict | None:
    """Update a user's information in the database."""

    user = get_user_by_id(user_id)
    if user is None:
        return None

    updates = {key: value for key, value in payload.items() if key in USER_COLUMNS}
    if not updates:
        return user

    user.update(updates)

    profile_update = ", ".join(f"{column} = ?" for column in updates)
    values = list(updates.values()) + [user_id]

    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE users SET {profile_update} WHERE user_id = ?",
            values,
        )
        conn.commit()
    finally:
        conn.close()

    # If user_id itself was changed, look up by the new value
    lookup_id = updates.get("user_id", user_id)
    return get_user_by_id(lookup_id)
