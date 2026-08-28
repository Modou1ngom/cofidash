"""
Snapshot du portefeuille à risque (Flexcube → SQLite).

Une photo par (mois, grain) : lignes brutes agence ou CAF à la date d'arrêté.
Le dashboard lit M et M-1 depuis SQLite au lieu de relancer les requêtes PAR.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import clear_cache
from services.portefeuille_risque_global_query import (
    PORTEFEUILLE_AGENCE_QUERY,
    PORTEFEUILLE_GLOBAL_QUERY,
)

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = _PY_ROOT / "data" / "portefeuille_risque_local.db"
_CALL_TIMEOUT_MS = 240_000

GRAINS = ("agence", "caf")

_GRAIN_SQL = {
    "agence": PORTEFEUILLE_AGENCE_QUERY,
    "caf": PORTEFEUILLE_GLOBAL_QUERY,
}

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS par_snapshots (
    month_key TEXT NOT NULL,
    grain TEXT NOT NULL,
    as_of_date TEXT,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (month_key, grain)
);

CREATE TABLE IF NOT EXISTS par_meta (
    month_key TEXT NOT NULL,
    grain TEXT NOT NULL,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL,
    as_of_date TEXT,
    PRIMARY KEY (month_key, grain)
);
"""


def month_key(month: int, year: int) -> str:
    return f"{int(year):04d}-{int(month):02d}"


def prev_month(month: int, year: int) -> tuple[int, int]:
    if int(month) == 1:
        return 12, int(year) - 1
    return int(month) - 1, int(year)


def as_of_date_str(year: int, month: int) -> str:
    import calendar

    last_day = calendar.monthrange(int(year), int(month))[1]
    as_of = date(int(year), int(month), last_day)
    today = datetime.now().date()
    if as_of > today:
        as_of = today
    return as_of.strftime("%d/%m/%Y")


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _row_jsonable(row: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k): _jsonable(v) for k, v in row.items()}


def _connect_local() -> sqlite3.Connection:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LOCAL_DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def init_par_local_db() -> None:
    conn = _connect_local()
    try:
        conn.executescript(_SQLITE_DDL)
        conn.commit()
    finally:
        conn.close()


def has_par_snapshot(month: int, year: int, grain: str) -> bool:
    init_par_local_db()
    key = month_key(month, year)
    g = (grain or "agence").strip().lower()
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT status FROM par_meta
            WHERE month_key = ? AND grain = ?
            """,
            (key, g),
        ).fetchone()
        return bool(row and row["status"] == "ok")
    finally:
        conn.close()


def get_par_snapshot_meta(
    month: int, year: int, grain: Optional[str] = None
) -> Any:
    init_par_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        if grain:
            g = grain.strip().lower()
            row = conn.execute(
                """
                SELECT month_key, grain, refreshed_at, row_count, status,
                       error_message, elapsed_seconds, as_of_date
                FROM par_meta
                WHERE month_key = ? AND grain = ?
                """,
                (key, g),
            ).fetchone()
            return dict(row) if row else None
        rows = conn.execute(
            """
            SELECT month_key, grain, refreshed_at, row_count, status,
                   error_message, elapsed_seconds, as_of_date
            FROM par_meta
            WHERE month_key = ?
            ORDER BY grain
            """,
            (key,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_par_snapshot(month: int, year: int, grain: str) -> List[Dict[str, Any]]:
    init_par_local_db()
    key = month_key(month, year)
    g = (grain or "agence").strip().lower()
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT payload_json FROM par_snapshots
            WHERE month_key = ? AND grain = ?
            """,
            (key, g),
        ).fetchone()
        if not row or not row["payload_json"]:
            return []
        data = json.loads(row["payload_json"])
        return data if isinstance(data, list) else []
    finally:
        conn.close()


def _fetch_from_flexcube(grain: str, as_of: str) -> List[Dict[str, Any]]:
    g = (grain or "agence").strip().lower()
    sql = _GRAIN_SQL.get(g)
    if not sql:
        raise ValueError(f"Grain PAR inconnu: {g}")

    logger.info("📅 Snapshot PAR Flexcube grain=%s arrêté=%s", g, as_of)
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _CALL_TIMEOUT_MS
            cursor.arraysize = 500
            cursor.prefetchrows = 500
            cursor.execute(sql, {"as_of_date": as_of})
            columns = [d[0] for d in cursor.description]
            raw_rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
        finally:
            cursor.close()
    return [_row_jsonable(r) for r in raw_rows]


