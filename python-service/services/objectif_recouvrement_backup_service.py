"""
Objectif de recouvrement du mois, figé le 1er.

Une photo par mois est conservée. Relancer le même mois remplace seulement
cette photo. Les mois précédents restent en place.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.oracle_pool import get_pool_flexcube
from services.suivi_production_backup_service import database_paths

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
_SQL_PATH = _PY_ROOT / "requete mobile" / "production" / "objectif_recouvrement.sql"
_CALL_TIMEOUT_MS = 3_600_000
_refresh_lock = threading.Lock()

ROW_COLUMNS: Tuple[str, ...] = (
    "account_number",
    "statut_pret",
    "exigible_m_1",
    "montant_echeance",
    "objectif_recouvrement",
)

_SQLITE_DDL = f"""
CREATE TABLE IF NOT EXISTS objectif_recouvrement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    {", ".join(f"{column} TEXT" for column in ROW_COLUMNS)}
);

CREATE INDEX IF NOT EXISTS idx_objectif_recouvrement_periode
    ON objectif_recouvrement(annee, mois);

CREATE INDEX IF NOT EXISTS idx_objectif_recouvrement_pret
    ON objectif_recouvrement(annee, mois, account_number);

CREATE TABLE IF NOT EXISTS objectif_recouvrement_meta (
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    date_debut TEXT,
    date_fin TEXT,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL,
    PRIMARY KEY (annee, mois)
);
"""


def _connect(path=None) -> sqlite3.Connection:
    target = path or database_paths()[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_objectif_recouvrement_local_db() -> None:
    for path in database_paths():
        with _connect(path) as conn:
            conn.executescript(_SQLITE_DDL)
            conn.commit()


def _load_sql() -> str:
    if not _SQL_PATH.is_file():
        raise FileNotFoundError(f"Requête introuvable : {_SQL_PATH}")
    return _SQL_PATH.read_text(encoding="utf-8").strip().rstrip(";").strip()


def _serialize_cell(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float):
        return format(value, "f")
    return str(value)


def _month_window(year: int, month: int) -> Tuple[date, date]:
    month = min(12, max(1, int(month)))
    start = date(int(year), month, 1)
    end = date(int(year), month, monthrange(int(year), month)[1])
    return start, end


def _set_meta(
    conn: sqlite3.Connection,
    *,
    year: int,
    month: int,
    status: str,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    row_count: int = 0,
    error_message: Optional[str] = None,
    elapsed_seconds: Optional[float] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO objectif_recouvrement_meta (
            annee, mois, date_debut, date_fin, refreshed_at, row_count,
            status, error_message, elapsed_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(annee, mois) DO UPDATE SET
            date_debut = COALESCE(excluded.date_debut, objectif_recouvrement_meta.date_debut),
            date_fin = COALESCE(excluded.date_fin, objectif_recouvrement_meta.date_fin),
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds
        """,
        (
            int(year),
            int(month),
            date_debut,
            date_fin,
            datetime.now().isoformat(timespec="seconds"),
            row_count,
            status,
            error_message,
            elapsed_seconds,
        ),
    )


def has_objectif_recouvrement_snapshot(year: int, month: int) -> bool:
    init_objectif_recouvrement_local_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT status FROM objectif_recouvrement_meta
            WHERE annee = ? AND mois = ?
            """,
            (int(year), int(month)),
        ).fetchone()
    return bool(row and row["status"] == "success")


def _amount(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def load_objectif_recouvrement(year: int, month: int) -> Optional[dict]:
    init_objectif_recouvrement_local_db()
    with _connect() as conn:
        meta = conn.execute(
            """
            SELECT annee, mois, date_debut, date_fin, refreshed_at, row_count,
                   status, error_message, elapsed_seconds
            FROM objectif_recouvrement_meta
            WHERE annee = ? AND mois = ? AND status = 'success'
            """,
            (int(year), int(month)),
        ).fetchone()
        if not meta:
            return None
        columns = ", ".join(ROW_COLUMNS)
        found = conn.execute(
            f"""
            SELECT {columns}
            FROM objectif_recouvrement
            WHERE annee = ? AND mois = ?
            """,
            (int(year), int(month)),
        ).fetchall()
    rows = [
        {
            "account_number": (item["account_number"] or "").strip(),
            "statut_pret": (item["statut_pret"] or "").strip(),
            "exigible_m_1": _amount(item["exigible_m_1"]),
            "montant_echeance": _amount(item["montant_echeance"]),
            "objectif_recouvrement": _amount(item["objectif_recouvrement"]),
        }
        for item in found
    ]
    return {"meta": dict(meta), "rows": rows}


def refresh_objectif_recouvrement(year: int, month: int) -> Dict[str, Any]:
    """Enregistre l'objectif du mois. Remplace la photo de ce mois seulement."""
    year = int(year)
    month = min(12, max(1, int(month)))
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "already_running", "annee": year, "mois": month}
    try:
        return _refresh(year, month)
    finally:
        _refresh_lock.release()


