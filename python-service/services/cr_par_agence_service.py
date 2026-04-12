"""
Service CR par Agence — données pré-agrégées DASH (DASH_CR_PAR_AGENCE).
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from database.oracle import get_oracle_connection_cofina

logger = logging.getLogger(__name__)

# Filtre lot : aligné sur la requête métier (comparaison jour comme chaîne DD/MM/YYYY).
# PARENT_GL : comparaison via TO_CHAR pour gérer NUMBER / VARCHAR et espaces.
_SQL_CR_DASH = """
SELECT
    d.AC_BRANCH,
    d.BRANCH_NAME,
    d.PARENT_GL,
    d.SOLDE_OUVERTURE,
    d.SOLDE_MOIS,
    d.MONTANT,
    d.MIGRATION_DATE,
    d.MIGRATION_DATETIME,
    d.MIGRATION_DATE_MINUS1
FROM DASH_CR_PAR_AGENCE d
WHERE d.MIGRATION_DATETIME = (
    SELECT MAX(t.MIGRATION_DATETIME)
    FROM DASH_CR_PAR_AGENCE t
    WHERE TO_CHAR(t.MIGRATION_DATE_MINUS1, 'DD/MM/YYYY') = :migration_date_minus1
)
AND TRIM(TO_CHAR(d.PARENT_GL)) IN ({parent_placeholders})
"""

# Si aucune ligne pour la date exacte (pas encore de snapshot ce jour-là) : dernier lot du mois.
_SQL_CR_DASH_BY_MONTH = """
SELECT
    d.AC_BRANCH,
    d.BRANCH_NAME,
    d.PARENT_GL,
    d.SOLDE_OUVERTURE,
    d.SOLDE_MOIS,
    d.MONTANT,
    d.MIGRATION_DATE,
    d.MIGRATION_DATETIME,
    d.MIGRATION_DATE_MINUS1
FROM DASH_CR_PAR_AGENCE d
WHERE d.MIGRATION_DATETIME = (
    SELECT MAX(t.MIGRATION_DATETIME)
    FROM DASH_CR_PAR_AGENCE t
    WHERE TO_CHAR(t.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
AND TRIM(TO_CHAR(d.PARENT_GL)) IN ({parent_placeholders})
"""


def _month_year_from_dd_mm_yyyy(date_to: str) -> str:
    """'31/03/2026' -> '03/2026'."""
    s = (date_to or "").strip()
    parts = s.split("/")
    if len(parts) != 3:
        return ""
    try:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        datetime(y, m, d)
        return f"{m:02d}/{y}"
    except (ValueError, TypeError):
        return ""


def _serialize_cell(val: Any) -> Any:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    return val


def _row_to_dict(columns: List[str], row: tuple) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for col, cell in zip(columns, row):
        key = col.upper() if isinstance(col, str) else col
        out[key] = _serialize_cell(cell)
    return out


def _execute_cr_query(
    conn,
    query_template: str,
    parent_placeholders: str,
    params: Dict[str, Any],
) -> Tuple[List[str], List[tuple]]:
    cursor = conn.cursor()
    query = query_template.format(parent_placeholders=parent_placeholders)
    cursor.execute(query, params)
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows


def get_cr_data_by_parent_gl(
    date_from: str,
    date_to: str,
    parent_gl_codes: List[str],
) -> List[Dict]:
    """
    Récupère les montants CR par agence depuis DASH_CR_PAR_AGENCE.

    Lot : MAX(MIGRATION_DATETIME) parmi les lignes dont la date (J-1 DASH) correspond à
    ``date_to`` (DD/MM/YYYY), via TO_CHAR comme en SQL métier.

    Si aucune ligne pour cette date, repli : dernier lot du mois calendaire de ``date_to``
    (MM/YYYY), comme pour les autres écrans DASH.

    Args:
        date_from: compatibilité API — non utilisé pour le filtre DASH.
        date_to: date cible du snapshot DASH (DD/MM/YYYY).
        parent_gl_codes: liste des PARENT_GL à filtrer.

    Returns:
        Lignes AC_BRANCH, BRANCH_NAME, PARENT_GL, SOLDE_*, MONTANT, MIGRATION_*.
    """
    _ = date_from
    if not parent_gl_codes:
        return []

    codes = [str(c).strip() for c in parent_gl_codes if str(c).strip()]
    if not codes:
        return []

    migration_key = (date_to or "").strip()
    month_year = _month_year_from_dd_mm_yyyy(migration_key)

    conn = get_oracle_connection_cofina()
    try:
        parent_placeholders = ", ".join([f":p{i}" for i in range(len(codes))])
        base_params: Dict[str, Any] = {"migration_date_minus1": migration_key}
        for i, c in enumerate(codes):
            base_params[f"p{i}"] = c

        logger.info(
            "CR par Agence DASH — date=%s, %s parent GL",
            migration_key,
            len(codes),
        )

        columns, rows = _execute_cr_query(conn, _SQL_CR_DASH, parent_placeholders, base_params)
        out = [_row_to_dict(columns, row) for row in rows]

        if not out and month_year:
            logger.warning(
                "CR par Agence DASH — 0 ligne pour la date %s, repli mois %s",
                migration_key,
                month_year,
            )
            params_m = {f"p{i}": codes[i] for i in range(len(codes))}
            params_m["month_year"] = month_year
            columns, rows = _execute_cr_query(
                conn, _SQL_CR_DASH_BY_MONTH, parent_placeholders, params_m
            )
            out = [_row_to_dict(columns, row) for row in rows]

        logger.info("CR par Agence DASH — %s lignes", len(out))
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
