"""
Snapshot quotidien de la Collecte d'épargne à vue (Flexcube → SQLite).

Le job du matin (06:00) matérialise le mois courant pour servir le dashboard
sans relancer la requête Oracle lourde à chaque ouverture.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.collecte_epargne_a_vue_query import COLLECTE_EPARGNE_A_VUE_QUERY

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = _PY_ROOT / "data" / "collecte_epargne_a_vue_local.db"
_CALL_TIMEOUT_MS = 240_000

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS collecte_epv_vue_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_key TEXT NOT NULL,
    code_agence TEXT,
    branch_name TEXT,
    code_caf TEXT,
    charge_affaire TEXT,
    matricule_client TEXT,
    numero_compte TEXT,
    nom_client TEXT,
    cum_montant_finance REAL,
    cum_encours_credit REAL,
    obj_col_epv_vue REAL,
    montant_echeance REAL,
    total_depot REAL,
    col_ep_vue REAL
);

CREATE INDEX IF NOT EXISTS idx_collecte_epv_month
    ON collecte_epv_vue_rows(month_key);

CREATE TABLE IF NOT EXISTS collecte_epv_vue_meta (
    month_key TEXT PRIMARY KEY,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL,
    date_debut TEXT,
    date_fin_exclusive TEXT
);
"""


def month_key(month: int, year: int) -> str:
    return f"{int(year):04d}-{int(month):02d}"


def _month_bounds_iso(month: int, year: int) -> tuple[str, str]:
    date_debut = f"{year:04d}-{month:02d}-01"
    if month == 12:
        date_fin_exclusive = f"{year + 1:04d}-01-01"
    else:
        date_fin_exclusive = f"{year:04d}-{month + 1:02d}-01"
    return date_debut, date_fin_exclusive


def _f(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _serialize_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _connect_local() -> sqlite3.Connection:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LOCAL_DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def init_collecte_epv_vue_local_db() -> None:
    conn = _connect_local()
    try:
        conn.executescript(_SQLITE_DDL)
        conn.commit()
    finally:
        conn.close()


def has_collecte_snapshot(month: int, year: int) -> bool:
    init_collecte_epv_vue_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            "SELECT status, row_count FROM collecte_epv_vue_meta WHERE month_key = ?",
            (key,),
        ).fetchone()
        return bool(row and row["status"] == "ok" and (row["row_count"] or 0) > 0)
    finally:
        conn.close()


