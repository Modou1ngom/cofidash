"""
Collecte d'épargne à vue — Flexcube (CFSFCUBS145).
Retourne aussi une structure hiérarchique (territoire → agence → CAF → clients).
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any, Dict, List, Optional, Set

from database.oracle_pool import get_pool_flexcube
from services.collecte_epargne_a_vue_backup_service import (
    get_collecte_snapshot_meta,
    has_collecte_snapshot,
    load_collecte_snapshot_rows,
    refresh_collecte_epv_vue_snapshot,
)
from services.collecte_epargne_a_vue_query import COLLECTE_EPARGNE_A_VUE_QUERY
from services.objectif_epv_vue_backup_service import apply_frozen_objectifs
from services.utils import (
    get_territory_from_agency,
    get_territory_from_branch_code,
    get_territory_key,
    normalize_branch_code_for_territory,
)

logger = logging.getLogger(__name__)

_CALL_TIMEOUT_MS = 240_000

_TERRITORY_KEYS = (
    "territoire_dakar_ville",
    "territoire_dakar_banlieue",
    "territoire_province_centre_sud",
    "territoire_province_nord",
)

_TERRITORY_LABELS = {
    "territoire_dakar_ville": "TERRITOIRE DAKAR VILLE",
    "territoire_dakar_banlieue": "TERRITOIRE DAKAR BANLIEUE",
    "territoire_province_centre_sud": "TERRITOIRE PROVINCE CENTRE-SUD",
    "territoire_province_nord": "TERRITOIRE PROVINCE NORD",
}


def _month_bounds_iso(month: int, year: int) -> tuple[str, str]:
    """Début inclusif + fin exclusive (1er jour du mois suivant), YYYY-MM-DD."""
    date_debut = f"{year:04d}-{month:02d}-01"
    if month == 12:
        date_fin_exclusive = f"{year + 1:04d}-01-01"
    else:
        date_fin_exclusive = f"{year:04d}-{month + 1:02d}-01"
    return date_debut, date_fin_exclusive


def _f(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _tro(collecte: float, objectif: float) -> float:
    if objectif <= 0:
        return 0.0
    return round((collecte / objectif) * 100, 2)


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [str(col[0]).lower() for col in cursor.description]
    rows: List[Dict[str, Any]] = []
    for raw in cursor.fetchall():
        row: Dict[str, Any] = {}
        for key, value in zip(columns, raw):
            if hasattr(value, "isoformat"):
                try:
                    row[key] = value.isoformat()
                except Exception:
                    row[key] = str(value)
            elif value is not None and hasattr(value, "as_tuple"):
                try:
                    row[key] = float(value)
                except Exception:
                    row[key] = value
            else:
                row[key] = value
        rows.append(row)
    return rows


def _empty_metrics() -> Dict[str, float]:
    return {
        "cumMontantFinance": 0.0,
        "encoursCredit": 0.0,
        "mtEcheance": 0.0,
        "objectif": 0.0,
        "collecteM": 0.0,
        "totalDepot": 0.0,
        "tro": 0.0,
    }


def _finalize_metrics(m: Dict[str, float]) -> Dict[str, float]:
    m["tro"] = _tro(m["collecteM"], m["objectif"])
    return m


def _metrics_payload(cm: Dict[str, float]) -> Dict[str, float]:
    return {
        "cumMontantFinance": cm["cumMontantFinance"],
        "CUM_MONTANT_FINANCE": cm["cumMontantFinance"],
        "encoursCredit": cm["encoursCredit"],
        "ENCOURS_CREDIT": cm["encoursCredit"],
        "CUM_ENCOURS_CREDIT": cm["encoursCredit"],
        "mtEcheance": cm["mtEcheance"],
        "MT_ECHEANCE": cm["mtEcheance"],
        "MONTANT_ECHEANCE": cm["mtEcheance"],
        "objectif": cm["objectif"],
        "OBJECTIF": cm["objectif"],
        "OBJ_COL_EPV_VUE": cm["objectif"],
        "collecteM": cm["collecteM"],
        "COLLECTE_M": cm["collecteM"],
        "COL_EP_VUE": cm["collecteM"],
        "totalDepot": cm["totalDepot"],
        "TOTAL_DEPOT": cm["totalDepot"],
        "tro": cm["tro"],
        "TRO": cm["tro"],
    }


def _build_hierarchical(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrège territoire → agence → CAF → clients.
    Objectif / encours / mt financé : somme des lignes.
    Échéance / dépôt / collecte : dédoublonnés par matricule.
    """
    agencies: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        branch_code = normalize_branch_code_for_territory(row.get("code_agence"))
        if not branch_code:
            continue

        agency_name = (row.get("branch_name") or branch_code or "").strip()
        code_caf = str(row.get("code_caf") or "-").strip() or "-"
        charge = (row.get("charge_affaire") or "-").strip() or "-"
        matricule = str(row.get("matricule_client") or "").strip()
        numero_compte = str(row.get("numero_compte") or "").strip()
        nom_client = (row.get("nom_client") or "").strip()

        if branch_code not in agencies:
            agencies[branch_code] = {
                "BRANCH_CODE": branch_code,
                "branch_code": branch_code,
                "BRANCH_NAME": agency_name,
                "name": agency_name,
                "AGENCE": agency_name,
                "metrics": _empty_metrics(),
                "clients_seen": set(),
                "charges": {},
            }

        agency = agencies[branch_code]
        if agency_name and agency["name"] in ("", branch_code):
            agency["name"] = agency_name
            agency["BRANCH_NAME"] = agency_name
            agency["AGENCE"] = agency_name

        if code_caf not in agency["charges"]:
            agency["charges"][code_caf] = {
                "codeGestion": code_caf,
                "CODE_GESTION": code_caf,
                "chargeAffaire": charge,
                "CHARGE_AFFAIRE": charge,
                "metrics": _empty_metrics(),
                "clients_seen": set(),
                "clients": [],
            }

        charge_bucket = agency["charges"][code_caf]
        if charge and charge != "-" and charge_bucket["chargeAffaire"] in ("-", ""):
            charge_bucket["chargeAffaire"] = charge
            charge_bucket["CHARGE_AFFAIRE"] = charge

        obj = _f(row.get("obj_col_epv_vue"))
        encours = _f(row.get("cum_encours_credit"))
        finance = _f(row.get("cum_montant_finance"))
        echeance = _f(row.get("montant_echeance"))
        depot = _f(row.get("total_depot"))
        collecte = _f(row.get("col_ep_vue"))

        for bucket in (agency, charge_bucket):
            bucket["metrics"]["objectif"] += obj
            bucket["metrics"]["encoursCredit"] += encours
            bucket["metrics"]["cumMontantFinance"] += finance

        if matricule and matricule not in charge_bucket["clients_seen"]:
            charge_bucket["clients_seen"].add(matricule)
            charge_bucket["metrics"]["mtEcheance"] += echeance
            charge_bucket["metrics"]["totalDepot"] += depot
            charge_bucket["metrics"]["collecteM"] += collecte

        if matricule and matricule not in agency["clients_seen"]:
            agency["clients_seen"].add(matricule)
            agency["metrics"]["mtEcheance"] += echeance
            agency["metrics"]["totalDepot"] += depot
            agency["metrics"]["collecteM"] += collecte

        charge_bucket["clients"].append(
            {
                "CODE_AGENCE": branch_code,
                "BRANCH_NAME": agency_name,
                "CODE_CAF": code_caf,
                "CHARGE_AFFAIRE": charge,
                "MATRICULE_CLIENT": matricule,
                "matriculeClient": matricule,
                "NUMERO_COMPTE": numero_compte,
                "numeroCompte": numero_compte,
                "NOM_CLIENT": nom_client,
                "nomClient": nom_client,
                "CUM_MONTANT_FINANCE": finance,
                "cumMontantFinance": finance,
                "CUM_ENCOURS_CREDIT": encours,
                "encoursCredit": encours,
                "OBJ_COL_EPV_VUE": obj,
                "objectif": obj,
                "MONTANT_ECHEANCE": echeance,
                "mtEcheance": echeance,
                "TOTAL_DEPOT": depot,
                "totalDepot": depot,
                "COL_EP_VUE": collecte,
                "collecteM": collecte,
                "tro": _tro(collecte, obj),
                "TRO": _tro(collecte, obj),
            }
        )

    by_territory: Dict[str, List[Dict[str, Any]]] = {k: [] for k in _TERRITORY_KEYS}
    grand_compte = None

    for branch_code, agency in agencies.items():
        metrics = _finalize_metrics(agency["metrics"])
        charge_lines = []
        for caf in sorted(agency["charges"].values(), key=lambda c: str(c["codeGestion"])):
            cm = _finalize_metrics(caf["metrics"])
            clients = sorted(
                caf["clients"],
                key=lambda c: (str(c.get("NOM_CLIENT") or ""), str(c.get("MATRICULE_CLIENT") or "")),
            )
            charge_lines.append(
                {
                    "codeGestion": caf["codeGestion"],
                    "CODE_GESTION": caf["CODE_GESTION"],
                    "CODE_CAF": caf["codeGestion"],
                    "chargeAffaire": caf["chargeAffaire"],
                    "CHARGE_AFFAIRE": caf["CHARGE_AFFAIRE"],
                    **_metrics_payload(cm),
                    "clients": clients,
                }
            )

        agency_obj = {
            "BRANCH_CODE": agency["BRANCH_CODE"],
            "branch_code": agency["branch_code"],
            "BRANCH_NAME": agency["BRANCH_NAME"],
            "name": agency["name"],
            "AGENCE": agency["AGENCE"],
            **_metrics_payload(metrics),
            "chargeAffaireDetails": charge_lines,
        }

        name_upper = (agency["name"] or "").upper()
        if "GRAND COMPTE" in name_upper or branch_code == "526":
            grand_compte = agency_obj
            continue

        territory = get_territory_from_branch_code(branch_code)
        if territory is None:
            territory = get_territory_from_agency(agency["name"])

        if territory is None or territory == "POINT SERVICES":
            territory_key = "territoire_dakar_ville"
        else:
            territory_key = get_territory_key(territory)
            if territory_key not in by_territory:
                territory_key = "territoire_dakar_ville"

        by_territory[territory_key].append(agency_obj)

    def territory_totals(agency_list: List[Dict[str, Any]]) -> Dict[str, float]:
        totals = _empty_metrics()
        for a in agency_list:
            totals["cumMontantFinance"] += _f(a.get("cumMontantFinance"))
            totals["encoursCredit"] += _f(a.get("encoursCredit"))
            totals["mtEcheance"] += _f(a.get("mtEcheance"))
            totals["objectif"] += _f(a.get("objectif"))
            totals["collecteM"] += _f(a.get("collecteM"))
            totals["totalDepot"] += _f(a.get("totalDepot"))
        return _finalize_metrics(totals)

    hierarchical: Dict[str, Any] = {"TERRITOIRE": {}, "POINT SERVICES": {}}

    for key in _TERRITORY_KEYS:
        agencies_list = sorted(by_territory[key], key=lambda a: str(a.get("name") or ""))
        hierarchical["TERRITOIRE"][key] = {
            "name": _TERRITORY_LABELS[key],
            "agencies": agencies_list,
            "totals": territory_totals(agencies_list),
        }

    if grand_compte:
        hierarchical["TERRITOIRE"]["grand_compte"] = {
            "name": "GRAND COMPTE",
            "agencies": [grand_compte],
            "totals": {
                "cumMontantFinance": _f(grand_compte.get("cumMontantFinance")),
                "encoursCredit": _f(grand_compte.get("encoursCredit")),
                "mtEcheance": _f(grand_compte.get("mtEcheance")),
                "objectif": _f(grand_compte.get("objectif")),
                "collecteM": _f(grand_compte.get("collecteM")),
                "totalDepot": _f(grand_compte.get("totalDepot")),
                "tro": _f(grand_compte.get("tro")),
            },
        }

    return hierarchical


