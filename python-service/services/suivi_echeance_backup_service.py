"""
Sauvegarde du suivi échéance, rafraîchie toutes les 30 minutes.

Chaque passe réussie remplace entièrement la précédente dans SQLite
(database/database.sqlite). Une seule photo est conservée.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from database.oracle_pool import get_pool_flexcube
from services.suivi_echeance_service import _SQL_PATH, _normalize_row
from services.suivi_production_backup_service import database_paths

logger = logging.getLogger(__name__)

_CALL_TIMEOUT_MS = 3_600_000
_refresh_lock = threading.Lock()

ROW_COLUMNS: Tuple[str, ...] = (
    "code_agence",
    "nom_agence",
    "no_pret",
    "matricule_client",
    "nom_client",
    "compte",
    "type_pret",
    "date_deblocage",
    "montant_capital_accorde",
    "encours_total",
    "encours_sain",
    "encours_impaye",
    "pourcentage_remboursement",
    "statut_pret",
    "statut_declassement",
    "code_gestion_pret",
    "charge_affaire",
    "montant_depot_garantie_initial",
    "solde_depot_garantie",
    "schedule_due_date",
    "numero_echeance",
    "solde_cpte",
    "mt_global_due_a_date",
    "etat_exigible_m_1",
    "total_charge",
    "montant_echeance_m",
    "montant_echeance_paye",
    "montant_echeance_impy",
    "penalite",
    "exigible_ech",
    "status_ech",
)

_SQLITE_DDL = f"""
CREATE TABLE IF NOT EXISTS suivi_echeance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jour TEXT NOT NULL,
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    {", ".join(f"{column} TEXT" for column in ROW_COLUMNS)}
);

CREATE INDEX IF NOT EXISTS idx_suivi_echeance_jour
    ON suivi_echeance(jour);

CREATE INDEX IF NOT EXISTS idx_suivi_echeance_periode
    ON suivi_echeance(annee, mois, jour);

CREATE INDEX IF NOT EXISTS idx_suivi_echeance_pret
    ON suivi_echeance(jour, no_pret);

CREATE INDEX IF NOT EXISTS idx_suivi_echeance_agence
    ON suivi_echeance(jour, code_agence);

CREATE TABLE IF NOT EXISTS suivi_echeance_meta (
    jour TEXT PRIMARY KEY,
    annee INTEGER,
    mois INTEGER,
    date_debut TEXT,
    date_fin TEXT,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL
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


def init_suivi_echeance_local_db() -> None:
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
    jour: str,
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
        INSERT INTO suivi_echeance_meta (
            jour, annee, mois, date_debut, date_fin, refreshed_at, row_count,
            status, error_message, elapsed_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(jour) DO UPDATE SET
            annee = excluded.annee,
            mois = excluded.mois,
            date_debut = COALESCE(excluded.date_debut, suivi_echeance_meta.date_debut),
            date_fin = COALESCE(excluded.date_fin, suivi_echeance_meta.date_fin),
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds
        """,
        (
            jour,
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


def get_suivi_echeance_snapshot_meta(jour: Optional[str] = None) -> Any:
    init_suivi_echeance_local_db()
    with _connect() as conn:
        if jour is None:
            rows = conn.execute(
                """
                SELECT jour, annee, mois, date_debut, date_fin, refreshed_at,
                       row_count, status, error_message, elapsed_seconds
                FROM suivi_echeance_meta
                ORDER BY jour DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
        row = conn.execute(
            """
            SELECT jour, annee, mois, date_debut, date_fin, refreshed_at,
                   row_count, status, error_message, elapsed_seconds
            FROM suivi_echeance_meta
            WHERE jour = ?
            """,
            (jour,),
        ).fetchone()
        return dict(row) if row else None


def latest_snapshot_for_month(year: int, month: int) -> Optional[dict]:
    init_suivi_echeance_local_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT jour, annee, mois, date_debut, date_fin, refreshed_at,
                   row_count, status, error_message, elapsed_seconds
            FROM suivi_echeance_meta
            WHERE annee = ? AND mois = ? AND status = 'success'
            ORDER BY jour DESC
            LIMIT 1
            """,
            (int(year), int(month)),
        ).fetchone()
        return dict(row) if row else None


def has_snapshot_for_day(jour: date) -> bool:
    meta = get_suivi_echeance_snapshot_meta(jour.isoformat())
    return bool(meta and meta.get("status") == "success")


def load_suivi_echeance_rows(year: int, month: int) -> Optional[dict]:
    """
    Lignes de la photo la plus récente du mois.
    None s'il n'y a pas encore de sauvegarde réussie.
    """
    meta = latest_snapshot_for_month(year, month)
    if not meta:
        return None
    init_suivi_echeance_local_db()
    columns = ", ".join(ROW_COLUMNS)
    with _connect() as conn:
        found = conn.execute(
            f"""
            SELECT {columns}
            FROM suivi_echeance
            WHERE jour = ?
            """,
            (meta["jour"],),
        ).fetchall()
    rows = []
    for item in found:
        raw = {column.upper(): item[column] for column in ROW_COLUMNS}
        rows.append(_normalize_row(raw))
    return {"meta": meta, "rows": rows}


def _refresh_day(jour: date, year: int, month: int) -> Dict[str, Any]:
    start, end = _month_window(year, month)
    jour_key = jour.isoformat()
    init_suivi_echeance_local_db()
    started = time.monotonic()

    logger.info(
        "Suivi échéance : sauvegarde %s pour %02d/%s (%s → %s)",
        jour_key,
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
                cursor.execute(
                    _load_sql(),
                    {"date_debut": start, "date_fin": end},
                )
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
                        fetched.append(
                            (jour_key, year, month, *(values[column] for column in ROW_COLUMNS))
                        )
            finally:
                cursor.close()

        placeholders = ", ".join(["?"] * (3 + len(ROW_COLUMNS)))
        insert_sql = (
            f"INSERT INTO suivi_echeance (jour, annee, mois, {', '.join(ROW_COLUMNS)}) "
            f"VALUES ({placeholders})"
        )
        elapsed = round(time.monotonic() - started, 1)
        stored = [str(path) for path in database_paths()]
        for path in database_paths():
            with _connect(path) as local:
                local.execute("BEGIN")
                local.execute("DELETE FROM suivi_echeance")
                local.execute("DELETE FROM suivi_echeance_meta")
                local.executemany(insert_sql, fetched)
                _set_meta(
                    local,
                    jour=jour_key,
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
            "Suivi échéance %s : %s lignes en %.1fs → %s",
            jour_key,
            len(fetched),
            elapsed,
            ", ".join(stored),
        )
        return {
            "status": "success",
            "jour": jour_key,
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
            "Sauvegarde suivi échéance %s échouée, photo précédente conservée: %s",
            jour_key,
            exc,
            exc_info=True,
        )
        raise


def refresh_suivi_echeance_day(
    jour: Optional[date] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """Photo du jour pour le mois indiqué (mois en cours par défaut)."""
    jour = jour or date.today()
    year = int(year or jour.year)
    month = int(month or jour.month)
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "already_running", "jour": jour.isoformat()}
    try:
        return _refresh_day(jour, year, month)
    finally:
        _refresh_lock.release()


def refresh_suivi_echeance_pending(today: Optional[date] = None) -> Dict[str, Any]:
    today = today or date.today()
    if has_snapshot_for_day(today):
        return {"status": "success", "jour": today.isoformat(), "reason": "already_fresh"}
    return refresh_suivi_echeance_day(today)