def get_collecte_snapshot_meta(month: int, year: int) -> Optional[Dict[str, Any]]:
    init_collecte_epv_vue_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT month_key, refreshed_at, row_count, status, error_message,
                   elapsed_seconds, date_debut, date_fin_exclusive
            FROM collecte_epv_vue_meta
            WHERE month_key = ?
            """,
            (key,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _fetch_collecte_from_flexcube(month: int, year: int) -> tuple[List[Dict[str, Any]], str, str]:
    date_debut, date_fin_exclusive = _month_bounds_iso(month, year)
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _CALL_TIMEOUT_MS
            cursor.execute(
                COLLECTE_EPARGNE_A_VUE_QUERY,
                {
                    "date_debut": date_debut,
                    "date_fin_exclusive": date_fin_exclusive,
                },
            )
            columns = [str(col[0]).lower() for col in cursor.description]
            rows: List[Dict[str, Any]] = []
            for raw in cursor.fetchall():
                rows.append(
                    {columns[i]: _serialize_cell(raw[i]) for i in range(len(columns))}
                )
            return rows, date_debut, date_fin_exclusive
        finally:
            cursor.close()


def _upsert_meta(
    conn: sqlite3.Connection,
    key: str,
    *,
    refreshed_at: str,
    row_count: int,
    status: str,
    error_message: Optional[str],
    elapsed_seconds: float,
    date_debut: Optional[str],
    date_fin_exclusive: Optional[str],
) -> None:
    conn.execute(
        """
        INSERT INTO collecte_epv_vue_meta (
            month_key, refreshed_at, row_count, status, error_message,
            elapsed_seconds, date_debut, date_fin_exclusive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month_key) DO UPDATE SET
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds,
            date_debut = excluded.date_debut,
            date_fin_exclusive = excluded.date_fin_exclusive
        """,
        (
            key,
            refreshed_at,
            row_count,
            status,
            error_message,
            elapsed_seconds,
            date_debut,
            date_fin_exclusive,
        ),
    )


def load_collecte_snapshot_rows(month: int, year: int) -> List[Dict[str, Any]]:
    if not has_collecte_snapshot(month, year):
        return []
    key = month_key(month, year)
    conn = _connect_local()
    try:
        rows = conn.execute(
            """
            SELECT
                code_agence, branch_name, code_caf, charge_affaire,
                matricule_client, numero_compte, nom_client,
                cum_montant_finance, cum_encours_credit, obj_col_epv_vue,
                montant_echeance, total_depot, col_ep_vue
            FROM collecte_epv_vue_rows
            WHERE month_key = ?
            ORDER BY code_agence, code_caf, matricule_client
            """,
            (key,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def refresh_collecte_epv_vue_snapshot(
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """Exécute la requête lourde Flexcube et remplace le snapshot du mois."""
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    if m < 1 or m > 12:
        raise ValueError(f"Mois invalide: {m}")

    key = month_key(m, y)
    init_collecte_epv_vue_local_db()
    started = time.monotonic()
    logger.info("📸 Snapshot collecte EPV vue — mois %s", key)

    try:
        rows, date_debut, date_fin_exclusive = _fetch_collecte_from_flexcube(m, y)
        local = _connect_local()
        try:
            local.execute("DELETE FROM collecte_epv_vue_rows WHERE month_key = ?", (key,))
            local.executemany(
                """
                INSERT INTO collecte_epv_vue_rows (
                    month_key, code_agence, branch_name, code_caf, charge_affaire,
                    matricule_client, numero_compte, nom_client,
                    cum_montant_finance, cum_encours_credit, obj_col_epv_vue,
                    montant_echeance, total_depot, col_ep_vue
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        key,
                        str(r.get("code_agence") or ""),
                        str(r.get("branch_name") or ""),
                        str(r.get("code_caf") or ""),
                        str(r.get("charge_affaire") or ""),
                        str(r.get("matricule_client") or ""),
                        str(r.get("numero_compte") or ""),
                        str(r.get("nom_client") or ""),
                        _f(r.get("cum_montant_finance")),
                        _f(r.get("cum_encours_credit")),
                        _f(r.get("obj_col_epv_vue")),
                        _f(r.get("montant_echeance")),
                        _f(r.get("total_depot")),
                        _f(r.get("col_ep_vue")),
                    )
                    for r in rows
                ],
            )
            elapsed = time.monotonic() - started
            refreshed_at = datetime.now().isoformat(timespec="seconds")
            _upsert_meta(
                local,
                key,
                refreshed_at=refreshed_at,
                row_count=len(rows),
                status="ok",
                error_message=None,
                elapsed_seconds=round(elapsed, 2),
                date_debut=date_debut,
                date_fin_exclusive=date_fin_exclusive,
            )
            local.commit()
        finally:
            local.close()

        logger.info(
            "✅ Snapshot collecte EPV vue %s: %s lignes en %.1fs",
            key,
            len(rows),
            elapsed,
        )
        return {
            "success": True,
            "month_key": key,
            "month": m,
            "year": y,
            "row_count": len(rows),
            "elapsed_seconds": round(elapsed, 2),
            "refreshed_at": refreshed_at,
            "date_debut": date_debut,
            "date_fin_exclusive": date_fin_exclusive,
        }
    except Exception as exc:
        elapsed = time.monotonic() - started
        logger.error("❌ Snapshot collecte EPV vue échoué (%s): %s", key, exc, exc_info=True)
        local = _connect_local()
        try:
            _upsert_meta(
                local,
                key,
                refreshed_at=datetime.now().isoformat(timespec="seconds"),
                row_count=0,
                status="error",
                error_message=str(exc),
                elapsed_seconds=round(elapsed, 2),
                date_debut=None,
                date_fin_exclusive=None,
            )
            local.commit()
        finally:
            local.close()
        raise
