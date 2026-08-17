"""
Snapshot quotidien de la Collecte d'épargne à vue (Flexcube → SQLite).

Le job du matin (06:00) matérialise :
  - les lignes brutes Flexcube (collecte_epv_vue_rows)
  - des tables d'affichage pré-agrégées (territoires / agences / CAFs / clients)
  - un payload JSON prêt à servir (collecte_epv_vue_display)

L'API lit le payload d'affichage sans reconstruire la hiérarchie à chaque ouverture.
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

-- Tables d'affichage pré-agrégées (servies au dashboard)
CREATE TABLE IF NOT EXISTS collecte_epv_vue_territoires (
    month_key TEXT NOT NULL,
    territory_key TEXT NOT NULL,
    name TEXT,
    cum_montant_finance REAL,
    encours_credit REAL,
    mt_echeance REAL,
    objectif REAL,
    collecte_m REAL,
    total_depot REAL,
    tro REAL,
    PRIMARY KEY (month_key, territory_key)
);

CREATE TABLE IF NOT EXISTS collecte_epv_vue_agences (
    month_key TEXT NOT NULL,
    territory_key TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    branch_name TEXT,
    cum_montant_finance REAL,
    encours_credit REAL,
    mt_echeance REAL,
    objectif REAL,
    collecte_m REAL,
    total_depot REAL,
    tro REAL,
    PRIMARY KEY (month_key, branch_code)
);

CREATE INDEX IF NOT EXISTS idx_collecte_epv_agences_terr
    ON collecte_epv_vue_agences(month_key, territory_key);

CREATE TABLE IF NOT EXISTS collecte_epv_vue_cafs (
    month_key TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    code_caf TEXT NOT NULL,
    charge_affaire TEXT,
    cum_montant_finance REAL,
    encours_credit REAL,
    mt_echeance REAL,
    objectif REAL,
    collecte_m REAL,
    total_depot REAL,
    tro REAL,
    PRIMARY KEY (month_key, branch_code, code_caf)
);

CREATE INDEX IF NOT EXISTS idx_collecte_epv_cafs_branch
    ON collecte_epv_vue_cafs(month_key, branch_code);

CREATE TABLE IF NOT EXISTS collecte_epv_vue_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_key TEXT NOT NULL,
    branch_code TEXT,
    branch_name TEXT,
    code_caf TEXT,
    charge_affaire TEXT,
    matricule_client TEXT,
    numero_compte TEXT,
    nom_client TEXT,
    cum_montant_finance REAL,
    encours_credit REAL,
    objectif REAL,
    mt_echeance REAL,
    total_depot REAL,
    collecte_m REAL,
    tro REAL
);

CREATE INDEX IF NOT EXISTS idx_collecte_epv_clients_month
    ON collecte_epv_vue_clients(month_key, branch_code, code_caf);

-- Payload JSON prêt à servir (une ligne par mois)
CREATE TABLE IF NOT EXISTS collecte_epv_vue_display (
    month_key TEXT PRIMARY KEY,
    refreshed_at TEXT,
    status TEXT,
    row_count INTEGER,
    payload_json TEXT NOT NULL
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


_schema_ready = False


def init_collecte_epv_vue_local_db() -> None:
    """Le DDL est rejoué une seule fois par process."""
    global _schema_ready
    if _schema_ready:
        return
    conn = _connect_local()
    try:
        conn.executescript(_SQLITE_DDL)
        conn.commit()
        _schema_ready = True
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


def has_collecte_display(month: int, year: int) -> bool:
    init_collecte_epv_vue_local_db()
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT status, length(payload_json) AS payload_len
            FROM collecte_epv_vue_display
            WHERE month_key = ?
            """,
            (key,),
        ).fetchone()
        return bool(row and row["status"] == "ok" and (row["payload_len"] or 0) > 2)
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


def load_collecte_display_payload(month: int, year: int) -> Optional[Dict[str, Any]]:
    """Charge le payload d'affichage pré-calculé (None si absent / invalide)."""
    if not has_collecte_display(month, year):
        return None
    key = month_key(month, year)
    conn = _connect_local()
    try:
        row = conn.execute(
            """
            SELECT payload_json FROM collecte_epv_vue_display
            WHERE month_key = ? AND status = 'ok'
            """,
            (key,),
        ).fetchone()
        if not row or not row["payload_json"]:
            return None
        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict) or "hierarchicalData" not in payload:
            return None
        return payload
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Payload display invalide pour %s: %s", key, exc)
        return None
    finally:
        conn.close()


