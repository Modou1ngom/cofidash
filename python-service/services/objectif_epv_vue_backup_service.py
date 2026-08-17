"""
Sauvegarde mensuelle des objectifs COLLECTE ÉPARGNE À VUE (OBJ_COL_EPV_VUE).

Table SQLite locale : une photo par mois (month_key = YYYY-MM), typiquement
prise le 1er du mois pour figer les objectifs pendant tout le mois.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.oracle_pool import get_pool_flexcube
from services.objectif_epv_vue_query import OBJECTIF_EPV_VUE_SNAPSHOT_QUERY

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = _PY_ROOT / "data" / "objectif_epv_vue_local.db"
_CALL_TIMEOUT_MS = 300_000

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS objectif_epv_vue_rows (
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
    obj_col_epv_vue REAL
);

CREATE INDEX IF NOT EXISTS idx_obj_epv_month
    ON objectif_epv_vue_rows(month_key);

CREATE INDEX IF NOT EXISTS idx_obj_epv_key
    ON objectif_epv_vue_rows(month_key, code_agence, code_caf, matricule_client, numero_compte);

CREATE TABLE IF NOT EXISTS objectif_epv_vue_meta (
    month_key TEXT PRIMARY KEY,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL
);
"""


def month_key(month: int, year: int) -> str:
    return f"{int(year):04d}-{int(month):02d}"


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


def init_objectif_epv_vue_local_db() -> None:
    conn = _connect_local()
    try:
        conn.executescript(_SQLITE_DDL)
        conn.commit()
    finally:
        conn.close()


def has_objectif_snapshot(month: int, year: int) -> bool:
    init_objectif_epv_vue_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            "SELECT status, row_count FROM objectif_epv_vue_meta WHERE month_key = ?",
            (key,),
        ).fetchone()
        return bool(row and row["status"] == "ok" and (row["row_count"] or 0) > 0)
    finally:
        conn.close()


def get_objectif_snapshot_meta(month: int, year: int) -> Optional[Dict[str, Any]]:
    init_objectif_epv_vue_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT month_key, refreshed_at, row_count, status, error_message, elapsed_seconds
            FROM objectif_epv_vue_meta
            WHERE month_key = ?
            """,
            (key,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _fetch_objectifs_from_flexcube() -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _CALL_TIMEOUT_MS
            cursor.execute(OBJECTIF_EPV_VUE_SNAPSHOT_QUERY)
            columns = [str(col[0]).lower() for col in cursor.description]
            rows: List[Dict[str, Any]] = []
            for raw in cursor.fetchall():
                row = {
                    columns[i]: _serialize_cell(raw[i]) for i in range(len(columns))
                }
                rows.append(row)
            return rows
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
) -> None:
    conn.execute(
        """
        INSERT INTO objectif_epv_vue_meta (
            month_key, refreshed_at, row_count, status, error_message, elapsed_seconds
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(month_key) DO UPDATE SET
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds
        """,
        (key, refreshed_at, row_count, status, error_message, elapsed_seconds),
    )


def refresh_objectif_epv_vue_snapshot(
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Exécute la requête objectifs sur Flexcube et matérialise le mois dans SQLite.
    Remplace entièrement le snapshot du mois ciblé.
    """
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    if m < 1 or m > 12:
        raise ValueError(f"Mois invalide: {m}")

    key = month_key(m, y)
    init_objectif_epv_vue_local_db()
    started = time.monotonic()
    logger.info("📸 Snapshot objectifs EPV vue — mois %s", key)

    try:
        rows = _fetch_objectifs_from_flexcube()
        local = _connect_local()
        try:
            local.execute("DELETE FROM objectif_epv_vue_rows WHERE month_key = ?", (key,))
            local.executemany(
                """
                INSERT INTO objectif_epv_vue_rows (
                    month_key, code_agence, branch_name, code_caf, charge_affaire,
                    matricule_client, numero_compte, nom_client,
                    cum_montant_finance, cum_encours_credit, obj_col_epv_vue
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    )
                    for r in rows
                ],
            )
            elapsed = time.monotonic() - started
            _upsert_meta(
                local,
                key,
                refreshed_at=datetime.now().isoformat(timespec="seconds"),
                row_count=len(rows),
                status="ok",
                error_message=None,
                elapsed_seconds=round(elapsed, 2),
            )
            local.commit()
        finally:
            local.close()

        logger.info("✅ Snapshot objectifs EPV vue %s: %s lignes en %.1fs", key, len(rows), elapsed)

        # Si les lignes collecte existent déjà, recalculer les tables d'affichage
        # avec les nouveaux objectifs figés.
        try:
            from services.collecte_epargne_a_vue_backup_service import (
                has_collecte_snapshot,
                materialize_collecte_display,
            )

            if has_collecte_snapshot(m, y):
                materialize_collecte_display(m, y, data_source="snapshot")
                logger.info("♻️ Affichage collecte EPV vue rematérialisé après figement objectifs")
        except Exception as remat_exc:
            logger.warning(
                "Objectifs figés OK mais rematérialisation affichage échouée: %s",
                remat_exc,
            )

        return {
            "success": True,
            "month_key": key,
            "month": m,
            "year": y,
            "row_count": len(rows),
            "elapsed_seconds": round(elapsed, 2),
            "refreshed_at": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as exc:
        elapsed = time.monotonic() - started
        logger.error("❌ Snapshot objectifs EPV vue échoué (%s): %s", key, exc, exc_info=True)
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
            )
            local.commit()
        finally:
            local.close()
        raise


def load_objectif_snapshot_map(month: int, year: int) -> Dict[Tuple[str, str, str, str], float]:
    """
    Retourne un dict (code_agence, code_caf, matricule, compte) -> obj_col_epv_vue
    pour le mois demandé.
    """
    if not has_objectif_snapshot(month, year):
        return {}

    key = month_key(month, year)
    conn = _connect_local()
    try:
        rows = conn.execute(
            """
            SELECT code_agence, code_caf, matricule_client, numero_compte, obj_col_epv_vue
            FROM objectif_epv_vue_rows
            WHERE month_key = ?
            """,
            (key,),
        ).fetchall()
        out: Dict[Tuple[str, str, str, str], float] = {}
        for r in rows:
            k = (
                str(r["code_agence"] or "").strip(),
                str(r["code_caf"] or "").strip(),
                str(r["matricule_client"] or "").strip(),
                str(r["numero_compte"] or "").strip(),
            )
            out[k] = _f(r["obj_col_epv_vue"])
        return out
    finally:
        conn.close()


def apply_frozen_objectifs(
    rows: List[Dict[str, Any]],
    month: int,
    year: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Remplace OBJ_COL_EPV_VUE par la valeur figée du snapshot mensuel si disponible.
    Retourne (rows, meta_info).
    """
    meta = get_objectif_snapshot_meta(month, year) or {}
    snap = load_objectif_snapshot_map(month, year)
    if not snap:
        return rows, {
            "objectifs_source": "live",
            "objectifs_figes": False,
            "objectifs_snapshot": meta or None,
            "objectifs_applied": 0,
        }

    applied = 0
    for row in rows:
        k = (
            str(row.get("code_agence") or "").strip(),
            str(row.get("code_caf") or "").strip(),
            str(row.get("matricule_client") or "").strip(),
            str(row.get("numero_compte") or "").strip(),
        )
        if k in snap:
            row["obj_col_epv_vue"] = snap[k]
            applied += 1

    return rows, {
        "objectifs_source": "snapshot",
        "objectifs_figes": True,
        "objectifs_snapshot": meta,
        "objectifs_applied": applied,
        "objectifs_snapshot_rows": len(snap),
    }
