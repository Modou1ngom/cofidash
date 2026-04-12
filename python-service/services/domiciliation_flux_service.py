"""
Domiciliation de flux — jointure DASH_ETAT_CPT (J−1), DASH_TOMBE_MOIS (J−1), DASH_EXIGIBLE (M−1).
Même logique de lots MIGRATION_DATE_MINUS1 / MIGRATION_DATETIME que Volume DAT et Dépôt de garantie.
"""
import logging
from datetime import date as dt_date
from datetime import timedelta
from typing import Any, Dict, List, Optional

from database.oracle import get_oracle_connection_cofina
from services.volume_dat_service import (
    _ref_month_year,
    _week_range_dd_mm_yyyy,
)

logger = logging.getLogger(__name__)


def _prev_month_year_str(month: int, year: int) -> str:
    """Mois calendaire précédent au format MM/YYYY (pour DASH_EXIGIBLE M−1)."""
    if month == 1:
        return f"12/{year - 1}"
    return f"{month - 1:02d}/{year}"


def _rows_to_json_serializable(rows: List[dict]) -> List[dict]:
    out = []
    for row in rows:
        d = {}
        for k, v in row.items():
            if v is not None and hasattr(v, "isoformat"):
                try:
                    d[k] = v.isoformat()
                except Exception:
                    d[k] = str(v)
            else:
                d[k] = v
        out.append(d)
    return out


# --- Filtres « période courante » (ETAT_CPT + TOMBE) : identiques entre e et t ---
# Jour (mois en cours affiché = mois calendaire courant)
_SQL_ETAT_TOMBE_DAY = """
WHERE t.MIGRATION_DATE_MINUS1 = (
    SELECT MAX(d.MIGRATION_DATE_MINUS1)
    FROM DASH_ETAT_CPT d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'DD/MM/YYYY') = :migration_target
)
AND t.MIGRATION_DATETIME = (
    SELECT MAX(t2.MIGRATION_DATETIME)
    FROM DASH_ETAT_CPT t2
    WHERE t2.MIGRATION_DATE_MINUS1 = t.MIGRATION_DATE_MINUS1
)
"""

_SQL_ETAT_TOMBE_MONTH = """
WHERE t.MIGRATION_DATETIME = (
    SELECT MAX(t2.MIGRATION_DATETIME)
    FROM DASH_ETAT_CPT t2
    WHERE TO_CHAR(t2.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
"""

_SQL_ETAT_TOMBE_WEEK = """
WHERE t.MIGRATION_DATETIME = (
    SELECT MAX(t2.MIGRATION_DATETIME)
    FROM DASH_ETAT_CPT t2
    WHERE TRUNC(t2.MIGRATION_DATE_MINUS1) BETWEEN TO_DATE(:week_start, 'DD/MM/YYYY')
                                            AND TO_DATE(:week_end, 'DD/MM/YYYY')
)
"""

_SQL_ETAT_TOMBE_YEAR = """
WHERE t.MIGRATION_DATETIME = (
    SELECT MAX(t2.MIGRATION_DATETIME)
    FROM DASH_ETAT_CPT t2
    WHERE TO_CHAR(t2.MIGRATION_DATE_MINUS1, 'YYYY') = :year_only
)
"""

# Tombe : même prédicat mais sur DASH_TOMBE_MOIS (sous-requêtes sur la même table)
def _tombe_where(etat_fragment: str) -> str:
    return etat_fragment.replace("DASH_ETAT_CPT", "DASH_TOMBE_MOIS")


_SQL_EXIGIBLE_M1 = """
WHERE t.MIGRATION_DATETIME = (
    SELECT MAX(t2.MIGRATION_DATETIME)
    FROM DASH_EXIGIBLE t2
    WHERE TO_CHAR(t2.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year_m1
)
"""