def _clear_display_tables(conn: sqlite3.Connection, key: str) -> None:
    for table in (
        "collecte_epv_vue_territoires",
        "collecte_epv_vue_agences",
        "collecte_epv_vue_cafs",
        "collecte_epv_vue_clients",
        "collecte_epv_vue_display",
    ):
        conn.execute(f"DELETE FROM {table} WHERE month_key = ?", (key,))


def _flatten_hierarchy_for_tables(
    hierarchical: Dict[str, Any],
    key: str,
) -> tuple[list, list, list, list]:
    """Extrait les tuples INSERT depuis hierarchicalData."""
    territoires: list = []
    agences: list = []
    cafs: list = []
    clients: list = []

    territoires_map = (hierarchical or {}).get("TERRITOIRE") or {}
    for territory_key, territory in territoires_map.items():
        totals = territory.get("totals") or {}
        territoires.append(
            (
                key,
                territory_key,
                territory.get("name") or territory_key,
                _f(totals.get("cumMontantFinance")),
                _f(totals.get("encoursCredit")),
                _f(totals.get("mtEcheance")),
                _f(totals.get("objectif")),
                _f(totals.get("collecteM")),
                _f(totals.get("totalDepot")),
                _f(totals.get("tro")),
            )
        )
        for agency in territory.get("agencies") or []:
            branch_code = str(agency.get("BRANCH_CODE") or agency.get("branch_code") or "")
            branch_name = agency.get("name") or agency.get("BRANCH_NAME") or branch_code
            agences.append(
                (
                    key,
                    territory_key,
                    branch_code,
                    branch_name,
                    _f(agency.get("cumMontantFinance")),
                    _f(agency.get("encoursCredit")),
                    _f(agency.get("mtEcheance")),
                    _f(agency.get("objectif")),
                    _f(agency.get("collecteM")),
                    _f(agency.get("totalDepot")),
                    _f(agency.get("tro")),
                )
            )
            for caf in agency.get("chargeAffaireDetails") or []:
                code_caf = str(caf.get("codeGestion") or caf.get("CODE_CAF") or "")
                cafs.append(
                    (
                        key,
                        branch_code,
                        code_caf,
                        caf.get("chargeAffaire") or caf.get("CHARGE_AFFAIRE") or "",
                        _f(caf.get("cumMontantFinance")),
                        _f(caf.get("encoursCredit")),
                        _f(caf.get("mtEcheance")),
                        _f(caf.get("objectif")),
                        _f(caf.get("collecteM")),
                        _f(caf.get("totalDepot")),
                        _f(caf.get("tro")),
                    )
                )
                for client in caf.get("clients") or []:
                    clients.append(
                        (
                            key,
                            branch_code,
                            branch_name,
                            code_caf,
                            client.get("CHARGE_AFFAIRE") or caf.get("chargeAffaire") or "",
                            str(client.get("MATRICULE_CLIENT") or ""),
                            str(client.get("NUMERO_COMPTE") or ""),
                            client.get("NOM_CLIENT") or "",
                            _f(client.get("CUM_MONTANT_FINANCE")),
                            _f(client.get("CUM_ENCOURS_CREDIT")),
                            _f(client.get("OBJ_COL_EPV_VUE")),
                            _f(client.get("MONTANT_ECHEANCE")),
                            _f(client.get("TOTAL_DEPOT")),
                            _f(client.get("COL_EP_VUE")),
                            _f(client.get("tro")),
                        )
                    )

    return territoires, agences, cafs, clients


