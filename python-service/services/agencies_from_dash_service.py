"""
Agences : CODE_BUREAU + libellé AGENCE depuis DASH_RELATION.
Par défaut : dernier snapshot global (MAX(MIGRATION_DATETIME)) pour lister toutes les agences du dernier chargement.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from database.oracle import get_oracle_connection_cofina
from services.agencies_dash_query import (
    AGENCIES_FROM_DASH_RELATION_SQL,
    AGENCIES_FROM_DASH_RELATION_SQL_BY_MONTH,
)
from services.utils import (
    get_territory_from_agency,
    get_territory_from_branch_code,
    normalize_branch_code_for_territory,
)

logger = logging.getLogger(__name__)

_TERRITORY_LABEL_TO_LARAVEL = {
    "DAKAR VILLE": "DAKAR_VILLE",
    "DAKAR CENTRE VILLE": "DAKAR_VILLE",
    "DAKAR BANLIEUE": "DAKAR_BANLIEUE",
    "PROVINCE CENTRE SUD": "PROVINCE_CENTRE_SUD",
    "PROVINCE NORD": "PROVINCE_NORD",
}


def _laravel_territory_code(py_territory: Optional[str]) -> Optional[str]:
    if not py_territory:
        return None
    key = " ".join(str(py_territory).upper().split())
    return _TERRITORY_LABEL_TO_LARAVEL.get(key)


def _row_to_agency_dict(code_raw: Any, name_raw: Any) -> Optional[dict[str, Any]]:
    if code_raw is None and name_raw is None:
        return None
    code_str = normalize_branch_code_for_territory(code_raw)
    name = (str(name_raw).strip() if name_raw is not None else "") or ""
    if not code_str or not name:
        return None
    upper_code = code_str.upper()
    if upper_code == "FILIALE":
        return None

    terr = get_territory_from_branch_code(code_str)
    if not terr:
        terr = get_territory_from_agency(name)
    territory_code = _laravel_territory_code(terr)

    return {
        "code": code_str,
        "name": name,
        "territory_code": territory_code,
    }


def fetch_agencies_from_dash_relation(
    month: Optional[int] = None,
    year: Optional[int] = None,
    scope: str = "latest",
) -> list[dict[str, Any]]:
    """
    Agences distinctes depuis DASH_RELATION.

    scope:
      - "latest" (défaut) : MAX(MIGRATION_DATETIME) sur toute la table — liste complète du dernier chargement.
      - "month" : même filtre MM/YYYY que le dash clients (sous-ensemble, souvent moins d'agences).
    """
    scope_norm = (scope or "latest").strip().lower()
    use_month = scope_norm == "month"

    conn = get_oracle_connection_cofina()
    try:
        cur = conn.cursor()
        if use_month:
            m, y = int(month or 0), int(year or 0)
            if not m or not y:
                now = datetime.now()
                m, y = now.month, now.year
            month_year = f"{m:02d}/{y}"
            cur.execute(AGENCIES_FROM_DASH_RELATION_SQL_BY_MONTH, {"month_year": month_year})
            log_label = f"month_year={month_year}"
        else:
            cur.execute(AGENCIES_FROM_DASH_RELATION_SQL)
            log_label = "snapshot global MAX(MIGRATION_DATETIME)"

        cols = [d[0] for d in cur.description]
        rows_out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for row in cur.fetchall():
            rec = dict(zip(cols, row))
            code_raw = rec.get("CODE_BUREAU")
            name_raw = rec.get("AGENCE")
            d = _row_to_agency_dict(code_raw, name_raw)
            if not d:
                continue
            key = (d["code"], d["name"])
            if key in seen:
                continue
            seen.add(key)
            rows_out.append(d)
        logger.info(
            "📊 Agences DASH_RELATION (%s): %s ligne(s)",
            log_label,
            len(rows_out),
        )
        return rows_out
    finally:
        conn.close()
