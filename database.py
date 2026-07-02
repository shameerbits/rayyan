"""
database.py – SQLite persistence layer for the Rayyan Quran Tracker.

All reads and writes go through this module.  The rest of the application
never touches JSON files or raw SQL; it calls the helper functions here.
"""

import datetime
import json
import os
import sqlite3
import urllib.request

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "rayyan.db")

_LEGACY_JSON = os.path.join(DB_DIR, "app_state.json")
_LEGACY_JSON_BAK = os.path.join(DB_DIR, "app_state.json.bak")

# ---------------------------------------------------------------------------
# Cloud Storage sync (Supabase Storage — optional, falls back to local SQLite)
# Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets or environment vars.
# Create a private storage bucket named "rayyan-data" in your Supabase project.
# ---------------------------------------------------------------------------

# Last sync status — readable by app.py for diagnostics
_cloud_sync_status: dict = {
    "pull": "not_run",   # "ok" | "no_file" | "error:<msg>" | "not_configured"
    "push": "not_run",   # "ok" | "error:<msg>" | "not_configured"
    "last_push_at": None,
    "last_pull_at": None,
}


def get_cloud_sync_status() -> dict:
    """Return a copy of the last cloud sync status for diagnostics."""
    return dict(_cloud_sync_status)


def _cloud_pull_db() -> None:
    """Download rayyan.db from Supabase Storage before the first DB open."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    bucket = os.environ.get("SUPABASE_BUCKET", "rayyan-data")
    if not url or not key:
        _cloud_sync_status["pull"] = "not_configured"
        return
    endpoint = f"{url}/storage/v1/object/{bucket}/rayyan.db"
    try:
        req = urllib.request.Request(
            endpoint,
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
        )
        os.makedirs(DB_DIR, exist_ok=True)
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(DB_PATH, "wb") as fh:
                fh.write(resp.read())
        _cloud_sync_status["pull"] = "ok"
        _cloud_sync_status["last_pull_at"] = datetime.datetime.utcnow().isoformat()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            _cloud_sync_status["pull"] = "no_file"  # First boot — normal
        else:
            _cloud_sync_status["pull"] = f"error:HTTP {e.code} {e.reason}"
    except Exception as e:
        _cloud_sync_status["pull"] = f"error:{type(e).__name__}: {e}"


def _cloud_push_db() -> None:
    """Upload rayyan.db to Supabase Storage after every successful save."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    bucket = os.environ.get("SUPABASE_BUCKET", "rayyan-data")
    if not url or not key:
        _cloud_sync_status["push"] = "not_configured"
        return
    if not os.path.isfile(DB_PATH):
        _cloud_sync_status["push"] = "error:DB file not found"
        return
    endpoint = f"{url}/storage/v1/object/{bucket}/rayyan.db"
    try:
        with open(DB_PATH, "rb") as fh:
            data = fh.read()
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/octet-stream",
                "x-upsert": "true",
            },
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=30):
            pass
        _cloud_sync_status["push"] = "ok"
        _cloud_sync_status["last_push_at"] = datetime.datetime.utcnow().isoformat()
    except urllib.error.HTTPError as e:
        _cloud_sync_status["push"] = f"error:HTTP {e.code} {e.reason}"
    except Exception as e:
        _cloud_sync_status["push"] = f"error:{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Low-level connection helper
# ---------------------------------------------------------------------------


def _open_connection() -> sqlite3.Connection:
    """Return an open SQLite connection configured for this app."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

_CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS history (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        date     TEXT NOT NULL,
        activity TEXT NOT NULL,
        surah    TEXT NOT NULL,
        details  TEXT NOT NULL DEFAULT '',
        points   INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memorized_ayahs (
        surah_name  TEXT    NOT NULL,
        ayah_number INTEGER NOT NULL,
        PRIMARY KEY (surah_name, ayah_number)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS revised_dates (
        surah_name   TEXT NOT NULL,
        ayah_number  TEXT NOT NULL,
        revised_date TEXT NOT NULL,
        PRIMARY KEY (surah_name, ayah_number)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS milestone_catalog (
        id           TEXT    PRIMARY KEY,
        title        TEXT    NOT NULL,
        goal_type    TEXT    NOT NULL DEFAULT 'xp_total',
        target_value INTEGER NOT NULL DEFAULT 1,
        reward_label TEXT    NOT NULL DEFAULT '🎁 Custom Reward',
        reward_xp    INTEGER NOT NULL DEFAULT 0,
        is_active    INTEGER NOT NULL DEFAULT 1,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS milestone_claims (
        milestone_id TEXT PRIMARY KEY,
        claimed_date TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assigned_surahs (
        surah_name    TEXT PRIMARY KEY,
        display_order INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS revision_schedule (
        surah_name              TEXT    NOT NULL,
        ayah_number             TEXT    NOT NULL,
        memorized_date          TEXT    NOT NULL DEFAULT '',
        stage                   INTEGER NOT NULL DEFAULT 0,
        next_due                TEXT    NOT NULL DEFAULT '',
        last_revised            TEXT    NOT NULL DEFAULT '',
        overdue_penalty_applied INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (surah_name, ayah_number)
    )
    """,
]


