"""
Synchronisation C360 Oracle → base SQLite locale.
"""
import logging
from typing import Any, Dict, List, Optional

from database.c360_local_db import (
    get_comptes,
    get_ecritures,
    get_kyc,
    get_remboursements,
    get_sync_status,
    save_comptes,
    save_ecritures,
    save_kyc,
    save_remboursements,
    upsert_sync_meta,
)
from services.c360_oracle_service import (
    compte_account_number,
    fetch_comptes_from_oracle,
    fetch_ecritures_from_oracle,
    fetch_kyc_from_oracle,
    fetch_prets_client_from_oracle,
    fetch_remboursements_from_oracle,
)

logger = logging.getLogger(__name__)


def sync_customer_c360(
    customer_no: str,
    ecritures_limit: int = 10,
    sync_remboursements: bool = True,
    prets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Synchronise KYC, comptes, écritures et remboursements d'un client depuis Oracle.
    """
    customer_no = str(customer_no).strip()
    if not customer_no:
        raise ValueError("customer_no requis")

    upsert_sync_meta(customer_no, status="running")

    comptes_count = 0
    ecritures_count = 0
    remboursements_count = 0

    try:
        kyc = fetch_kyc_from_oracle(customer_no)
        if kyc:
            save_kyc(customer_no, kyc)
        else:
            logger.warning("KYC introuvable pour le client %s", customer_no)

        comptes = fetch_comptes_from_oracle(customer_no)
        comptes_count = save_comptes(customer_no, comptes)

        for compte in comptes:
            account_no = compte_account_number(compte)
            if not account_no:
                continue
            ecritures = fetch_ecritures_from_oracle(account_no, limit=ecritures_limit)
            ecritures_count += save_ecritures(account_no, ecritures)

        pret_list = prets if prets is not None else []
        if sync_remboursements and not pret_list:
            pret_list = fetch_prets_client_from_oracle(customer_no)

        for no_pret in pret_list:
            no_pret = str(no_pret).strip()
            if not no_pret:
                continue
            remb = fetch_remboursements_from_oracle(no_pret)
            remboursements_count += save_remboursements(no_pret, remb, customer_no)

        upsert_sync_meta(
            customer_no,
            status="success",
            comptes_count=comptes_count,
            ecritures_count=ecritures_count,
            remboursements_count=remboursements_count,
        )

        return {
            "customer_no": customer_no,
            "status": "success",
            "kyc_found": kyc is not None,
            "comptes_count": comptes_count,
            "ecritures_count": ecritures_count,
            "remboursements_count": remboursements_count,
            "sync_meta": get_sync_status(customer_no),
        }
    except Exception as exc:
        logger.error("Erreur sync C360 client %s: %s", customer_no, exc, exc_info=True)
        upsert_sync_meta(
            customer_no,
            status="error",
            error_message=str(exc),
            comptes_count=comptes_count,
            ecritures_count=ecritures_count,
            remboursements_count=remboursements_count,
        )
        raise


def get_customer_c360(
    customer_no: str,
    refresh: bool = False,
    ecritures_limit: int = 10,
) -> Dict[str, Any]:
    """Retourne les données C360 depuis le cache local, avec option de rafraîchissement Oracle."""
    customer_no = str(customer_no).strip()
    if refresh:
        sync_customer_c360(customer_no, ecritures_limit=ecritures_limit)

    kyc = get_kyc(customer_no)
    comptes = get_comptes(customer_no)
    sync_meta = get_sync_status(customer_no)

    return {
        "customer_no": customer_no,
        "source": "local_cache",
        "sync_meta": sync_meta,
        "kyc": kyc,
        "comptes": comptes,
    }


def get_account_ecritures(
    account_no: str,
    limit: int = 10,
    refresh: bool = False,
) -> Dict[str, Any]:
    account_no = str(account_no).strip()
    if refresh:
        ecritures = fetch_ecritures_from_oracle(account_no, limit=limit)
        save_ecritures(account_no, ecritures)
    return {
        "account_no": account_no,
        "source": "local_cache" if not refresh else "oracle+local_cache",
        **get_ecritures(account_no, limit=limit),
    }


def get_pret_remboursements(
    no_pret: str,
    customer_no: Optional[str] = None,
    refresh: bool = False,
) -> Dict[str, Any]:
    no_pret = str(no_pret).strip()
    if refresh:
        remb = fetch_remboursements_from_oracle(no_pret)
        save_remboursements(no_pret, remb, customer_no)
    return {
        "no_pret": no_pret,
        "source": "local_cache" if not refresh else "oracle+local_cache",
        **get_remboursements(no_pret),
    }
