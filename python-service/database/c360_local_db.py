"""
Base SQLite locale pour le cache C360 (sauvegarde + API mobile).
"""
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from config.settings import C360_LOCAL_DB_PATH
from services.c360_oracle_service import compte_account_number

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db_dir() -> None:
    Path(C360_LOCAL_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def init_local_db() -> None:
    """Crée les tables C360 si elles n'existent pas."""
    _ensure_db_dir()
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS c360_sync_meta (
                customer_no TEXT PRIMARY KEY,
                last_sync_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                comptes_count INTEGER DEFAULT 0,
                ecritures_count INTEGER DEFAULT 0,
                remboursements_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS c360_kyc (
                customer_no TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS c360_comptes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_no TEXT NOT NULL,
                numero_compte TEXT NOT NULL,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(customer_no, numero_compte)
            );

            CREATE INDEX IF NOT EXISTS idx_c360_comptes_customer
                ON c360_comptes(customer_no);

            CREATE TABLE IF NOT EXISTS c360_ecritures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_no TEXT NOT NULL,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_c360_ecritures_account
                ON c360_ecritures(account_no);

            CREATE TABLE IF NOT EXISTS c360_remboursements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_pret TEXT NOT NULL,
                customer_no TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_c360_remboursements_pret
                ON c360_remboursements(no_pret);
            """
        )
        conn.commit()
    logger.info("Base locale C360 initialisée : %s", C360_LOCAL_DB_PATH)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    _ensure_db_dir()
    conn = sqlite3.connect(C360_LOCAL_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_loads(raw: Optional[str]) -> Any:
    if not raw:
        return None
    return json.loads(raw)


def get_sync_status(customer_no: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM c360_sync_meta WHERE customer_no = ?",
            (customer_no,),
        ).fetchone()
        return dict(row) if row else None


def upsert_sync_meta(
    customer_no: str,
    status: str,
    error_message: Optional[str] = None,
    comptes_count: int = 0,
    ecritures_count: int = 0,
    remboursements_count: int = 0,
) -> None:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO c360_sync_meta (
                customer_no, last_sync_at, status, error_message,
                comptes_count, ecritures_count, remboursements_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_no) DO UPDATE SET
                last_sync_at = excluded.last_sync_at,
                status = excluded.status,
                error_message = excluded.error_message,
                comptes_count = excluded.comptes_count,
                ecritures_count = excluded.ecritures_count,
                remboursements_count = excluded.remboursements_count
            """,
            (
                customer_no,
                now,
                status,
                error_message,
                comptes_count,
                ecritures_count,
                remboursements_count,
            ),
        )
        conn.commit()


def save_kyc(customer_no: str, data: Dict[str, Any]) -> None:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO c360_kyc (customer_no, data_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(customer_no) DO UPDATE SET
                data_json = excluded.data_json,
                updated_at = excluded.updated_at
            """,
            (customer_no, _json_dumps(data), now),
        )
        conn.commit()


def save_comptes(customer_no: str, comptes: List[Dict[str, Any]]) -> int:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute("DELETE FROM c360_comptes WHERE customer_no = ?", (customer_no,))
        for compte in comptes:
            numero = compte_account_number(compte)
            if not numero:
                continue
            conn.execute(
                """
                INSERT INTO c360_comptes (customer_no, numero_compte, data_json, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (customer_no, numero, _json_dumps(compte), now),
            )
        conn.commit()
    return len(comptes)


def save_ecritures(account_no: str, ecritures: List[Dict[str, Any]]) -> int:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute("DELETE FROM c360_ecritures WHERE account_no = ?", (account_no,))
        for ecriture in ecritures:
            conn.execute(
                """
                INSERT INTO c360_ecritures (account_no, data_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (account_no, _json_dumps(ecriture), now),
            )
        conn.commit()
    return len(ecritures)


def save_remboursements(
    no_pret: str,
    remboursements: List[Dict[str, Any]],
    customer_no: Optional[str] = None,
) -> int:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute("DELETE FROM c360_remboursements WHERE no_pret = ?", (no_pret,))
        for row in remboursements:
            conn.execute(
                """
                INSERT INTO c360_remboursements (no_pret, customer_no, data_json, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (no_pret, customer_no, _json_dumps(row), now),
            )
        conn.commit()
    return len(remboursements)


def get_kyc(customer_no: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT data_json, updated_at FROM c360_kyc WHERE customer_no = ?",
            (customer_no,),
        ).fetchone()
        if not row:
            return None
        return {"data": _json_loads(row["data_json"]), "updated_at": row["updated_at"]}


def get_comptes(customer_no: str) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT data_json, updated_at FROM c360_comptes
            WHERE customer_no = ?
            ORDER BY numero_compte
            """,
            (customer_no,),
        ).fetchall()
        if not rows:
            return {"data": [], "updated_at": None}
        updated_at = max(r["updated_at"] for r in rows)
        return {
            "data": [_json_loads(r["data_json"]) for r in rows],
            "updated_at": updated_at,
        }


def get_ecritures(account_no: str, limit: Optional[int] = None) -> Dict[str, Any]:
    with get_connection() as conn:
        query = """
            SELECT data_json, updated_at FROM c360_ecritures
            WHERE account_no = ?
            ORDER BY id DESC
        """
        params: tuple = (account_no,)
        if limit is not None:
            query += " LIMIT ?"
            params = (account_no, limit)
        rows = conn.execute(query, params).fetchall()
        if not rows:
            return {"data": [], "updated_at": None}
        updated_at = max(r["updated_at"] for r in rows)
        return {
            "data": [_json_loads(r["data_json"]) for r in rows],
            "updated_at": updated_at,
        }


def get_remboursements(no_pret: str) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT data_json, updated_at FROM c360_remboursements
            WHERE no_pret = ?
            ORDER BY id DESC
            """,
            (no_pret,),
        ).fetchall()
        if not rows:
            return {"data": [], "updated_at": None}
        updated_at = max(r["updated_at"] for r in rows)
        return {
            "data": [_json_loads(r["data_json"]) for r in rows],
            "updated_at": updated_at,
        }