def _upsert_meta(
    conn: sqlite3.Connection,
    key: str,
    grain: str,
    *,
    refreshed_at: str,
    row_count: int,
    status: str,
    error_message: Optional[str],
    elapsed_seconds: float,
    as_of_date: str,
) -> None:
    conn.execute(
        """
        INSERT INTO par_meta (
            month_key, grain, refreshed_at, row_count, status,
            error_message, elapsed_seconds, as_of_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month_key, grain) DO UPDATE SET
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds,
            as_of_date = excluded.as_of_date
        """,
        (
            key,
            grain,
            refreshed_at,
            row_count,
            status,
            error_message,
            elapsed_seconds,
            as_of_date,
        ),
    )


def refresh_par_snapshot(
    month: Optional[int] = None,
    year: Optional[int] = None,
    grain: Optional[str] = None,
) -> Dict[str, Any]:
    """Rafraîchit le snapshot SQLite pour un mois (un grain ou agence+CAF)."""
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    if m < 1 or m > 12:
        raise ValueError(f"Mois invalide: {m}")

    grains = [grain.strip().lower()] if grain else list(GRAINS)
    for g in grains:
        if g not in _GRAIN_SQL:
            raise ValueError(f"Grain PAR inconnu: {g}")

    init_par_local_db()
    key = month_key(m, y)
    as_of = as_of_date_str(y, m)
    results: List[Dict[str, Any]] = []

    for g in grains:
        started = time.monotonic()
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            rows = _fetch_from_flexcube(g, as_of)
            elapsed = round(time.monotonic() - started, 2)
            conn = _connect_local()
            try:
                conn.execute(
                    """
                    INSERT INTO par_snapshots (month_key, grain, as_of_date, payload_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(month_key, grain) DO UPDATE SET
                        as_of_date = excluded.as_of_date,
                        payload_json = excluded.payload_json
                    """,
                    (key, g, as_of, json.dumps(rows, ensure_ascii=False)),
                )
                _upsert_meta(
                    conn,
                    key,
                    g,
                    refreshed_at=refreshed_at,
                    row_count=len(rows),
                    status="ok",
                    error_message=None,
                    elapsed_seconds=elapsed,
                    as_of_date=as_of,
                )
                conn.commit()
            finally:
                conn.close()
            logger.info(
                "✅ Snapshot PAR %s %s : %s lignes en %.1fs (arrêté %s)",
                g,
                key,
                len(rows),
                elapsed,
                as_of,
            )
            results.append(
                {
                    "month_key": key,
                    "grain": g,
                    "status": "ok",
                    "row_count": len(rows),
                    "elapsed_seconds": elapsed,
                    "refreshed_at": refreshed_at,
                    "as_of_date": as_of,
                }
            )
        except Exception as exc:
            elapsed = round(time.monotonic() - started, 2)
            logger.error("❌ Snapshot PAR %s %s échoué: %s", g, key, exc, exc_info=True)
            conn = _connect_local()
            try:
                _upsert_meta(
                    conn,
                    key,
                    g,
                    refreshed_at=refreshed_at,
                    row_count=0,
                    status="error",
                    error_message=str(exc),
                    elapsed_seconds=elapsed,
                    as_of_date=as_of,
                )
                conn.commit()
            finally:
                conn.close()
            results.append(
                {
                    "month_key": key,
                    "grain": g,
                    "status": "error",
                    "error_message": str(exc),
                    "elapsed_seconds": elapsed,
                    "as_of_date": as_of,
                }
            )

    clear_cache("par-agence:")
    clear_cache("par-caf-raw:")
    ok = all(r.get("status") == "ok" for r in results)
    return {
        "month": m,
        "year": y,
        "month_key": key,
        "as_of_date": as_of,
        "status": "ok" if ok else "error",
        "grains": results,
    }


def ensure_par_snapshot(month: int, year: int, grain: str) -> None:
    """Calcule le snapshot s'il n'existe pas encore."""
    g = (grain or "agence").strip().lower()
    if has_par_snapshot(month, year, g):
        return
    logger.info(
        "⚠️ Pas de snapshot PAR %s %s — calcul Flexcube",
        g,
        month_key(month, year),
    )
    result = refresh_par_snapshot(month=month, year=year, grain=g)
    grain_results = result.get("grains") or []
    if grain_results and grain_results[0].get("status") != "ok":
        raise RuntimeError(
            grain_results[0].get("error_message") or "Échec snapshot PAR"
        )
