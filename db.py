# db.py

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable, Iterator, Optional, Sequence

# ═══════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════

DB_FILE = "clinic.db"

# Tuning knobs
_BUSY_TIMEOUT_MS = 5000          # wait up to 5s for a lock
_CACHE_SIZE_KB = -8000           # ~8 MB page cache (negative = KB)
_MMAP_SIZE_BYTES = 64 * 1024 * 1024  # 64 MB memory-mapped I/O (if supported)

# Thread-local storage for per-thread connections
_local = threading.local()


# ═══════════════════════════════════════════════════════════════════
#  Schema definition
# ═══════════════════════════════════════════════════════════════════

_SCHEMA_SQL: tuple[str, ...] = (
    # patients ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT,
        birth_date TEXT,
        address TEXT,
        notes TEXT,
        blood_type TEXT,
        allergies TEXT,
        chronic_diseases TEXT,
        created_at TEXT
    )
    """,
    # appointments --------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'Scheduled',
        created_at TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """,
    # medical_records ----------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        visit_date TEXT,
        diagnosis TEXT,
        prescription TEXT,
        blood_pressure TEXT,
        temperature TEXT,
        weight TEXT,
        sugar_level TEXT,
        heart_rate TEXT,
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """,
    # inventory -----------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        quantity INTEGER DEFAULT 0,
        min_quantity INTEGER DEFAULT 5,
        purchase_price REAL DEFAULT 0,
        sale_price REAL DEFAULT 0,
        expiry_date TEXT,
        supplier TEXT,
        batch_number TEXT,
        notes TEXT,
        created_at TEXT
    )
    """,
    # invoices ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        invoice_date TEXT,
        subtotal REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        tax REAL DEFAULT 0,
        total REAL DEFAULT 0,
        paid REAL DEFAULT 0,
        status TEXT DEFAULT 'Unpaid',
        payment_method TEXT,
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """,
    # invoice_items -------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        description TEXT,
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0,
        line_total REAL DEFAULT 0,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )
    """,
    # expenses ------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_date TEXT,
        category TEXT,
        description TEXT,
        amount REAL DEFAULT 0,
        payment_method TEXT,
        notes TEXT,
        created_at TEXT
    )
    """,
    # activity_log --------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        entity TEXT,
        entity_id INTEGER,
        details TEXT,
        created_at TEXT
    )
    """,
)

_INDEX_SQL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_patients_name  ON patients(full_name)",
    "CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone)",
    "CREATE INDEX IF NOT EXISTS idx_app_date       ON appointments(appointment_date)",
    "CREATE INDEX IF NOT EXISTS idx_app_patient    ON appointments(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_app_status     ON appointments(status)",
    "CREATE INDEX IF NOT EXISTS idx_rec_patient    ON medical_records(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_rec_date       ON medical_records(visit_date)",
    "CREATE INDEX IF NOT EXISTS idx_inv_date       ON invoices(invoice_date)",
    "CREATE INDEX IF NOT EXISTS idx_inv_patient    ON invoices(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_inv_status     ON invoices(status)",
    "CREATE INDEX IF NOT EXISTS idx_items_invoice  ON invoice_items(invoice_id)",
    "CREATE INDEX IF NOT EXISTS idx_inv_name       ON inventory(name)",
    "CREATE INDEX IF NOT EXISTS idx_inv_expiry     ON inventory(expiry_date)",
    "CREATE INDEX IF NOT EXISTS idx_exp_date       ON expenses(expense_date)",
    "CREATE INDEX IF NOT EXISTS idx_exp_category   ON expenses(category)",
    "CREATE INDEX IF NOT EXISTS idx_log_created    ON activity_log(created_at)",
)


# ═══════════════════════════════════════════════════════════════════
#  Connection management
# ═══════════════════════════════════════════════════════════════════

def _configure(conn: sqlite3.Connection) -> None:
    """Apply PRAGMAs tuned for a desktop clinic app."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Safety & correctness
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    # Performance (WAL allows concurrent readers + faster writes)
    cur.execute("PRAGMA journal_mode = WAL")
    cur.execute("PRAGMA synchronous = NORMAL")
    cur.execute("PRAGMA temp_store = MEMORY")
    cur.execute(f"PRAGMA cache_size = {_CACHE_SIZE_KB}")
    # Memory-mapped I/O — best-effort (ignored by some builds)
    try:
        cur.execute(f"PRAGMA mmap_size = {_MMAP_SIZE_BYTES}")
    except sqlite3.DatabaseError:
        pass
    cur.close()


def _get_connection() -> sqlite3.Connection:
    """Return (or create) the current thread's connection."""
    conn: Optional[sqlite3.Connection] = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_FILE, timeout=_BUSY_TIMEOUT_MS / 1000.0,
                               isolation_level=None)  # autocommit; we control txns
        _configure(conn)
        _local.conn = conn
    return conn


