"""
Sauvegarde New Deal : exécute la requête Flexcube et matérialise en SQLite local.

"""
from __future__ import annotations

import logging
import re
import sqlite3
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.oracle_pool import get_pool_flexcube

logger = logging.getLogger(__name__)

TABLE_NAME = "NEW_DEAL"
_PY_ROOT = Path(__file__).resolve().parent.parent.parent
SQL_PATH = _PY_ROOT / "requete mobile" / "new_deal" / "new_deal.sql"
LOCAL_DB_PATH = _PY_ROOT / "data" / "new_deal_local.db"

_CALL_TIMEOUT_MS = 3_600_000  # 1 h

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS new_deal_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_agence TEXT,
    nom_agence TEXT,
    no_pret TEXT,
    matricule_client TEXT,
    nom_client TEXT,
    compte TEXT,
    amount_financed REAL,
    field_char_2 TEXT,
    ui_dr_prod_ac TEXT,
    trn_dt TEXT
);

CREATE INDEX IF NOT EXISTS idx_new_deal_agence
    ON new_deal_rows(code_agence);

CREATE INDEX IF NOT EXISTS idx_new_deal_trn
    ON new_deal_rows(trn_dt);

CREATE TABLE IF NOT EXISTS new_deal_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL
);
"""


def _qualify_flexcube(sql: str) -> str:
    sql = re.sub(
        r"(?i)(?<!CFSFCUBS145\.)\bSTTM_CUSTOMER\b",
        "CFSFCUBS145.STTM_CUSTOMER",
        sql,
    )
    sql = re.sub(
        r"(?i)(?<!CFSFCUBS145\.)\bCLTB_ACCOUNT_MASTER\b",
        "CFSFCUBS145.CLTB_ACCOUNT_MASTER",
        sql,
    )
    sql = re.sub(
        r"(?i)(?<!CFSFCUBS145\.)\bacvw_all_ac_entries\b",
        "CFSFCUBS145.acvw_all_ac_entries",
        sql,
    )
    sql = re.sub(
        r"(?i)(?<!CFSFCUBS145\.)\bSTTM_BRANCH\b",
        "CFSFCUBS145.STTM_BRANCH",
        sql,
    )
    return sql


def _load_select_sql() -> str:
    if not SQL_PATH.is_file():
        raise FileNotFoundError(f"Script introuvable: {SQL_PATH}")
    raw = SQL_PATH.read_text(encoding="utf-8")
    match = re.search(r"(?is)\bCREATE\s+TABLE\b", raw)
    if not match:
        raise ValueError(f"Aucun CREATE TABLE trouvé dans {SQL_PATH}")
    sql = raw[match.start():].strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    # CREATE TABLE … AS <requête> → ne garder que la requête
    sql = re.sub(r"(?is)^CREATE\s+TABLE\s+\S+\s+AS\s*", "", sql).strip()
    return _qualify_flexcube(sql)


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


def _normalize_row(cols: List[str], row: tuple) -> Tuple:
    raw = {cols[i]: _serialize_cell(row[i]) for i in range(len(cols))}
    # Colonnes Oracle (aliases CTAS / SELECT)
    def pick(*names: str) -> Any:
        for n in names:
            if n in raw:
                return raw[n]
            up = n.upper()
            for k, v in raw.items():
                if k.upper().replace(" ", "_") == up.replace(" ", "_"):
                    return v
                if k.upper() == up:
                    return v
        # match with spaces stripped
        targets = {n.upper().replace(" ", "") for n in names}
        for k, v in raw.items():
            if k.upper().replace(" ", "") in targets:
                return v
        return None

    return (
        pick("CODE_AGENCE", "CODE AGENCE"),
        pick("NOM_AGENCE", "NOM AGENCE"),
        pick("NO_PRET", "NO PRET"),
        pick("MATRICULE_CLIENT", "MATRICULE CLIENT"),
        pick("NOM_CLIENT", "NOM CLIENT"),
        pick("COMPTE"),
        pick("AMOUNT_FINANCED"),
        pick("FIELD_CHAR_2"),
        pick("UI_DR_PROD_AC"),
        pick("TRN_DT"),
    )


def _sqlite_connect() -> sqlite3.Connection:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LOCAL_DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def init_new_deal_local_db() -> None:
    with _sqlite_connect() as conn:
        conn.executescript(_SQLITE_DDL)
        # Migration éventuelle depuis l'ancien nom de table
        try:
            cols = conn.execute("PRAGMA table_info(sv_deblocages_hors_client_nafa)").fetchall()
            if cols:
                count_new = conn.execute("SELECT COUNT(*) FROM new_deal_rows").fetchone()[0]
                if count_new == 0:
                    conn.execute(
                        """
                        INSERT INTO new_deal_rows (
                            code_agence, nom_agence, no_pret, matricule_client, nom_client,
                            compte, amount_financed, field_char_2, ui_dr_prod_ac, trn_dt
                        )
                        SELECT
                            code_agence, nom_agence, no_pret, matricule_client, nom_client,
                            compte, amount_financed, field_char_2, ui_dr_prod_ac, trn_dt
                        FROM sv_deblocages_hors_client_nafa
                        """
                    )
                conn.execute("DROP TABLE IF EXISTS sv_deblocages_hors_client_nafa")
            meta_old = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sv_deblocages_meta'"
            ).fetchone()
            if meta_old:
                count_meta = conn.execute("SELECT COUNT(*) FROM new_deal_meta").fetchone()[0]
                if count_meta == 0:
                    conn.execute(
                        """
                        INSERT INTO new_deal_meta (
                            id, refreshed_at, row_count, status, error_message, elapsed_seconds
                        )
                        SELECT id, refreshed_at, row_count, status, error_message, elapsed_seconds
                        FROM sv_deblocages_meta
                        """
                    )
                conn.execute("DROP TABLE IF EXISTS sv_deblocages_meta")
        except Exception:
            pass
        conn.commit()


def _set_meta(
    conn: sqlite3.Connection,
    *,
    status: str,
    row_count: int = 0,
    error_message: Optional[str] = None,
    elapsed_seconds: Optional[float] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO new_deal_meta (id, refreshed_at, row_count, status, error_message, elapsed_seconds)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds
        """,
        (
            datetime.utcnow().isoformat(timespec="seconds") + "Z",
            row_count,
            status,
            error_message,
            elapsed_seconds,
        ),
    )