def init_db() -> None:
    """Create all tables (if they don't exist) and migrate legacy JSON data."""
    _cloud_pull_db()  # Restore DB from cloud before first open (no-op if not configured)
    conn = _open_connection()
    try:
        for sql in _CREATE_TABLES_SQL:
            conn.execute(sql)
        conn.commit()

        # One-time migration from legacy app_state.json
        row_count = conn.execute("SELECT COUNT(*) FROM app_settings").fetchone()[0]
        if row_count == 0:
            _migrate_from_json_if_needed(conn)
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration helper
# ---------------------------------------------------------------------------


def _migrate_from_json_if_needed(conn: sqlite3.Connection) -> None:
    """Import data from the legacy app_state.json into the database once."""
    if not os.path.isfile(_LEGACY_JSON):
        return
    try:
        with open(_LEGACY_JSON, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            return
        _write_state(conn, payload)
        # Rename so it isn't re-imported; keep as a human-readable backup.
        try:
            os.replace(_LEGACY_JSON, _LEGACY_JSON_BAK)
        except OSError:
            pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Settings helpers (key-value store inside app_settings table)
# ---------------------------------------------------------------------------


def _get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute(
        "SELECT value FROM app_settings WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return default
    return row["value"]


def _set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


# ---------------------------------------------------------------------------
# Public read API
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """
    Read all persisted values from SQLite and return them as a plain dict.

    Keys whose values are not present in the database are returned as None
    so that app.py's default-initialisation blocks can handle them normally.
    """
    conn = _open_connection()
    try:
        return _read_state(conn)
    finally:
        conn.close()


def _read_state(conn: sqlite3.Connection) -> dict:
    state: dict = {}

    # ------------------------------------------------------------------
    # Is the database already populated (not a brand-new install)?
    # We use this to distinguish "intentionally empty list" from "never set".
    # ------------------------------------------------------------------
    db_has_data = (
        conn.execute("SELECT COUNT(*) FROM app_settings").fetchone()[0] > 0
    )

    # --- Scalar integer settings ---
    def _int(key: str, default: int = 0) -> int:
        raw = _get_setting(conn, key, str(default))
        try:
            return int(raw)
        except (ValueError, TypeError):
            return default

    state["xp"] = _int("xp", 0)
    state["streak"] = _int("streak", 0)
    state["milestone_version"] = _int("milestone_version", 1)

    # --- Optional string settings (None if empty / not present) ---
    def _opt_str(key: str) -> "str | None":
        val = _get_setting(conn, key, "")
        return val if val else None

    state["last_active_date"] = _opt_str("last_active_date")
    state["last_inactivity_penalty_for_date"] = _opt_str(
        "last_inactivity_penalty_for_date"
    )
    state["last_blessing_claim"] = _opt_str("last_blessing_claim")
    state["nav_section"] = _opt_str("nav_section")
    state["selected_surah"] = _opt_str("selected_surah")
    state["hifdh_selected_surah"] = _opt_str("hifdh_selected_surah")
    state["murajah_selected_surah"] = _opt_str("murajah_selected_surah")

    # --- Required string settings (empty string as fallback) ---
    state["recent_praise"] = _get_setting(conn, "recent_praise", "")

    # --- History (newest-first via DESC on autoincrement id) ---
    rows = conn.execute(
        "SELECT date, activity, surah, details, points"
        " FROM history ORDER BY id DESC"
    ).fetchall()
    state["history"] = [
        {
            "date": row["date"],
            "activity": row["activity"],
            "surah": row["surah"],
            "details": row["details"],
            "points": row["points"],
        }
        for row in rows
    ]

    # --- Memorized ayahs ---
    rows = conn.execute(
        "SELECT surah_name, ayah_number FROM memorized_ayahs ORDER BY ayah_number"
    ).fetchall()
    memorized: dict = {}
    for row in rows:
        surah = row["surah_name"]
        memorized.setdefault(surah, []).append(row["ayah_number"])
    state["memorized"] = memorized

    # --- Revised dates ---
    rows = conn.execute(
        "SELECT surah_name, ayah_number, revised_date FROM revised_dates"
    ).fetchall()
    revised_dates: dict = {}
    for row in rows:
        surah = row["surah_name"]
        revised_dates.setdefault(surah, {})[row["ayah_number"]] = row[
            "revised_date"
        ]
    state["revised_dates"] = revised_dates

    # --- Milestone claims ---
    rows = conn.execute(
        "SELECT milestone_id, claimed_date FROM milestone_claims"
    ).fetchall()
    state["milestone_claims"] = {
        row["milestone_id"]: row["claimed_date"] for row in rows
    }

    # --- Milestone catalog ---
    # Return None on a fresh install so app.py builds the default catalog.
    rows = conn.execute(
        "SELECT id, title, goal_type, target_value, reward_label,"
        "       reward_xp, is_active, created_at, updated_at"
        " FROM milestone_catalog"
    ).fetchall()
    if rows:
        state["milestone_catalog"] = [
            {
                "id": row["id"],
                "title": row["title"],
                "goal_type": row["goal_type"],
                "target_value": row["target_value"],
                "reward_label": row["reward_label"],
                "reward_xp": row["reward_xp"],
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    else:
        # db_has_data == True means all milestones were intentionally deleted.
        # db_has_data == False means fresh install; let app.py build defaults.
        state["milestone_catalog"] = [] if db_has_data else None

    # --- Assigned surahs ---
    rows = conn.execute(
        "SELECT surah_name FROM assigned_surahs ORDER BY display_order"
    ).fetchall()
    if rows:
        state["assigned_surahs"] = [row["surah_name"] for row in rows]
    else:
        state["assigned_surahs"] = [] if db_has_data else None

    # --- Revision schedule ---
    rows = conn.execute(
        "SELECT surah_name, ayah_number, memorized_date, stage, next_due,"
        "       last_revised, overdue_penalty_applied"
        " FROM revision_schedule"
    ).fetchall()
    revision_schedule: dict = {}
    for row in rows:
        surah = row["surah_name"]
        revision_schedule.setdefault(surah, {})[row["ayah_number"]] = {
            "memorized_date": row["memorized_date"],
            "stage": row["stage"],
            "next_due": row["next_due"],
            "last_revised": row["last_revised"],
            "overdue_penalty_applied": bool(row["overdue_penalty_applied"]),
        }
    state["revision_schedule"] = revision_schedule

    return state


# ---------------------------------------------------------------------------
# Public write API
# ---------------------------------------------------------------------------


def save_state(state: dict) -> None:
    """
    Persist all values in *state* to SQLite atomically.

    Silently swallows exceptions so persistence failures never interrupt the
    learning flow.
    """
    try:
        conn = _open_connection()
        try:
            _write_state(conn, state)
            conn.commit()
        finally:
            conn.close()
        _cloud_push_db()  # Sync to cloud after every successful save
    except Exception:
        pass


def _write_state(conn: sqlite3.Connection, state: dict) -> None:
    """Write all state values; called inside an open transaction."""

    today_iso = datetime.date.today().isoformat()

    # --- Scalar settings ---
    _set_setting(conn, "xp", str(state.get("xp", 0)))
    _set_setting(conn, "streak", str(state.get("streak", 0)))
    _set_setting(conn, "milestone_version", str(state.get("milestone_version", 1)))
    _set_setting(
        conn,
        "last_active_date",
        str(state.get("last_active_date") or ""),
    )
    _set_setting(
        conn,
        "last_inactivity_penalty_for_date",
        str(state.get("last_inactivity_penalty_for_date") or ""),
    )
    _set_setting(
        conn,
        "last_blessing_claim",
        str(state.get("last_blessing_claim") or ""),
    )
    _set_setting(conn, "recent_praise", str(state.get("recent_praise") or ""))
    _set_setting(
        conn,
        "nav_section",
        str(state.get("nav_section") or "🏠 Dashboard"),
    )
    _set_setting(
        conn, "selected_surah", str(state.get("selected_surah") or "")
    )
    _set_setting(
        conn,
        "hifdh_selected_surah",
        str(state.get("hifdh_selected_surah") or ""),
    )
    _set_setting(
        conn,
        "murajah_selected_surah",
        str(state.get("murajah_selected_surah") or ""),
    )

    # --- History (full replace; session state list is newest-first) ---
    conn.execute("DELETE FROM history")
    history = state.get("history") or []
    # Insert oldest-first so autoincrement IDs match chronological order.
    for entry in reversed(history):
        conn.execute(
            "INSERT INTO history (date, activity, surah, details, points)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                str(entry.get("date", "")),
                str(entry.get("activity", "")),
                str(entry.get("surah", "")),
                str(entry.get("details", "")),
                int(entry.get("points", 0)),
            ),
        )

    # --- Memorized ayahs (full replace) ---
    conn.execute("DELETE FROM memorized_ayahs")
    for surah_name, ayah_list in (state.get("memorized") or {}).items():
        for ayah_number in ayah_list:
            conn.execute(
                "INSERT OR IGNORE INTO memorized_ayahs (surah_name, ayah_number)"
                " VALUES (?, ?)",
                (str(surah_name), int(ayah_number)),
            )

    # --- Revised dates (full replace) ---
    conn.execute("DELETE FROM revised_dates")
    for surah_name, ayah_map in (state.get("revised_dates") or {}).items():
        for ayah_number, revised_date in ayah_map.items():
            conn.execute(
                "INSERT OR REPLACE INTO revised_dates"
                " (surah_name, ayah_number, revised_date) VALUES (?, ?, ?)",
                (str(surah_name), str(ayah_number), str(revised_date)),
            )

    # --- Milestone catalog (full replace) ---
    conn.execute("DELETE FROM milestone_catalog")
    for milestone in state.get("milestone_catalog") or []:
        conn.execute(
            "INSERT OR REPLACE INTO milestone_catalog"
            " (id, title, goal_type, target_value, reward_label,"
            "  reward_xp, is_active, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(milestone.get("id", "")),
                str(milestone.get("title", "")),
                str(milestone.get("goal_type", "xp_total")),
                int(milestone.get("target_value", 1)),
                str(milestone.get("reward_label", "🎁 Custom Reward")),
                int(milestone.get("reward_xp", 0)),
                1 if milestone.get("is_active", True) else 0,
                str(milestone.get("created_at", today_iso)),
                str(milestone.get("updated_at", today_iso)),
            ),
        )

    # --- Milestone claims (full replace) ---
    conn.execute("DELETE FROM milestone_claims")
    for milestone_id, claimed_date in (state.get("milestone_claims") or {}).items():
        conn.execute(
            "INSERT OR REPLACE INTO milestone_claims (milestone_id, claimed_date)"
            " VALUES (?, ?)",
            (str(milestone_id), str(claimed_date)),
        )

    # --- Assigned surahs (full replace) ---
    conn.execute("DELETE FROM assigned_surahs")
    for order, surah_name in enumerate(state.get("assigned_surahs") or []):
        conn.execute(
            "INSERT OR REPLACE INTO assigned_surahs (surah_name, display_order)"
            " VALUES (?, ?)",
            (str(surah_name), order),
        )

    # --- Revision schedule (full replace) ---
    conn.execute("DELETE FROM revision_schedule")
    for surah_name, ayah_map in (state.get("revision_schedule") or {}).items():
        for ayah_number, entry in ayah_map.items():
            conn.execute(
                "INSERT OR REPLACE INTO revision_schedule"
                " (surah_name, ayah_number, memorized_date, stage, next_due,"
                "  last_revised, overdue_penalty_applied)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(surah_name),
                    str(ayah_number),
                    str(entry.get("memorized_date", "")),
                    int(entry.get("stage", 0)),
                    str(entry.get("next_due", "")),
                    str(entry.get("last_revised", "")),
                    1 if entry.get("overdue_penalty_applied", False) else 0,
                ),
            )
