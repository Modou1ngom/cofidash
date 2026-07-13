"""
Router C360 — API pour l'application mobile (cache local + sync Oracle).
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database.c360_local_db import get_sync_status
from services.c360_sync_service import (
    get_account_ecritures,
    get_customer_c360,
    get_pret_remboursements,
    sync_customer_c360,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/c360", tags=["c360"])


class SyncRequest(BaseModel):
    customer_no: str = Field(..., min_length=1)
    ecritures_limit: int = Field(default=10, ge=1, le=100)
    sync_remboursements: bool = True
    prets: Optional[List[str]] = None


@router.get("/health")
async def c360_health():
    """Santé du module C360."""
    from config.settings import C360_LOCAL_DB_PATH

    return {
        "status": "ok",
        "module": "c360",
        "local_db": C360_LOCAL_DB_PATH,
    }


@router.get("/sync/status/{customer_no}")
async def sync_status(customer_no: str):
    """Statut de la dernière synchronisation pour un client."""
    meta = get_sync_status(customer_no.strip())
    if not meta:
        return {"customer_no": customer_no, "status": "never_synced"}
    return meta


@router.post("/sync")
async def sync_customer(body: SyncRequest):
    """
    Synchronise un client depuis Oracle Flexcube vers la base locale.
    À appeler périodiquement ou à la connexion mobile.
    """
    try:
        result = sync_customer_c360(
            customer_no=body.customer_no,
            ecritures_limit=body.ecritures_limit,
            sync_remboursements=body.sync_remboursements,
            prets=body.prets,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Erreur sync C360: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/client/{customer_no}")
async def get_client_360(
    customer_no: str,
    refresh: bool = Query(False, description="Forcer une sync Oracle avant lecture"),
    ecritures_limit: int = Query(10, ge=1, le=100),
):
    """Vue 360 d'un client : KYC + comptes (depuis cache local)."""
    try:
        return get_customer_c360(
            customer_no=customer_no,
            refresh=refresh,
            ecritures_limit=ecritures_limit,
        )
    except Exception as exc:
        logger.error("Erreur lecture C360 client %s: %s", customer_no, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/kyc/{customer_no}")
async def get_kyc(
    customer_no: str,
    refresh: bool = Query(False),
    ecritures_limit: int = Query(10, ge=1, le=100),
):
    """Données KYC d'un client."""
    result = get_customer_c360(customer_no, refresh=refresh, ecritures_limit=ecritures_limit)
    kyc = result.get("kyc")
    if not kyc:
        raise HTTPException(status_code=404, detail=f"KYC introuvable pour {customer_no}")
    return {
        "customer_no": customer_no,
        "source": result.get("source"),
        "sync_meta": result.get("sync_meta"),
        **kyc,
    }


@router.get("/comptes/{customer_no}")
async def get_comptes(
    customer_no: str,
    refresh: bool = Query(False),
    ecritures_limit: int = Query(10, ge=1, le=100),
):
    """Comptes bancaires (Banque au quotidien) d'un client."""
    result = get_customer_c360(customer_no, refresh=refresh, ecritures_limit=ecritures_limit)
    return {
        "customer_no": customer_no,
        "source": result.get("source"),
        "sync_meta": result.get("sync_meta"),
        **result.get("comptes", {"data": [], "updated_at": None}),
    }


@router.get("/ecritures/{account_no}")
async def get_ecritures(
    account_no: str,
    limit: int = Query(10, ge=1, le=100),
    refresh: bool = Query(False),
):
    """Historique des écritures d'un compte."""
    try:
        return get_account_ecritures(account_no, limit=limit, refresh=refresh)
    except Exception as exc:
        logger.error("Erreur écritures %s: %s", account_no, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/remboursements/{no_pret}")
async def get_remboursements(
    no_pret: str,
    customer_no: Optional[str] = Query(None),
    refresh: bool = Query(False),
):
    """Historique des remboursements d'un prêt."""
    try:
        return get_pret_remboursements(no_pret, customer_no=customer_no, refresh=refresh)
    except Exception as exc:
        logger.error("Erreur remboursements %s: %s", no_pret, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
