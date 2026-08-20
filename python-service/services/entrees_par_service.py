"""
Service Entrées PAR : dossiers entrés dans un palier PAR (0, 30, 90, 180, 360).
"""
import logging
import calendar
from typing import List, Dict, Optional
from datetime import datetime, date

from database.oracle_pool import get_pool_flexcube
from services.cache_service import TTL_DASHBOARD, generate_cache_key, get_cache, set_cache
from services.entrees_par_query import get_query_entrees_par

logger = logging.getLogger(__name__)


def _serialize_row(row: dict) -> dict:
    """Convertit les types Oracle (dates, Decimal) en types JSON-friendly."""
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = None
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif hasattr(v, "__float__") and not isinstance(v, (int, bool)):
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = str(v)
        else:
            out[k] = v
    return out


def _as_of_date_str(year: int, month: int) -> str:
    last_day = calendar.monthrange(year, month)[1]
    as_of = date(year, month, last_day)
    today = datetime.now().date()
    if as_of > today:
        as_of = today
    return as_of.strftime("%d/%m/%Y")


def get_entrees_par_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    par_bucket: int = 0,
) -> List[Dict]:
    """
    Récupère les dossiers entrés dans un palier PAR à la date d'arrêté.

    Args:
        month: Mois (1-12). Défaut: mois courant.
        year: Année. Défaut: année courante.
        par_bucket: Palier PAR (0, 30, 90, 180 ou 360).

    Returns:
        Liste de dictionnaires (NO_PRET, CHARGE_AFFAIRE, AGENCE, ENCOURS_IMPAYE, …)
    """
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    as_of_date = _as_of_date_str(year, month)
    cache_key = f"entrees-par:{generate_cache_key(as_of_date, par_bucket)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ Entrées PAR cache hit arrêté=%s par_bucket=%s", as_of_date, par_bucket)
        return cached

    logger.info("📊 Entrées PAR live Flexcube: arrêté=%s, par_bucket=%s", as_of_date, par_bucket)

    sql, binds = get_query_entrees_par(as_of_date, par_bucket)
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 180_000
            cursor.arraysize = 1000
            cursor.prefetchrows = 1000
            cursor.execute(sql, binds)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [_serialize_row(dict(zip(columns, row))) for row in rows]
            logger.info("✅ Entrées PAR: %d lignes pour PAR%s", len(result), par_bucket)
            set_cache(cache_key, result, TTL_DASHBOARD)
            return result
        finally:
            cursor.close()
