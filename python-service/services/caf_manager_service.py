"""
Résolution CODE_GESTION_PRET (FIELD_CHAR_2 / LOV GESTION_PRET) pour les CAF.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import TTL_REFERENCE, get_cache, set_cache

logger = logging.getLogger(__name__)

GESTION_PRET_MANAGERS = """
SELECT
    u.LOV AS CODE_GESTION_PRET,
    u.LOV_DESC AS CHARGE_AFFAIRE
FROM CFSFCUBS145.UDTM_LOV u
WHERE u.FIELD_NAME = 'GESTION_PRET'
ORDER BY u.LOV_DESC
"""


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [str(col[0]).lower() for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _execute_flexcube(query: str, params: Optional[dict] = None) -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 30_000
            cursor.execute(query, params or {})
            return _rows_to_dicts(cursor)
        finally:
            cursor.close()


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text


def _name_candidates(name: Optional[str], email: Optional[str]) -> List[str]:
    candidates: List[str] = []
    if name:
        candidates.append(_normalize_text(name))
    if email:
        local = email.split("@", 1)[0].strip()
        if local and len(local) >= 4:
            candidates.append(_normalize_text(local.replace(".", " ").replace("_", " ")))
    seen = set()
    unique: List[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def list_gestion_pret_managers() -> List[Dict[str, str]]:
    cache_key = "flexcube-gestion-pret-managers"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ Liste CAF cache hit (%s)", len(cached))
        return cached

    rows = _execute_flexcube(GESTION_PRET_MANAGERS)
    managers = [
        {
            "code_gestion_pret": str(row.get("code_gestion_pret") or "").strip(),
            "charge_affaire": str(row.get("charge_affaire") or "").strip(),
        }
        for row in rows
        if str(row.get("code_gestion_pret") or "").strip()
    ]
    set_cache(cache_key, managers, TTL_REFERENCE)
    return managers


def resolve_manager_code(
    *,
    manager_code: Optional[str] = None,
    charge_affaire: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Retrouve le code gestionnaire Flexcube à partir du code, du nom ou de l'email."""
    code = str(manager_code or "").strip()
    if code:
        managers = list_gestion_pret_managers()
        for row in managers:
            if row["code_gestion_pret"] == code:
                return row
        logger.info("CODE_GESTION_PRET introuvable dans LOV GESTION_PRET: %s", code)
        return None

    managers = list_gestion_pret_managers()
    if not managers:
        return None

    search_labels = _name_candidates(charge_affaire or name, email)
    if not search_labels:
        return None

    for label in search_labels:
        for row in managers:
            desc = _normalize_text(row.get("charge_affaire"))
            if desc == label:
                return row

    for label in search_labels:
        if len(label) < 6:
            continue
        for row in managers:
            desc = _normalize_text(row.get("charge_affaire"))
            if label in desc or desc in label:
                return row

    logger.info(
        "Aucun CODE_GESTION_PRET trouvé pour email=%s name=%s labels=%s",
        email,
        name,
        search_labels,
    )
    return None