def materialize_collecte_display(
    month: int,
    year: int,
    *,
    data_source: str = "snapshot",
) -> Dict[str, Any]:
    """
    Construit les tables d'affichage + payload JSON à partir des lignes brutes
    déjà stockées (objectifs figés appliqués).
    """
    # Import différé pour éviter un cycle avec collecte_epargne_a_vue_service
    from services.collecte_epargne_a_vue_service import (
        _build_hierarchical,
        _f as svc_f,
        _tro,
    )
    from services.objectif_epv_vue_backup_service import apply_frozen_objectifs

    m = int(month)
    y = int(year)
    key = month_key(m, y)
    init_collecte_epv_vue_local_db()
    started = time.monotonic()

    if not has_collecte_snapshot(m, y):
        raise ValueError(f"Pas de lignes brutes pour matérialiser l'affichage {key}")

    rows = load_collecte_snapshot_rows(m, y)
    rows, objectifs_meta = apply_frozen_objectifs(rows, m, y)
    hierarchical = _build_hierarchical(rows)
    snapshot_meta = get_collecte_snapshot_meta(m, y) or {}
    date_debut, date_fin_exclusive = _month_bounds_iso(m, y)
    date_debut = snapshot_meta.get("date_debut") or date_debut
    date_fin_exclusive = snapshot_meta.get("date_fin_exclusive") or date_fin_exclusive

    seen = set()
    total_depot = total_col = total_echeance = 0.0
    total_objectif = sum(svc_f(r.get("obj_col_epv_vue")) for r in rows)
    total_finance = sum(svc_f(r.get("cum_montant_finance")) for r in rows)
    total_encours = sum(svc_f(r.get("cum_encours_credit")) for r in rows)
    for r in rows:
        mat = str(r.get("matricule_client") or "")
        if mat and mat in seen:
            continue
        if mat:
            seen.add(mat)
        total_depot += svc_f(r.get("total_depot"))
        total_col += svc_f(r.get("col_ep_vue"))
        total_echeance += svc_f(r.get("montant_echeance"))

    elapsed = time.monotonic() - started
    refreshed_at = datetime.now().isoformat(timespec="seconds")
    payload = {
        "data": [],
        "hierarchicalData": hierarchical,
        "count": len(rows),
        "month": m,
        "year": y,
        "date_debut": date_debut,
        "date_fin_exclusive": date_fin_exclusive,
        "elapsed_seconds": round(elapsed, 2),
        "data_source": data_source,
        "data_snapshot": snapshot_meta,
        **objectifs_meta,
        "totals": {
            "cum_montant_finance": total_finance,
            "cum_encours_credit": total_encours,
            "obj_col_epv_vue": total_objectif,
            "montant_echeance": total_echeance,
            "total_depot": total_depot,
            "col_ep_vue": total_col,
            "tro": _tro(total_col, total_objectif),
        },
        "display_cached": True,
    }

    territoires, agences, cafs, clients = _flatten_hierarchy_for_tables(hierarchical, key)

    local = _connect_local()
    try:
        _clear_display_tables(local, key)
        local.executemany(
            """
            INSERT INTO collecte_epv_vue_territoires (
                month_key, territory_key, name,
                cum_montant_finance, encours_credit, mt_echeance,
                objectif, collecte_m, total_depot, tro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            territoires,
        )
        local.executemany(
            """
            INSERT INTO collecte_epv_vue_agences (
                month_key, territory_key, branch_code, branch_name,
                cum_montant_finance, encours_credit, mt_echeance,
                objectif, collecte_m, total_depot, tro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            agences,
        )
        local.executemany(
            """
            INSERT INTO collecte_epv_vue_cafs (
                month_key, branch_code, code_caf, charge_affaire,
                cum_montant_finance, encours_credit, mt_echeance,
                objectif, collecte_m, total_depot, tro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cafs,
        )
        local.executemany(
            """
            INSERT INTO collecte_epv_vue_clients (
                month_key, branch_code, branch_name, code_caf, charge_affaire,
                matricule_client, numero_compte, nom_client,
                cum_montant_finance, encours_credit, objectif,
                mt_echeance, total_depot, collecte_m, tro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            clients,
        )
        local.execute(
            """
            INSERT INTO collecte_epv_vue_display (
                month_key, refreshed_at, status, row_count, payload_json
            ) VALUES (?, ?, 'ok', ?, ?)
            """,
            (
                key,
                refreshed_at,
                len(rows),
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        local.commit()
    finally:
        local.close()

    logger.info(
        "✅ Affichage collecte EPV vue %s matérialisé: %s terr. / %s ag. / %s CAF / %s clients (%.2fs)",
        key,
        len(territoires),
        len(agences),
        len(cafs),
        len(clients),
        elapsed,
    )
    return payload


def refresh_collecte_epv_vue_snapshot(
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """Exécute la requête lourde Flexcube, remplace le snapshot, matérialise l'affichage."""
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
            "✅ Snapshot lignes collecte EPV vue %s: %s lignes en %.1fs",
            key,
            len(rows),
            elapsed,
        )

        # Tables d'affichage + payload prêt à servir
        materialize_collecte_display(m, y, data_source="refreshed")

        return {
            "success": True,
            "month_key": key,
            "month": m,
            "year": y,
            "row_count": len(rows),
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "refreshed_at": refreshed_at,
            "date_debut": date_debut,
            "date_fin_exclusive": date_fin_exclusive,
            "display_ready": True,
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
