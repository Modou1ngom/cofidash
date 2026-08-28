"""
Snapshot quotidien des transferts d'argent (Flexcube → SQLite).

Une photo par (mois, opérateur) : volumes et commissions agrégés par agence.
Le dashboard lit M et M-1 depuis SQLite au lieu de rescanner le journal.
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
from services.transfers_flexcube_query import (
    SERVICE_COMMISSION_GL_WHERE,
    SERVICE_VOLUME_GL_WHERE,
    sql_transfers_flexcube_month,
)

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = _PY_ROOT / "data" / "transfers_local.db"
_CALL_TIMEOUT_MS = 180_000

TRANSFER_SERVICES = tuple(SERVICE_VOLUME_GL_WHERE.keys())

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS transfers_rows (
    month_key TEXT NOT NULL,
    service TEXT NOT NULL,
    code_agence TEXT NOT NULL,
    libelle_agence TEXT,
    volume REAL,
    commission REAL,
    PRIMARY KEY (month_key, service, code_agence)
);

CREATE INDEX IF NOT EXISTS idx_transfers_month_svc
    ON transfers_rows(month_key, service);

CREATE TABLE IF NOT EXISTS transfers_meta (
    month_key TEXT NOT NULL,
    service TEXT NOT NULL,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL,
    date_debut TEXT,
    date_fin_exclusive TEXT,
    PRIMARY KEY (month_key, service)
);
"""


def month_key(month: int, year: int) -> str:
    return f"{int(year):04d}-{int(month):02d}"


def prev_month(month: int, year: int) -> tuple[int, int]:
    if int(month) == 1:
        return 12, int(year) - 1
    return int(month) - 1, int(year)


def _month_bounds_iso(month: int, year: int) -> tuple[str, str]:
    date_debut = f"{int(year):04d}-{int(month):02d}-01"
    if int(month) == 12:
        date_fin_exclusive = f"{int(year) + 1:04d}-01-01"
    else:
        date_fin_exclusive = f"{int(year):04d}-{int(month) + 1:02d}-01"
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


def _connect_local() -> sqlite3.Connection:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LOCAL_DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def init_transfers_local_db() -> None:
    conn = _connect_local()
    try:
        conn.executescript(_SQLITE_DDL)
        conn.commit()
    finally:
        conn.close()


def has_transfers_snapshot(month: int, year: int, service: str) -> bool:
    init_transfers_local_db()
    key = month_key(month, year)
    svc = (service or "om").strip().lower()
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT status FROM transfers_meta
            WHERE month_key = ? AND service = ?
            """,
            (key, svc),
        ).fetchone()
        return bool(row and row["status"] == "ok")
    finally:
        conn.close()


def get_transfers_snapshot_meta(
    month: int, year: int, service: Optional[str] = None
) -> Any:
    init_transfers_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        if service:
            svc = service.strip().lower()
            row = conn.execute(
                """
                SELECT month_key, service, refreshed_at, row_count, status,
                       error_message, elapsed_seconds, date_debut, date_fin_exclusive
                FROM transfers_meta
                WHERE month_key = ? AND service = ?
                """,
                (key, svc),
            ).fetchone()
            return dict(row) if row else None
        rows = conn.execute(
            """
            SELECT month_key, service, refreshed_at, row_count, status,
                   error_message, elapsed_seconds, date_debut, date_fin_exclusive
            FROM transfers_meta
            WHERE month_key = ?
            ORDER BY service
            """,
            (key,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_transfers_month(month: int, year: int, service: str) -> List[Dict[str, Any]]:
    init_transfers_local_db()
    key = month_key(month, year)
    svc = (service or "om").strip().lower()
    conn = _connect_local()
    try:
        rows = conn.execute(
            """
            SELECT code_agence, libelle_agence, volume, commission
            FROM transfers_rows
            WHERE month_key = ? AND service = ?
            ORDER BY code_agence
            """,
            (key, svc),
        ).fetchall()
        return [
            {
                "code_agence": str(r["code_agence"] or "").strip(),
                "agence": (r["libelle_agence"] or "").strip(),
                "volume": _f(r["volume"]),
                "commission": _f(r["commission"]),
            }
            for r in rows
            if str(r["code_agence"] or "").strip()
        ]
    finally:
        conn.close()


def _fetch_month_from_flexcube(service: str, month: int, year: int) -> List[Dict[str, Any]]:
    svc = (service or "om").strip().lower()
    if svc not in SERVICE_VOLUME_GL_WHERE:
        raise ValueError(f"Service transferts inconnu: {svc}")

    date_debut, date_fin_exclusive = _month_bounds_iso(month, year)
    sql = sql_transfers_flexcube_month(
        SERVICE_VOLUME_GL_WHERE[svc],
        SERVICE_COMMISSION_GL_WHERE[svc],
    )
    binds = {
        "date_debut": date_debut,
        "date_fin_exclusive": date_fin_exclusive,
    }

    logger.info(
        "📅 Snapshot transferts Flexcube %s %s (%s → %s)",
        svc,
        month_key(month, year),
        date_debut,
        date_fin_exclusive,
    )

    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _CALL_TIMEOUT_MS
            cursor.arraysize = 500
            cursor.prefetchrows = 500
            cursor.execute(sql, binds)
            columns = [d[0] for d in cursor.description]
            raw_rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
        finally:
            cursor.close()

    out: List[Dict[str, Any]] = []
    for row in raw_rows:
        code = str(row.get("CODE_AGENCE") or "").strip()
        if not code:
            continue
        out.append(
            {
                "code_agence": code,
                "libelle_agence": (row.get("LIBELLE_AGENCE") or "").strip(),
                "volume": round(_f(row.get("VOLUME")), 2),
                "commission": round(_f(row.get("COMMISSION")), 2),
            }
        )
    return out


def _upsert_meta(
    conn: sqlite3.Connection,
    key: str,
    service: str,
    *,
    refreshed_at: str,
    row_count: int,
    status: str,
    error_message: Optional[str],
    elapsed_seconds: float,
    date_debut: str,
    date_fin_exclusive: str,
) -> None:
    conn.execute(
        """
        INSERT INTO transfers_meta (
            month_key, service, refreshed_at, row_count, status,
            error_message, elapsed_seconds, date_debut, date_fin_exclusive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(month_key, service) DO UPDATE SET
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
            service,
            refreshed_at,
            row_count,
            status,
            error_message,
            elapsed_seconds,
            date_debut,
            date_fin_exclusive,
        ),
    )


