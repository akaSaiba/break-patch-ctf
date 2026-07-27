import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "portal.db"
SEED_SQL_PATH = BASE_DIR / "seed.sql"


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
        "points": row["points"],
        "introduction": row["introduction"],
        "vip": bool(row["vip"]),
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


def search_activities(query: str) -> list[dict]:
    """Search campus activities by title."""
    conn = get_connection()

    try:
        rows = conn.execute(
            f"SELECT id, title, points FROM activities WHERE title LIKE '%{query}%'"
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# Below is the database schema for the users table, this will be useful in challenge 3
# CREATE TABLE users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     username TEXT NOT NULL UNIQUE,
#     password TEXT NOT NULL,
#     name TEXT NOT NULL,
#     user_id INTEGER NOT NULL UNIQUE,
#     points INTEGER NOT NULL DEFAULT 0,
#     introduction TEXT,
#     vip INTEGER NOT NULL DEFAULT 0
# );
def award_introduction_bonus(user_id: int, introduction) -> dict:
    """Awards introduction bonus to a user and saves their introduction."""
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT introduction FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if not user:
            return {"ok": False, "message": "You could not be recognized"}

        # Validate introduction
        if not introduction:
            return {"ok": False, "message": "Introduction cannot be empty"}

        if user["introduction"] is not None:
            return {"ok": False, "message": "You already have an introduction!"}

        # Award bonus
        conn.execute(
            "UPDATE users SET points = points + 10000 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

        # Save introduction
        conn.execute(
            "UPDATE users SET introduction = ? WHERE user_id = ?",
            (introduction, user_id),
        )
        conn.commit()

        return {"ok": True, "message": "Introduction saved; 10,000 points awarded"}
        
    finally:
        conn.close()


def get_store_items() -> list[dict]:
    """Return all University Store items ordered by id."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, cost, is_secret FROM store_items ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    finally:
        conn.close()


def purchase_item(user_id: int, item_id: int) -> dict:
    """Spend Personal Points to buy a store item, or return an error result."""
    conn = get_connection()
    try:
        item = conn.execute(
            "SELECT * FROM store_items WHERE id = ?",
            (item_id,),
        ).fetchone()

        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if item is None or user is None:
            return {"ok": False, "message": "Item or user not found"}
        if user["points"] < item["cost"]:
            return {"ok": False, "message": "Not enough Personal Points"}

        conn.execute(
            "UPDATE users SET points = points - ? WHERE user_id = ?",
            (item["cost"], user_id),
        )

        conn.commit()

        return {
            "ok": True,
            "item": dict(item),
            "points": user["points"] - item["cost"],
        }
    finally:
        conn.close()


def set_vip(user_id: int, vip: bool) -> None:
    """Set student's VIP membership status."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET vip = ? WHERE user_id = ?",
            (int(vip), user_id),
        )
        conn.commit()
    finally:
        conn.close()
