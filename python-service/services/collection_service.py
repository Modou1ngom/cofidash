"""
Collecte / domiciliation de flux — données issues des tables DASH
(DASH_ETAT_CPT, DASH_TOMBE_MOIS, DASH_EXIGIBLE) via domiciliation_flux_service.
"""
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key
from services.domiciliation_flux_service import get_domiciliation_flux_data

logger = logging.getLogger(__name__)

_GRAND_COMPTE_NAMES = frozenset(
    x.upper() for x in ("GRAND COMPTE", "AGENCE GRAND COMPTE", "GRAND COMPTES")
)


def _f(row: dict, *keys: str) -> float:
    for k in keys:
        v = row.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0


def _base_agency_shell(
    agency_name: str,
    branch_code: str,
    code_gestion: str,
    charge_affaire: str,
) -> Dict[str, Any]:
    return {
        "name": agency_name,
        "AGENCE": agency_name,
        "BRANCH_CODE": branch_code,
        "branch_code": branch_code,
        "AC_NO": "",
        "ac_no": "",
        "codeGestion": code_gestion,
        "CODE_GESTION": code_gestion,
        "codeGestionList": [],
        "CODE_GESTION_LIST": [],
        "chargeAffaire": charge_affaire,
        "CHARGE_AFFAIRE": charge_affaire,
        "chargeAffaireList": [],
        "CHARGE_AFFAIRE_LIST": [],
        "exigibleM1": 0.0,
        "EXIGIBLE_M1": 0.0,
        "exigibleS1": 0.0,
        "EXIGIBLE_S1": 0.0,
        "exigibleS2": 0.0,
        "EXIGIBLE_S2": 0.0,
        "exigibleS3": 0.0,
        "EXIGIBLE_S3": 0.0,
        "exigibleS4": 0.0,
        "EXIGIBLE_S4": 0.0,
        "SLD_M": 0.0,
        "SLD_M_1": 0.0,
        "SLD_S1": 0.0,
        "sldS1": 0.0,
        "SLD_S2": 0.0,
        "sldS2": 0.0,
        "SLD_S3": 0.0,
        "sldS3": 0.0,
        "SLD_S4": 0.0,
        "sldS4": 0.0,
        "MT_ECHEANCE": 0.0,
        "mtEcheance": 0.0,
        "M": 0.0,
        "M_1": 0.0,
        "S1": 0.0,
        "S2": 0.0,
        "S3": 0.0,
        "S4": 0.0,
        "MT_ECH_S1": 0.0,
        "MT_ECH_S2": 0.0,
        "MT_ECH_S3": 0.0,
        "MT_ECH_S4": 0.0,
        "COLLECTE_M": 0.0,
        "collecteM": 0.0,
        "COLLECTE_S1": 0.0,
        "collecteS1": 0.0,
        "COLLECTE_S2": 0.0,
        "collecteS2": 0.0,
        "COLLECTE_S3": 0.0,
        "collecteS3": 0.0,
        "COLLECTE_S4": 0.0,
        "collecteS4": 0.0,
        "objectif": 0.0,
        "OBJECTIF": 0.0,
    }