def _build_main_sql(etat_tombe_filter: str, tombe_filter: str) -> str:
    return f"""
WITH CTE_DASH_ETAT_CPT AS (
    SELECT
        BRANCH_CODE,
        AGENCE,
        CODE_GESTION_PRET,
        CHARGE_AFFAIRE,
        ETAT_CPT,
        MIGRATION_DATE_MINUS1
    FROM DASH_ETAT_CPT t
    {etat_tombe_filter}
),
CTE_DASH_EXIGIBLE_M_1 AS (
    SELECT
        BRANCH_CODE,
        BRANCH_NAME,
        CODE_GESTION_PRET,
        CHARGE_AFFAIRE,
        EXIGIBLE_M AS EXIGIBLE_M_1,
        MIGRATION_DATE_MINUS1
    FROM DASH_EXIGIBLE t
    {_SQL_EXIGIBLE_M1}
),
CTE_DASH_TOMBE_MOIS AS (
    SELECT
        BRANCH_CODE,
        CODE_GESTION_PRET,
        CHARGE_AFFAIRE,
        MONTANT_ECHEANCE_M,
        MIGRATION_DATE_MINUS1
    FROM DASH_TOMBE_MOIS t
    {tombe_filter}
)
SELECT
    e.BRANCH_CODE,
    e.AGENCE,
    e.CODE_GESTION_PRET,
    e.CHARGE_AFFAIRE,
    e.ETAT_CPT,
    NVL(t.MONTANT_ECHEANCE_M, 0) AS MONTANT_ECHEANCE_M,
    NVL(ex.EXIGIBLE_M_1, 0) AS EXIGIBLE_M_1,
    GREATEST(
        e.ETAT_CPT - (NVL(ex.EXIGIBLE_M_1, 0) + NVL(t.MONTANT_ECHEANCE_M, 0)),
        0
    ) AS COLLECTE_NET
FROM CTE_DASH_ETAT_CPT e
LEFT JOIN CTE_DASH_TOMBE_MOIS t
    ON t.CODE_GESTION_PRET = e.CODE_GESTION_PRET
   AND t.BRANCH_CODE = e.BRANCH_CODE
LEFT JOIN CTE_DASH_EXIGIBLE_M_1 ex
    ON ex.CODE_GESTION_PRET = e.CODE_GESTION_PRET
   AND ex.BRANCH_CODE = e.BRANCH_CODE
ORDER BY e.BRANCH_CODE, e.CODE_GESTION_PRET
"""


def get_domiciliation_flux_data(
    period: str = "month",
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Exécute la requête domiciliation (lots DASH alignés Volume DAT).

    - ETAT_CPT + TOMBE_MOIS : même filtre de période (jour / semaine / mois / année).
    - EXIGIBLE : toujours le mois calendaire M−1 (MM/YYYY) par rapport au mois de référence
      de la période (sauf mode année : EXIGIBLE sur 12/(année−1)).
    """
    from services.cache_service import get_cache, set_cache

    period = (period or "month").strip().lower()
    today = dt_date.today()
    ref_m, ref_y = _ref_month_year(period, month, year, date)
    viewing_current_month = ref_y == today.year and ref_m == today.month

    week_range = _week_range_dd_mm_yyyy(period, date)

    year_only_str: Optional[str] = None
    if period == "year":
        y = int(year) if year is not None else today.year
        year_only_str = f"{y:04d}"

    if week_range:
        ws, we = week_range
        cache_key = f"domiciliation_flux:week:{ws}_{we}:v1"
        month_year_m1 = _prev_month_year_str(ref_m, ref_y)
        etat_f = _SQL_ETAT_TOMBE_WEEK
        tombe_f = _tombe_where(_SQL_ETAT_TOMBE_WEEK)
        binds: Dict[str, Any] = {
            "week_start": ws,
            "week_end": we,
            "month_year_m1": month_year_m1,
        }
    elif year_only_str is not None:
        y = int(year) if year is not None else today.year
        cache_key = f"domiciliation_flux:year:{year_only_str}:v1"
        month_year_m1 = f"12/{y - 1}"
        etat_f = _SQL_ETAT_TOMBE_YEAR
        tombe_f = _tombe_where(_SQL_ETAT_TOMBE_YEAR)
        binds = {"year_only": year_only_str, "month_year_m1": month_year_m1}
    elif viewing_current_month:
        migration_target = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        month_year_m1 = _prev_month_year_str(today.month, today.year)
        cache_key = f"domiciliation_flux:day:{migration_target}:v1"
        etat_f = _SQL_ETAT_TOMBE_DAY
        tombe_f = _tombe_where(_SQL_ETAT_TOMBE_DAY)
        binds = {"migration_target": migration_target, "month_year_m1": month_year_m1}
    else:
        month_year = f"{ref_m:02d}/{ref_y}"
        month_year_m1 = _prev_month_year_str(ref_m, ref_y)
        cache_key = f"domiciliation_flux:month:{month_year}:v1"
        etat_f = _SQL_ETAT_TOMBE_MONTH
        tombe_f = _tombe_where(_SQL_ETAT_TOMBE_MONTH)
        binds = {"month_year": month_year, "month_year_m1": month_year_m1}

    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("✅ Domiciliation flux — cache hit %s", cache_key)
        return cached

    sql = _build_main_sql(etat_f, tombe_f)
    logger.info("🔍 Domiciliation flux — %s binds=%s", cache_key, binds)

    conn = get_oracle_connection_cofina()
    try:
        cursor = conn.cursor()
        cursor.arraysize = 500
        cursor.execute(sql, binds)
        columns = [d[0] for d in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        data = _rows_to_json_serializable(data)

        out = {
            "data": data,
            "meta": {
                "period": period,
                "binds": binds,
                "rowCount": len(data),
            },
        }
        set_cache(cache_key, out, ttl=300)
        logger.info("📊 Domiciliation flux — %s lignes", len(data))
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
