"""
Router Vue 360 — endpoints consommés par Laravel /api/v1.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services import vue360_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vue360", tags=["vue360"])


class BranchScope(BaseModel):
    branch_codes: List[str] = Field(default_factory=list)


class AgencyInput(BaseModel):
    code: str
    name: str = ""
    zone: str = ""
    category: str = "agence"


class AgenciesKpiRequest(BaseModel):
    agencies: List[AgencyInput] = Field(default_factory=list)


class ZoneAgencyInput(BaseModel):
    code: str
    name: str = ""


class ZoneInput(BaseModel):
    id: str
    name: str = ""
    agencies: List[ZoneAgencyInput] = Field(default_factory=list)


class ZonesKpiRequest(BaseModel):
    zones: List[ZoneInput] = Field(default_factory=list)
    agencies_kpis: Optional[List[dict]] = None


@router.post("/agencies/kpis")
async def vue360_agencies_kpis(body: AgenciesKpiRequest):
    """KPI Oracle par agence (Flexcube + DASH)."""
    try:
        agencies = [a.model_dump() for a in body.agencies]
        return {"data": vue360_service.get_agencies_kpis(agencies)}
    except Exception as exc:
        logger.error("vue360 agencies kpis: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/zones/kpis")
async def vue360_zones_kpis(body: ZonesKpiRequest):
    """KPI Oracle agrégés par zone."""
    try:
        all_agencies = []
        for zone in body.zones:
            for agency in zone.agencies:
                all_agencies.append(
                    {
                        "code": agency.code,
                        "name": agency.name,
                        "zone": zone.name,
                    }
                )
        agencies_kpis = body.agencies_kpis
        if not agencies_kpis:
            agencies_kpis = vue360_service.get_agencies_kpis(all_agencies)

        zones_out = []
        for zone in body.zones:
            zone_dict = {
                "id": zone.id,
                "name": zone.name,
                "agencies": [a.model_dump() for a in zone.agencies],
            }
            zones_out.append(vue360_service.get_zone_kpis(zone_dict, agencies_kpis))
        return {"data": zones_out}
    except Exception as exc:
        logger.error("vue360 zones kpis: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clients")
async def vue360_clients(
    branch_codes: Optional[str] = Query(None, description="Codes agence séparés par virgule"),
    field: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        data = vue360_service.list_clients(
            branch_codes=branches or None,
            field=field,
            query=query,
            limit=limit,
        )
        return {"data": data}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("vue360 clients: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clients/{client_id}/kyc")
async def vue360_client_kyc(
    client_id: str,
    branch_codes: Optional[str] = Query(None, description="Codes agence séparés par virgule"),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        kyc = vue360_service.get_kyc(client_id, branch_codes=branches or None)
        if not kyc:
            raise HTTPException(status_code=404, detail="KYC introuvable")
        return {"data": kyc}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("vue360 kyc %s: %s", client_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clients/{client_id}/accounts")
async def vue360_client_accounts(
    client_id: str,
    type: Optional[str] = Query(
        None,
        description="Type de compte: courant, epargne, dat, depot_garantie",
    ),
    refresh: bool = Query(False),
    ecritures_limit: int = Query(10, ge=1, le=100),
):
    try:
        data = vue360_service.list_client_accounts(
            client_id,
            account_type=type,
            refresh=refresh,
            ecritures_limit=ecritures_limit,
        )
        return {"data": data}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("vue360 comptes %s: %s", client_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clients/{client_id}/accounts/{account_number}")
async def vue360_client_account_detail(
    client_id: str,
    account_number: str,
    refresh: bool = Query(False),
    transactions_limit: int = Query(20, ge=1, le=100),
):
    try:
        account = vue360_service.get_client_account(
            client_id,
            account_number,
            refresh=refresh,
            transactions_limit=transactions_limit,
        )
        if not account:
            raise HTTPException(status_code=404, detail="Compte introuvable")
        return {"data": account}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "vue360 compte %s/%s: %s", client_id, account_number, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clients/{client_id}")
async def vue360_client_detail(
    client_id: str,
    branch_codes: Optional[str] = Query(None),
    refresh_cache: bool = Query(False),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        client = vue360_service.get_client(
            client_id,
            branch_codes=branches or None,
            refresh_cache=refresh_cache,
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client introuvable")
        return {"data": client}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("vue360 client %s: %s", client_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/credits")
async def vue360_credits(
    branch_codes: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        data = vue360_service.list_credits(
            branch_codes=branches or None,
            client_id=client_id,
            limit=limit,
        )
        return {"data": data}
    except Exception as exc:
        logger.error("vue360 credits: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/credits/{loan_id}")
async def vue360_credit_detail(
    loan_id: str,
    branch_codes: Optional[str] = Query(None),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        credit = vue360_service.get_credit(loan_id, branch_codes=branches or None)
        if not credit:
            raise HTTPException(status_code=404, detail="Crédit introuvable")
        return {"data": credit}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("vue360 credit %s: %s", loan_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/credits/{loan_id}/ta")
async def vue360_credit_amortization(loan_id: str):
    try:
        data = vue360_service.get_amortization_schedule(loan_id)
        return {"data": data}
    except Exception as exc:
        logger.error("vue360 ta %s: %s", loan_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/credits/{loan_id}/repayments")
async def vue360_repayments(loan_id: str):
    try:
        data = vue360_service.get_repayments(loan_id)
        return {"data": data}
    except Exception as exc:
        logger.error("vue360 repayments %s: %s", loan_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/caf/managers")
async def vue360_caf_managers():
    """Liste des chargés d'affaires Flexcube (LOV GESTION_PRET)."""
    try:
        from services.caf_manager_service import list_gestion_pret_managers

        return {"data": list_gestion_pret_managers()}
    except Exception as exc:
        logger.error("vue360 caf managers: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/caf/resolve-manager")