def _refresh(year: int, month: int) -> Dict[str, Any]:
    start, end = _month_window(year, month)
    init_objectif_recouvrement_local_db()
    started = time.monotonic()
    logger.info(
        "Objectif recouvrement : sauvegarde %02d/%s (%s → %s)",
        month,
        year,
        start.isoformat(),
        end.isoformat(),
    )
    pool = get_pool_flexcube()
    try:
        with pool.get_connection_context() as ora_conn:
            if hasattr(ora_conn, "callTimeout"):
                ora_conn.callTimeout = _CALL_TIMEOUT_MS
            cursor = ora_conn.cursor()
            try:
                if hasattr(cursor, "callTimeout"):
                    cursor.callTimeout = _CALL_TIMEOUT_MS
                cursor.arraysize = 1000
                cursor.execute(_load_sql(), {"date_debut": start, "date_fin": end})
                columns = [str(col[0]).strip().upper() for col in cursor.description]
                index = {name: position for position, name in enumerate(columns)}
                fetched: List[Tuple] = []
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    for raw in batch:
                        values = {
                            column: _serialize_cell(raw[index[column.upper()]])
                            if column.upper() in index
                            else None
                            for column in ROW_COLUMNS
                        }
                        fetched.append((year, month, *(values[column] for column in ROW_COLUMNS)))
            finally:
                cursor.close()

        placeholders = ", ".join(["?"] * (2 + len(ROW_COLUMNS)))
        insert_sql = (
            f"INSERT INTO objectif_recouvrement (annee, mois, {', '.join(ROW_COLUMNS)}) "
            f"VALUES ({placeholders})"
        )
        elapsed = round(time.monotonic() - started, 1)
        stored = [str(path) for path in database_paths()]
        for path in database_paths():
            with _connect(path) as local:
                local.execute("BEGIN")
                local.execute(
                    "DELETE FROM objectif_recouvrement WHERE annee = ? AND mois = ?",
                    (year, month),
                )
                local.executemany(insert_sql, fetched)
                _set_meta(
                    local,
                    year=year,
                    month=month,
                    status="success",
                    date_debut=start.isoformat(),
                    date_fin=end.isoformat(),
                    row_count=len(fetched),
                    elapsed_seconds=elapsed,
                )
                local.commit()
        logger.info(
            "Objectif recouvrement %02d/%s : %s lignes en %.1fs → %s",
            month,
            year,
            len(fetched),
            elapsed,
            ", ".join(stored),
        )
        return {
            "status": "success",
            "annee": year,
            "mois": month,
            "date_debut": start.isoformat(),
            "date_fin": end.isoformat(),
            "row_count": len(fetched),
            "elapsed_seconds": elapsed,
            "path": stored,
        }
    except Exception as exc:
        logger.error(
            "Sauvegarde objectif recouvrement %02d/%s échouée, photo précédente conservée: %s",
            month,
            year,
            exc,
            exc_info=True,
        )
        if not has_objectif_recouvrement_snapshot(year, month):
            try:
                for path in database_paths():
                    with _connect(path) as local:
                        _set_meta(
                            local,
                            year=year,
                            month=month,
                            status="error",
                            date_debut=start.isoformat(),
                            date_fin=end.isoformat(),
                            error_message=str(exc),
                            elapsed_seconds=round(time.monotonic() - started, 1),
                        )
                        local.commit()
            except Exception:
                logger.exception(
                    "Impossible d'enregistrer l'échec objectif recouvrement %02d/%s",
                    month,
                    year,
                )
        raise


def get_objectif_recouvrement_data(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    today = date.today()
    year = int(year or today.year)
    month = min(12, max(1, int(month or today.month)))
    saved = load_objectif_recouvrement(year, month)
    rows = saved["rows"] if saved else []
    meta = saved["meta"] if saved else None
    return {
        "period": {"year": year, "month": month},
        "count": len(rows),
        "snapshot": meta,
        "warning": None if saved else "L'objectif de ce mois n'est pas encore enregistré. Il est figé le 1er du mois.",
        "rows": rows,
    }
