"""
Service Entrées PAR et Provisions : exécute la requête par palier PAR (0, 30, 90, 180, 360).
"""
import logging
import calendar
from typing import List, Dict, Optional
from datetime import datetime

from database.oracle_pool import get_pool
from services.entrees_par_query import get_query_entrees_par

logger = logging.getLogger(__name__)


def _serialize_row(row: dict) -> dict:
    """Convertit les types Oracle (dates, Decimal) en types JSON-friendly."""
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = None
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat() if hasattr(v, "isoformat") else str(v)
        elif hasattr(v, "__float__") and not isinstance(v, (int, bool)):
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = str(v)
        else:
            out[k] = v
    return out


def get_entrees_par_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    par_bucket: int = 0,
) -> List[Dict]:
    """
    Récupère les entrées PAR et provisions pour une date (dernier jour du mois) et un palier PAR.

    Args:
        month: Mois (1-12). Défaut: mois courant.
        year: Année. Défaut: année courante.
        par_bucket: Palier PAR (0, 30, 90, 180 ou 360).

    Returns:
        Liste de dictionnaires (NO_PRET, BLOC, NOM_CLIENT, AGENCE, ENCOURS_TOTAL, PROVISIONS, etc.)
    """
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    last_day = calendar.monthrange(year, month)[1]
    date_obj = datetime(year, month, last_day)
    date_str = date_obj.strftime("%d/%m/%Y")

    logger.info("📊 Entrées PAR: date=%s, par_bucket=%s", date_str, par_bucket)

    sql = get_query_entrees_par(date_str, par_bucket)
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.arraysize = 1000
            cursor.prefetchrows = 1000
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [_serialize_row(dict(zip(columns, row))) for row in rows]
            logger.info("✅ Entrées PAR: %d lignes pour PAR%s", len(result), par_bucket)
            return result
        finally:
            cursor.close()