async def vue360_caf_resolve_manager(
    email: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    manager_code: Optional[str] = Query(None),
    charge_affaire: Optional[str] = Query(None),
):
    """Résout email/nom → CODE_GESTION_PRET Oracle."""
    try:
        from services.caf_manager_service import resolve_manager_code

        resolved = resolve_manager_code(
            manager_code=manager_code,
            charge_affaire=charge_affaire,
            email=email,
            name=name,
        )
        if not resolved:
            raise HTTPException(status_code=404, detail="Code gestionnaire introuvable")
        return {"data": resolved}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("vue360 caf resolve-manager: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/caf/vue-ensemble")
async def vue360_caf_vue_ensemble(
    branch_codes: Optional[str] = Query(None, description="Codes agence séparés par virgule"),
    caf_code: Optional[str] = Query(None, description="CODE_GESTION_PRET (FIELD_CHAR_2)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Mois calendaire (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Année"),
):
    """Vue d'ensemble CAF mobile — portefeuille, top encours PAR, provisions."""
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        from services.caf_vue_ensemble_service import get_caf_vue_ensemble

        return {
            "data": get_caf_vue_ensemble(
                branch_codes=branches or None,
                caf_code=caf_code,
                month=month,
                year=year,
            )
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("vue360 caf vue-ensemble: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/kpis")
async def vue360_dashboard_kpis(branch_codes: Optional[str] = Query(None)):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        return {"data": vue360_service.get_dashboard_kpis(branches or None)}
    except Exception as exc:
        logger.error("vue360 kpis: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/risks")
async def vue360_risks(branch_codes: Optional[str] = Query(None)):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        return {"data": vue360_service.get_risks(branches or None)}
    except Exception as exc:
        logger.error("vue360 risks: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dat-deposits")
async def vue360_dat_deposits(
    branch_codes: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        return {"data": vue360_service.list_dat_deposits(branches or None, limit=limit)}
    except Exception as exc:
        logger.error("vue360 dat: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/opportunities")
async def vue360_opportunities(branch_codes: Optional[str] = Query(None)):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        clients = vue360_service.list_clients(branch_codes=branches or None, limit=100)
        return {"data": vue360_service.list_opportunities(clients)}
    except Exception as exc:
        logger.error("vue360 opportunities: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/notifications")
async def vue360_notifications(branch_codes: Optional[str] = Query(None)):
    branches = [b.strip() for b in (branch_codes or "").split(",") if b.strip()]
    try:
        clients = vue360_service.list_clients(branch_codes=branches or None, limit=100)
        return {"data": vue360_service.list_notifications(clients)}
    except Exception as exc:
        logger.error("vue360 notifications: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