def refresh_transfers_snapshot(
    month: Optional[int] = None,
    year: Optional[int] = None,
    service: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rafraîchit le snapshot SQLite pour un mois (un opérateur ou tous).
    """
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    if m < 1 or m > 12:
        raise ValueError(f"Mois invalide: {m}")

    services = [service.strip().lower()] if service else list(TRANSFER_SERVICES)
    for svc in services:
        if svc not in SERVICE_VOLUME_GL_WHERE:
            raise ValueError(f"Service transferts inconnu: {svc}")

    init_transfers_local_db()
    key = month_key(m, y)
    date_debut, date_fin_exclusive = _month_bounds_iso(m, y)
    results: List[Dict[str, Any]] = []

    for svc in services:
        started = time.monotonic()
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            rows = _fetch_month_from_flexcube(svc, m, y)
            elapsed = round(time.monotonic() - started, 2)
            conn = _connect_local()
            try:
                conn.execute(
                    "DELETE FROM transfers_rows WHERE month_key = ? AND service = ?",
                    (key, svc),
                )
                conn.executemany(
                    """
                    INSERT INTO transfers_rows (
                        month_key, service, code_agence, libelle_agence, volume, commission
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            key,
                            svc,
                            r["code_agence"],
                            r["libelle_agence"],
                            r["volume"],
                            r["commission"],
                        )
                        for r in rows
                    ],
                )
                _upsert_meta(
                    conn,
                    key,
                    svc,
                    refreshed_at=refreshed_at,
                    row_count=len(rows),
                    status="ok",
                    error_message=None,
                    elapsed_seconds=elapsed,
                    date_debut=date_debut,
                    date_fin_exclusive=date_fin_exclusive,
                )
                conn.commit()
            finally:
                conn.close()
            logger.info(
                "✅ Snapshot transferts %s %s : %s agences en %.1fs",
                svc,
                key,
                len(rows),
                elapsed,
            )
            results.append(
                {
                    "month_key": key,
                    "service": svc,
                    "status": "ok",
                    "row_count": len(rows),
                    "elapsed_seconds": elapsed,
                    "refreshed_at": refreshed_at,
                }
            )
        except Exception as exc:
            elapsed = round(time.monotonic() - started, 2)
            logger.error(
                "❌ Snapshot transferts %s %s échoué: %s",
                svc,
                key,
                exc,
                exc_info=True,
            )
            conn = _connect_local()
            try:
                _upsert_meta(
                    conn,
                    key,
                    svc,
                    refreshed_at=refreshed_at,
                    row_count=0,
                    status="error",
                    error_message=str(exc),
                    elapsed_seconds=elapsed,
                    date_debut=date_debut,
                    date_fin_exclusive=date_fin_exclusive,
                )
                conn.commit()
            finally:
                conn.close()
            results.append(
                {
                    "month_key": key,
                    "service": svc,
                    "status": "error",
                    "error_message": str(exc),
                    "elapsed_seconds": elapsed,
                }
            )

    ok = all(r.get("status") == "ok" for r in results)
    return {
        "month": m,
        "year": y,
        "month_key": key,
        "status": "ok" if ok else "error",
        "services": results,
    }


def ensure_transfers_snapshot(month: int, year: int, service: str) -> None:
    """Calcule le snapshot s'il n'existe pas encore."""
    if has_transfers_snapshot(month, year, service):
        return
    logger.info(
        "⚠️ Pas de snapshot transferts %s %s — calcul Flexcube",
        service,
        month_key(month, year),
    )
    result = refresh_transfers_snapshot(month=month, year=year, service=service)
    svc_results = result.get("services") or []
    if svc_results and svc_results[0].get("status") != "ok":
        raise RuntimeError(
            svc_results[0].get("error_message") or "Échec snapshot transferts"
        )