def _build_from_domiciliation_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Agrège les lignes prêt (DASH) en agences + territoires + détails chargé d'affaire."""
    agencies_data: Dict[str, Dict[str, Any]] = {}
    charge_affaire_data: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    grand_compte: Optional[Dict[str, Any]] = None

    for row in rows:
        agency_name = (row.get("AGENCE") or row.get("agence") or "INCONNU").strip()
        branch_code = str(row.get("BRANCH_CODE") or row.get("branch_code") or "").strip()
        code_gestion = (row.get("CODE_GESTION_PRET") or "").strip()
        if code_gestion in ("", "-"):
            code_gestion = ""
        charge_affaire = (row.get("CHARGE_AFFAIRE") or "").strip()
        exig = _f(row, "EXIGIBLE_M_1", "exigible_m_1")
        mt_ech = _f(row, "MONTANT_ECHEANCE_M", "montant_echeance_m")
        etat = _f(row, "ETAT_CPT", "etat_cpt")
        coll = _f(row, "COLLECTE_NET", "collecte_net")

        is_gc = agency_name.upper() in _GRAND_COMPTE_NAMES or "GRAND COMPTE" in agency_name.upper()

        if is_gc:
            if grand_compte is None:
                grand_compte = _base_agency_shell(agency_name, branch_code or "526", "", charge_affaire)
                grand_compte["BRANCH_CODE"] = branch_code or "526"
                grand_compte["branch_code"] = branch_code or "526"
            grand_compte["exigibleM1"] += exig
            grand_compte["EXIGIBLE_M1"] += exig
            grand_compte["MT_ECHEANCE"] += mt_ech
            grand_compte["mtEcheance"] += mt_ech
            grand_compte["M"] += etat
            grand_compte["COLLECTE_M"] += coll
            grand_compte["collecteM"] += coll
            continue

        agency_key = branch_code if branch_code else f"NO_CODE_{agency_name}"

        if agency_key not in agencies_data:
            agencies_data[agency_key] = _base_agency_shell(agency_name, branch_code, code_gestion, charge_affaire)

        ag = agencies_data[agency_key]
        ag["exigibleM1"] += exig
        ag["EXIGIBLE_M1"] += exig
        ag["MT_ECHEANCE"] += mt_ech
        ag["mtEcheance"] += mt_ech
        ag["M"] += etat
        ag["COLLECTE_M"] += coll
        ag["collecteM"] += coll

        if code_gestion and code_gestion not in (ag.get("codeGestionList") or []):
            ag.setdefault("codeGestionList", []).append(code_gestion)
            ag.setdefault("CODE_GESTION_LIST", []).append(code_gestion)
        if not ag.get("codeGestion") and code_gestion:
            ag["codeGestion"] = code_gestion
            ag["CODE_GESTION"] = code_gestion

        if charge_affaire and charge_affaire not in (ag.get("chargeAffaireList") or []):
            ag.setdefault("chargeAffaireList", []).append(charge_affaire)
            ag.setdefault("CHARGE_AFFAIRE_LIST", []).append(charge_affaire)
        if not ag.get("chargeAffaire") and charge_affaire:
            ag["chargeAffaire"] = charge_affaire
            ag["CHARGE_AFFAIRE"] = charge_affaire

        caf_key = f"{code_gestion}_{charge_affaire}" if code_gestion or charge_affaire else f"NO_CHARGE_{agency_key}"
        if caf_key not in charge_affaire_data[agency_key]:
            charge_affaire_data[agency_key][caf_key] = _base_agency_shell(
                agency_name, branch_code, code_gestion, charge_affaire or "-"
            )
        cfd = charge_affaire_data[agency_key][caf_key]
        cfd["exigibleM1"] += exig
        cfd["EXIGIBLE_M1"] += exig
        cfd["MT_ECHEANCE"] += mt_ech
        cfd["mtEcheance"] += mt_ech
        cfd["M"] += etat
        cfd["COLLECTE_M"] += coll
        cfd["collecteM"] += coll

    agencies_by_territory = {
        "territoire_dakar_ville": [],
        "territoire_dakar_banlieue": [],
        "territoire_province_centre_sud": [],
        "territoire_province_nord": [],
    }

    for agency_key, ag in agencies_data.items():
        bc = ag.get("BRANCH_CODE") or ""
        an = ag.get("AGENCE") or ""
        territory_name = get_territory_from_branch_code(bc) if bc else None
        if not territory_name:
            territory_name = get_territory_from_agency(an)
        tk = get_territory_key(territory_name) if territory_name else "territoire_dakar_ville"
        if tk not in agencies_by_territory:
            tk = "territoire_dakar_ville"
        agencies_by_territory[tk].append(ag)

    def calculate_territory_totals(agencies_list: List[Dict[str, Any]]) -> Dict[str, float]:
        totals = {
            "exigibleM1": 0.0,
            "EXIGIBLE_M1": 0.0,
            "mtEcheance": 0.0,
            "MT_ECHEANCE": 0.0,
            "collecteM": 0.0,
            "COLLECTE_M": 0.0,
            "sldM": 0.0,
            "SLD_M": 0.0,
            "sldS1": 0.0,
            "SLD_S1": 0.0,
            "sldS2": 0.0,
            "SLD_S2": 0.0,
            "sldS3": 0.0,
            "SLD_S3": 0.0,
            "sldS4": 0.0,
            "SLD_S4": 0.0,
            "collecteS1": 0.0,
            "COLLECTE_S1": 0.0,
            "collecteS2": 0.0,
            "COLLECTE_S2": 0.0,
            "collecteS3": 0.0,
            "COLLECTE_S3": 0.0,
            "collecteS4": 0.0,
            "COLLECTE_S4": 0.0,
        }
        for a in agencies_list:
            totals["exigibleM1"] += float(a.get("exigibleM1") or 0)
            totals["EXIGIBLE_M1"] += float(a.get("EXIGIBLE_M1") or 0)
            totals["mtEcheance"] += float(a.get("mtEcheance") or 0)
            totals["MT_ECHEANCE"] += float(a.get("MT_ECHEANCE") or 0)
            totals["collecteM"] += float(a.get("collecteM") or a.get("COLLECTE_M") or 0)
            totals["COLLECTE_M"] += float(a.get("COLLECTE_M") or 0)
            totals["sldM"] += float(a.get("sldM") or a.get("SLD_M") or 0)
            totals["SLD_M"] += float(a.get("SLD_M") or 0)
            totals["sldS1"] += float(a.get("sldS1") or a.get("SLD_S1") or 0)
            totals["collecteS1"] += float(a.get("collecteS1") or a.get("COLLECTE_S1") or 0)
        return totals

    total_exigible = sum(float(a.get("exigibleM1") or 0) for a in agencies_data.values())

    response_data: Dict[str, Any] = {
        "globalResult": {
            "exigibleJ1": total_exigible,
            "montantARecouvrer": total_exigible,
        },
        "hierarchicalData": {
            "TERRITOIRE": {
                "dakar_centre_ville": {
                    "name": "DAKAR CENTRE VILLE",
                    "agencies": agencies_by_territory["territoire_dakar_ville"],
                    "totals": calculate_territory_totals(agencies_by_territory["territoire_dakar_ville"]),
                },
                "dakar_banlieue": {
                    "name": "DAKAR BANLIEUE",
                    "agencies": agencies_by_territory["territoire_dakar_banlieue"],
                    "totals": calculate_territory_totals(agencies_by_territory["territoire_dakar_banlieue"]),
                },
                "province_centre_sud": {
                    "name": "PROVINCE CENTRE SUD",
                    "agencies": agencies_by_territory["territoire_province_centre_sud"],
                    "totals": calculate_territory_totals(agencies_by_territory["territoire_province_centre_sud"]),
                },
                "province_nord": {
                    "name": "PROVINCE NORD",
                    "agencies": agencies_by_territory["territoire_province_nord"],
                    "totals": calculate_territory_totals(agencies_by_territory["territoire_province_nord"]),
                },
            }
        },
    }

    if grand_compte:
        response_data["grandCompte"] = grand_compte

    charge_affaire_by_agency: Dict[str, List[Dict[str, Any]]] = {}
    for ak, dct in charge_affaire_data.items():
        charge_affaire_by_agency[ak] = list(dct.values())
    response_data["chargeAffaireDetails"] = charge_affaire_by_agency

    return response_data


def get_collection_data(
    period: str = "month",
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Données de collection = agrégation des lignes domiciliation DASH (collecte net).
    Les soldes (onglet Solde) ne sont plus alimentés par l’ancienne requête FCUBS : affichage à 0
    tant qu’une source DASH dédiée n’est pas branchée.
    """
    logger.info(
        "🔍 get_collection_data (DASH) period=%s zone=%s month=%s year=%s date=%s",
        period,
        zone,
        month,
        year,
        date,
    )

    from services.cache_service import generate_cache_key, get_cache, set_cache

    cache_key = f"collection_dash:v1:{generate_cache_key(period, zone, month, year, date)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("✅ Collection (DASH) depuis cache")
        return cached

    raw = get_domiciliation_flux_data(
        period=period or "month",
        zone=zone,
        month=month,
        year=year,
        date=date,
    )
    rows = raw.get("data") or []
    if not isinstance(rows, list):
        rows = []

    response_data = _build_from_domiciliation_rows(rows)

    set_cache(cache_key, response_data, ttl=300)
    logger.info("✅ Collection (DASH) : %s lignes brutes → territoires", len(rows))
    return response_data