def get_collecte_epargne_a_vue_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    refresh: bool = False,
) -> Dict[str, Any]:
    """
    Lignes client + structure hiérarchique pour le dashboard DEPOT.

    Par défaut lit le snapshot SQLite du matin (06h).
    refresh=True force un recalcul Flexcube + mise à jour du snapshot.
    """
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    if m < 1 or m > 12:
        raise ValueError(f"Mois invalide: {m}")

    date_debut, date_fin_exclusive = _month_bounds_iso(m, y)
    started = time.monotonic()
    data_source = "snapshot"
    snapshot_meta: Optional[Dict[str, Any]] = None

    if refresh or not has_collecte_snapshot(m, y):
        if refresh:
            logger.info(
                "🔄 collecte-epargne-a-vue REFRESH forcé month=%s year=%s",
                m,
                y,
            )
        else:
            logger.info(
                "⚠️ Pas de snapshot collecte EPV vue pour %04d-%02d — calcul Flexcube",
                y,
                m,
            )
        refresh_collecte_epv_vue_snapshot(month=m, year=y)
        data_source = "refreshed" if refresh else "live_then_cached"

    rows = load_collecte_snapshot_rows(m, y)
    snapshot_meta = get_collecte_snapshot_meta(m, y)
    if snapshot_meta:
        date_debut = snapshot_meta.get("date_debut") or date_debut
        date_fin_exclusive = snapshot_meta.get("date_fin_exclusive") or date_fin_exclusive

    logger.info(
        "📦 collecte-epargne-a-vue source=%s month=%s year=%s rows=%s",
        data_source,
        m,
        y,
        len(rows),
    )

    rows, objectifs_meta = apply_frozen_objectifs(rows, m, y)
    if objectifs_meta.get("objectifs_figes"):
        logger.info(
            "📌 Objectifs figés appliqués (%s/%s lignes)",
            objectifs_meta.get("objectifs_applied"),
            objectifs_meta.get("objectifs_snapshot_rows"),
        )
    else:
        logger.info("⚠️ Objectifs live (aucun snapshot objectifs pour %04d-%02d)", y, m)

    elapsed = time.monotonic() - started
    hierarchical = _build_hierarchical(rows)
    logger.info(
        "✅ collecte-epargne-a-vue: %s lignes, hiérarchie OK en %.1fs (source=%s)",
        len(rows),
        elapsed,
        data_source,
    )

    total_objectif = sum(_f(r.get("obj_col_epv_vue")) for r in rows)
    total_finance = sum(_f(r.get("cum_montant_finance")) for r in rows)
    total_encours = sum(_f(r.get("cum_encours_credit")) for r in rows)
    seen: Set[str] = set()
    total_depot = 0.0
    total_col = 0.0
    total_echeance = 0.0
    for r in rows:
        mat = str(r.get("matricule_client") or "")
        if mat and mat in seen:
            continue
        if mat:
            seen.add(mat)
        total_depot += _f(r.get("total_depot"))
        total_col += _f(r.get("col_ep_vue"))
        total_echeance += _f(r.get("montant_echeance"))

    return {
        "data": rows,
        "hierarchicalData": hierarchical,
        "count": len(rows),
        "month": m,
        "year": y,
        "date_debut": date_debut,
        "date_fin_exclusive": date_fin_exclusive,
        "elapsed_seconds": round(elapsed, 2),
        "data_source": data_source,
        "data_snapshot": snapshot_meta,
        **objectifs_meta,
        "totals": {
            "cum_montant_finance": total_finance,
            "cum_encours_credit": total_encours,
            "obj_col_epv_vue": total_objectif,
            "montant_echeance": total_echeance,
            "total_depot": total_depot,
            "col_ep_vue": total_col,
            "tro": _tro(total_col, total_objectif),
        },
    }
