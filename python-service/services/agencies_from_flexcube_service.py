"""
Agences : BRANCH_CODE + BRANCH_NAME depuis Flexcube (STTM_BRANCH).
Sans tables DASH.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from database.oracle import get_oracle_connection
from services.agencies_flexcube_query import AGENCIES_FROM_STTM_BRANCH_SQL
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


def fetch_agencies_from_flexcube() -> list[dict[str, Any]]:
    """Agences distinctes depuis CFSFCUBS145.STTM_BRANCH (Flexcube)."""
    conn = get_oracle_connection()
    try:
        cur = conn.cursor()
        cur.execute(AGENCIES_FROM_STTM_BRANCH_SQL)

        cols = [d[0] for d in cur.description]
        rows_out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for row in cur.fetchall():
            rec = dict(zip(cols, row))
            code_raw = rec.get("BRANCH_CODE")
            name_raw = rec.get("BRANCH_NAME")
            d = _row_to_agency_dict(code_raw, name_raw)
            if not d:
                continue
            key = (d["code"], d["name"])
            if key in seen:
                continue
            seen.add(key)
            rows_out.append(d)
        logger.info("📊 Agences STTM_BRANCH (Flexcube): %s ligne(s)", len(rows_out))
        return rows_out
    finally:
        conn.close()