@contextmanager
def connect_db() -> Iterator[sqlite3.Connection]:
    """
    Context manager yielding a configured SQLite connection.

    Behavior:
      - Reuses the thread's connection (fast).
      - Opens an explicit transaction.
      - Commits on clean exit, rolls back on exception.
      - Closes the connection only at interpreter shutdown or via
        `close_thread_connection()`.
    """
    conn = _get_connection()
    try:
        conn.execute("BEGIN")
        yield conn
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    else:
        try:
            conn.execute("COMMIT")
        except sqlite3.Error:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise


def close_thread_connection() -> None:
    """Close the current thread's connection (optional cleanup)."""
    conn: Optional[sqlite3.Connection] = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except sqlite3.Error:
            pass
        _local.conn = None


# ═══════════════════════════════════════════════════════════════════
#  Initialization & migration
# ═══════════════════════════════════════════════════════════════════

def init_db() -> None:
    """
    Create schema + indexes if missing. Idempotent and safe to call
    on every app start.
    """
    with connect_db() as conn:
        for stmt in _SCHEMA_SQL:
            conn.execute(stmt)
        for stmt in _INDEX_SQL:
            conn.execute(stmt)
        # quick integrity check (fast, read-only)
        try:
            conn.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError:
            pass


def reset_db() -> None:
    """
    Delete the database file and re-create an empty schema.
    DANGEROUS: destroys all data. Use for tests/dev only.
    """
    close_thread_connection()
    for suffix in ("", "-wal", "-shm"):
        p = DB_FILE + suffix
        if os.path.exists(p):
            os.remove(p)
    init_db()


# ═══════════════════════════════════════════════════════════════════
#  Small helpers
# ═══════════════════════════════════════════════════════════════════

def table_exists(name: str) -> bool:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
    return row is not None


def column_exists(table: str, column: str) -> bool:
    """Return True if `column` exists in `table`."""
    with connect_db() as conn:
        rows = conn.execute(f"PRAGMA table_info({_safe_ident(table)})").fetchall()
    return any(r["name"] == column for r in rows)


def _safe_ident(name: str) -> str:
    """Reject anything that is not a simple identifier (defensive)."""
    if not name or not name.replace("_", "").isalnum():
        raise ValueError(f"Unsafe identifier: {name!r}")
    return name


# ═══════════════════════════════════════════════════════════════════
#  Activity log
# ═══════════════════════════════════════════════════════════════════

def log_action(action: str, entity: str = "", entity_id: Optional[int] = None,
               details: str = "") -> None:
    """Insert one row into activity_log."""
    with connect_db() as conn:
        conn.execute(
            """INSERT INTO activity_log
               (action, entity, entity_id, details, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (action, entity, entity_id, details,
             datetime.now().isoformat(timespec="seconds")),
        )


def log_actions_many(entries: Iterable[Sequence[Any]]) -> None:
    """
    Batch-insert activity log rows.

    Each entry: (action, entity, entity_id, details)
    Uses a single transaction → much faster for bulk operations.
    """
    now = datetime.now().isoformat(timespec="seconds")
    rows = [
        (e[0], e[1] if len(e) > 1 else "",
         e[2] if len(e) > 2 else None,
         e[3] if len(e) > 3 else "", now)
        for e in entries
    ]
    if not rows:
        return
    with connect_db() as conn:
        conn.executemany(
            """INSERT INTO activity_log
               (action, entity, entity_id, details, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            rows,
        )


# ═══════════════════════════════════════════════════════════════════
#  Backup
# ═══════════════════════════════════════════════════════════════════

def backup_to(path: str) -> None:
    """
    Safely copy the database to `path` using SQLite's online backup API.
    Correct even while the DB is being written (WAL included).
    """
    src = _get_connection()
    dest = sqlite3.connect(path)
    try:
        src.backup(dest)
        dest.commit()
    finally:
        dest.close()


# ═══════════════════════════════════════════════════════════════════
#  Convenience wrappers (optional but handy)
# ═══════════════════════════════════════════════════════════════════

def fetch_one(sql: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
    with connect_db() as conn:
        return conn.execute(sql, params).fetchone()


def fetch_all(sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
    with connect_db() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql: str, params: Sequence[Any] = ()) -> int:
    """Run a write statement; return lastrowid."""
    with connect_db() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def scalar(sql: str, params: Sequence[Any] = (), default: Any = 0) -> Any:
    with connect_db() as conn:
        row = conn.execute(sql, params).fetchone()
    if not row:
        return default
    val = row[0]
    return default if val is None else val


# ═══════════════════════════════════════════════════════════════════
#  Cleanup on interpreter exit
# ═══════════════════════════════════════════════════════════════════

import atexit


@atexit.register
def _close_all() -> None:  # pragma: no cover
    """Best-effort close of the current thread's connection at exit."""
    close_thread_connection()


# ═══════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print(f"✔ Database ready: {os.path.abspath(DB_FILE)}")
    print(f"  Journal mode : ", end="")
    with connect_db() as c:
        print(c.execute("PRAGMA journal_mode").fetchone()[0])
    print(f"  Tables       : ", end="")
    with connect_db() as c:
        tables = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
    print(", ".join(tables))