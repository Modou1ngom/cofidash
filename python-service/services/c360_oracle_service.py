"""
Service C360 — lecture Oracle Flexcube (CFSFCUBS145).
"""
import logging
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.c360_queries import (
    CHECKING_PI_QUERY,
    COMPTES_QUERY,
    ECRITURES_QUERY,
    KYC_BY_ACCOUNT_QUERY,
    KYC_BY_EXT_REF_QUERY,
    KYC_QUERY,
    PRETS_CLIENT_QUERY,
    REMBOURSEMENTS_QUERY,
)

logger = logging.getLogger(__name__)


def _serialize_cell(val: Any) -> Any:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    if isinstance(val, (int, float, str, bool)):
        return val
    return str(val)


def compte_field(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        val = row.get(key)
        if val is not None and str(val).strip() != "":
            return val
    return None


def compte_account_number(row: Dict[str, Any]) -> str:
    return str(
        compte_field(
            row,
            "NUMERO COMPTE",
            "NUMERO_COMPTE",
            "numero_Compte",
            "numero_compte",
        )
        or ""
    ).strip()


def ecriture_field(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        val = row.get(key)
        if val is not None and str(val).strip() != "":
            return val
    return None


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out: List[Dict[str, Any]] = []
    for row in rows:
        item: Dict[str, Any] = {}
        for col, cell in zip(columns, row):
            key = col.upper() if isinstance(col, str) else col
            item[key] = _serialize_cell(cell)
        out.append(item)
    return out


def _execute_query(query: str, params: dict, timeout_ms: int = 20_000) -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = timeout_ms
            cursor.execute(query, params)
            return _rows_to_dicts(cursor)
        finally:
            cursor.close()


def fetch_kyc_from_oracle(lookup: str) -> Optional[Dict[str, Any]]:
    """KYC Flexcube — recherche par CUSTOMER_NO, N° compte ou matricule (EXT_REF)."""
    key = str(lookup or "").strip()
    if not key:
        return None

    rows = _execute_query(KYC_QUERY, {"customer_no": key})
    if rows:
        return rows[0]

    if key.isdigit() and len(key) >= 8:
        rows = _execute_query(KYC_BY_ACCOUNT_QUERY, {"lookup": key})
        if rows:
            return rows[0]

    rows = _execute_query(KYC_BY_EXT_REF_QUERY, {"lookup": key})
    return rows[0] if rows else None


def fetch_comptes_from_oracle(customer_no: str) -> List[Dict[str, Any]]:
    return _execute_query(COMPTES_QUERY, {"customer_no": customer_no})


def fetch_ecritures_from_oracle(account_no: str, limit: int = 10) -> List[Dict[str, Any]]:
    return _execute_query(
        ECRITURES_QUERY,
        {"account_no": account_no, "limit": limit},
    )


def fetch_remboursements_from_oracle(no_pret: str) -> List[Dict[str, Any]]:
    return _execute_query(REMBOURSEMENTS_QUERY, {"no_pret": no_pret})


def fetch_prets_client_from_oracle(customer_no: str) -> List[str]:
    rows = _execute_query(PRETS_CLIENT_QUERY, {"customer_no": customer_no})
    return [str(r.get("NO_PRET", "")).strip() for r in rows if r.get("NO_PRET")]


def fetch_checking_pi_from_oracle(customer_no: str) -> Optional[Dict[str, Any]]:
    """Champs Checking-PI Flexcube pour un client (compte épargne/courant ouvert)."""
    key = str(customer_no or "").strip()
    if not key:
        return None
    rows = _execute_query(CHECKING_PI_QUERY, {"customer_no": key}, timeout_ms=45_000)
    return rows[0] if rows else None