def refresh_new_deal_snapshot() -> Dict[str, Any]:
    """
    Exécute la requête New Deal sur Flexcube et remplace le snapshot SQLite local.
    """
    select_sql = _load_select_sql()
    started = time.monotonic()
    init_new_deal_local_db()

    ora_cur = None
    try:
        pool = get_pool_flexcube()
        with pool.get_connection_context() as ora_conn:
            if hasattr(ora_conn, "callTimeout"):
                ora_conn.callTimeout = _CALL_TIMEOUT_MS

            ora_cur = ora_conn.cursor()
            try:
                logger.info("New Deal: exécution requête Flexcube…")
                ora_cur.execute(select_sql)
                cols = [d[0] for d in ora_cur.description]

                batch: List[Tuple] = []
                total = 0
                fetch_size = 1000

                with _sqlite_connect() as local:
                    local.execute("DELETE FROM new_deal_rows")
                    insert_sql = """
                INSERT INTO new_deal_rows (
                    code_agence, nom_agence, no_pret, matricule_client, nom_client,
                    compte, amount_financed, field_char_2, ui_dr_prod_ac, trn_dt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
                    while True:
                        rows = ora_cur.fetchmany(fetch_size)
                        if not rows:
                            break
                        batch = [_normalize_row(cols, r) for r in rows]
                        local.executemany(insert_sql, batch)
                        total += len(batch)

                    elapsed = round(time.monotonic() - started, 1)
                    _set_meta(
                        local,
                        status="success",
                        row_count=total,
                        elapsed_seconds=elapsed,
                    )
                    local.commit()
            finally:
                try:
                    ora_cur.close()
                except Exception:
                    pass
                ora_cur = None

            logger.info(
                "New Deal snapshot OK (%s lignes, %.1fs) → %s",
                total,
                elapsed,
                LOCAL_DB_PATH,
            )
            return {
                "status": "success",
                "table": TABLE_NAME,
                "storage": "sqlite",
                "path": str(LOCAL_DB_PATH),
                "row_count": total,
                "elapsed_seconds": elapsed,
            }
    except Exception as exc:
        logger.error("Échec rafraîchissement New Deal: %s", exc, exc_info=True)
        try:
            with _sqlite_connect() as local:
                _set_meta(local, status="error", error_message=str(exc))
                local.commit()
        except Exception:
            pass
        raise
    finally:
        if ora_cur is not None:
            try:
                ora_cur.close()
            except Exception:
                pass


def read_new_deal_rows(limit: Optional[int] = None) -> Dict[str, Any]:
    """Lecture du snapshot SQLite New Deal."""
    init_new_deal_local_db()
    with _sqlite_connect() as conn:
        meta = conn.execute(
            "SELECT refreshed_at, row_count, status, error_message, elapsed_seconds "
            "FROM new_deal_meta WHERE id = 1"
        ).fetchone()

        sql = """
            SELECT
                code_agence, nom_agence, no_pret, matricule_client, nom_client,
                compte, amount_financed, field_char_2, ui_dr_prod_ac, trn_dt
            FROM new_deal_rows
            ORDER BY trn_dt DESC, nom_agence, no_pret
        """
        params: Tuple = ()
        if limit is not None and int(limit) > 0:
            sql += " LIMIT ?"
            params = (int(limit),)

        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        total_amount = sum(
            float(r["amount_financed"])
            for r in rows
            if r.get("amount_financed") is not None
        )

        result: Dict[str, Any] = {
            "data": rows,
            "count": len(rows),
            "total_amount": total_amount,
            "table": TABLE_NAME,
            "storage": "sqlite",
        }
        if meta:
            result["refreshed_at"] = meta["refreshed_at"]
            result["meta_status"] = meta["status"]
            if meta["status"] == "error" and meta["error_message"]:
                result["warning"] = meta["error_message"]
            elif not rows:
                result["warning"] = (
                    "Snapshot New Deal vide. Lancez le rafraîchissement "
                    "(06h/12h ou bouton Reconstruire)."
                )
        elif not rows:
            result["warning"] = (
                "Snapshot New Deal absent. Lancez le rafraîchissement "
                "(06h/12h ou bouton Reconstruire)."
            )
        return result


def get_new_deal_for_caf(
    caf_code: Optional[str],
    month: int,
    year: int,
) -> Dict[str, Any]:
    """
    New Deal filtré pour un CAF (FIELD_CHAR_2) et un mois calendaire.
    Source : snapshot SQLite (rafraîchi 06h / 12h).
    """
    code = str(caf_code or "").strip()
    if not code:
        return {
            "loan_count": 0.0,
            "monthly_volume": 0.0,
            "loans": [],
            "refreshed_at": None,
        }

    init_new_deal_local_db()
    month_prefix = f"{int(year):04d}-{int(month):02d}"
    with _sqlite_connect() as conn:
        meta = conn.execute(
            "SELECT refreshed_at, status FROM new_deal_meta WHERE id = 1"
        ).fetchone()
        cur = conn.execute(
            """
            SELECT
                code_agence, nom_agence, no_pret, matricule_client, nom_client,
                compte, amount_financed, field_char_2, ui_dr_prod_ac, trn_dt
            FROM new_deal_rows
            WHERE TRIM(COALESCE(field_char_2, '')) = ?
              AND substr(COALESCE(trn_dt, ''), 1, 7) = ?
            ORDER BY trn_dt DESC, no_pret
            """,
            (code, month_prefix),
        )
        rows = [dict(r) for r in cur.fetchall()]

    loans = [
        {
            "loan_number": r.get("no_pret"),
            "client_name": r.get("nom_client"),
            "client_id": r.get("matricule_client"),
            "agency_code": r.get("code_agence"),
            "agency_name": r.get("nom_agence"),
            "outstanding": r.get("amount_financed"),
            "disbursement_date": r.get("trn_dt"),
            "account": r.get("compte"),
            "caf_code": r.get("field_char_2"),
        }
        for r in rows
    ]
    volume = sum(
        float(r["amount_financed"])
        for r in rows
        if r.get("amount_financed") is not None
    )
    return {
        "loan_count": float(len(loans)),
        "monthly_volume": float(volume),
        "loans": loans,
        "refreshed_at": meta["refreshed_at"] if meta else None,
        "meta_status": meta["status"] if meta else None,
    }
