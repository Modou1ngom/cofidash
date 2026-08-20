"""
Service pour la gestion des données de portefeuille à risque (PAR)
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime, date
import calendar
from database.oracle_pool import get_pool_flexcube
from services.cache_service import TTL_DASHBOARD, generate_cache_key, get_cache, set_cache
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key, get_all_territories
from services.portefeuille_risque_global_query import (
    PORTEFEUILLE_GLOBAL_QUERY,
    PORTEFEUILLE_AGENCE_QUERY,
)

logger = logging.getLogger(__name__)


def _as_of_date_str(y: int, m: int) -> str:
    last_day = calendar.monthrange(y, m)[1]
    as_of = date(y, m, last_day)
    today = datetime.now().date()
    if as_of > today:
        as_of = today
    return as_of.strftime("%d/%m/%Y")


def _resolve_as_of_dates(
    month: Optional[int],
    year: Optional[int],
    month_ref: Optional[int],
    year_ref: Optional[int],
):
    if month is None or year is None:
        now = datetime.now()
        month = month or now.month
        year = year or now.year

    if month_ref is not None and year_ref is not None:
        month_m1, year_m1 = month_ref, year_ref
    elif month == 1:
        month_m1, year_m1 = 12, year - 1
    else:
        month_m1, year_m1 = month - 1, year

    return _as_of_date_str(year, month), _as_of_date_str(year_m1, month_m1)


def _run_par_query(sql: str, as_of_date: str) -> List[Dict]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 180_000
            cursor.execute(sql, {"as_of_date": as_of_date})
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()


def _safe_float(r: dict, *keys) -> float:
    if not r:
        return 0.0
    for k in keys:
        if k in r and r[k] is not None:
            try:
                return float(r[k])
            except (TypeError, ValueError):
                pass
    return 0.0


def _pct(enc, num):
    return round((num / enc * 100), 2) if enc else 0


def get_portefeuille_risque_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    month_ref: Optional[int] = None,
    year_ref: Optional[int] = None
):
    """
    Récupère les données de portefeuille à risque (PAR) depuis Oracle
    
    Args:
        month: Mois en cours (1-12). Si non fourni, utilise le mois courant.
        year: Année du mois en cours. Si non fourni, utilise l'année courante.
        month_ref: Mois de référence (1-12). Si non fourni, utilise le mois précédent du mois en cours.
        year_ref: Année du mois de référence. Si non fourni, déduite du mois en cours.
    
    Returns:
        Dictionnaire avec les données PAR organisées par territoires et agences
    """
    logger.info(f"🔍 get_portefeuille_risque_data appelé avec month={month}, year={year}, month_ref={month_ref}, year_ref={year_ref}")

    date_m_str, date_m1_str = _resolve_as_of_dates(month, year, month_ref, year_ref)
    cache_key = f"par-agence:{generate_cache_key(date_m_str, date_m1_str)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ PAR agence cache hit M=%s M-1=%s", date_m_str, date_m1_str)
        return cached
    logger.info("📅 PAR AGENCE — Flexcube live: M=%s, M-1=%s", date_m_str, date_m1_str)

    try:
        logger.info("🔍 Exécution requête PAR AGENCE (arrêté M=%s)...", date_m_str)
        rows_m = _run_par_query(PORTEFEUILLE_AGENCE_QUERY, date_m_str)
        logger.info("🔍 Exécution requête PAR AGENCE (arrêté M-1=%s)...", date_m1_str)
        rows_m1 = _run_par_query(PORTEFEUILLE_AGENCE_QUERY, date_m1_str)

        key_m1_code = {(r.get("BRANCH_CODE") or "").strip(): r for r in rows_m1}
        key_m1_name = {((r.get("BRANCH_NAME") or "").strip() or "-"): r for r in rows_m1}

        agency_rows = []
        seen = set()
        for r in rows_m:
            branch = (r.get("BRANCH_NAME") or "").strip() or "-"
            code = (r.get("BRANCH_CODE") or "").strip()
            r1 = key_m1_code.get(code) or key_m1_name.get(branch)
            enc_m = _safe_float(r, "ENCOURS_TOTAL")
            enc_m1 = _safe_float(r1, "ENCOURS_TOTAL") if r1 else 0.0
            agency_rows.append({
                "AGENCE": branch,
                "CODE_AGENCE": code,
                "ENCOURS_M": enc_m,
                "ENCOURS_M_1": enc_m1,
                "PROVISIONS": _safe_float(r, "PROVISION_TOTAL"),
                "NBRE_DOSSIERS": int(_safe_float(r, "NOMBRE_DOSSIER")),
                "PAR_0_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_0") if r1 else 0),
                "PAR_0_M": _pct(enc_m, _safe_float(r, "ENCOURS_PAR_0")),
                "PAR_30_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_30") if r1 else 0),
                "PAR_30_M": _pct(enc_m, _safe_float(r, "ENCOURS_PAR_30")),
                "PAR_90_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_90") if r1 else 0),
                "PAR_90_M": _pct(enc_m, _safe_float(r, "ENCOURS_PAR_90")),
                "PAR_180_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_180") if r1 else 0),
                "PAR_180_M": _pct(enc_m, _safe_float(r, "ENCOURS_PAR_180")),
                "PAR_360_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_360") if r1 else 0),
                "PAR_360_M": _pct(enc_m, _safe_float(r, "ENCOURS_PAR_360")),
            })
            seen.add(code or branch)

        for r1 in rows_m1:
            branch = (r1.get("BRANCH_NAME") or "").strip() or "-"
            code = (r1.get("BRANCH_CODE") or "").strip()
            if (code or branch) in seen:
                continue
            enc_m1 = _safe_float(r1, "ENCOURS_TOTAL")
            agency_rows.append({
                "AGENCE": branch,
                "CODE_AGENCE": code,
                "ENCOURS_M": 0.0,
                "ENCOURS_M_1": enc_m1,
                "PROVISIONS": 0.0,
                "NBRE_DOSSIERS": 0,
                "PAR_0_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_0")),
                "PAR_0_M": 0.0,
                "PAR_30_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_30")),
                "PAR_30_M": 0.0,
                "PAR_90_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_90")),
                "PAR_90_M": 0.0,
                "PAR_180_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_180")),
                "PAR_180_M": 0.0,
                "PAR_360_M_1": _pct(enc_m1, _safe_float(r1, "ENCOURS_PAR_360")),
                "PAR_360_M": 0.0,
            })

        logger.info(
            "✅ PAR AGENCE: %d lignes M, %d M-1, %d agences",
            len(rows_m),
            len(rows_m1),
            len(agency_rows),
        )

        # Organiser les données en structure hiérarchique (à partir des lignes agence)
        try:
            hierarchical_data = organize_par_data(agency_rows)
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'organisation des données PAR: {str(e)}", exc_info=True)
            # Retourner les données brutes même si l'organisation échoue
            hierarchical_data = {
                "TERRITOIRE": {},
                "POINT SERVICES": {}
            }
        
        payload = {
            "data": agency_rows,
            "hierarchicalData": hierarchical_data
        }
        set_cache(cache_key, payload, TTL_DASHBOARD)
        return payload
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"❌ Erreur lors de la récupération des données PAR: {str(e)}\n{error_detail}", exc_info=True)
        raise


def _fetch_caf_raw_rows(
    month: Optional[int],
    year: Optional[int],
    month_ref: Optional[int],
    year_ref: Optional[int],
) -> List[Dict]:
    """Lignes PAR par CAF (agence + code gestionnaire) pour l'onglet PAR | CAF."""
    date_m_str, date_m1_str = _resolve_as_of_dates(month, year, month_ref, year_ref)
    cache_key = f"par-caf-raw:{generate_cache_key(date_m_str, date_m1_str)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ PAR CAF cache hit M=%s M-1=%s", date_m_str, date_m1_str)
        return cached
    logger.info("📅 PAR CAF — Flexcube live: M=%s, M-1=%s", date_m_str, date_m1_str)

    logger.info("🔍 Exécution requête PAR CAF (arrêté M=%s)...", date_m_str)
    rows_m = _run_par_query(PORTEFEUILLE_GLOBAL_QUERY, date_m_str)
    logger.info("🔍 Exécution requête PAR CAF (arrêté M-1=%s)...", date_m1_str)
    rows_m1 = _run_par_query(PORTEFEUILLE_GLOBAL_QUERY, date_m1_str)

    key_m1 = {
        (
            (r.get("BRANCH_NAME") or "").strip() or "-",
            (r.get("CODE_GESTION_PRET") or "").strip() or "",
        ): r
        for r in rows_m1
    }

    raw_data = []
    for r in rows_m:
        branch = (r.get("BRANCH_NAME") or "").strip() or "-"
        code = (r.get("CODE_GESTION_PRET") or "").strip() or ""
        r1 = key_m1.get((branch, code))
        raw_data.append({
            "AGENCE": branch,
            "CODE_AGENCE": (r.get("BRANCH_CODE") or "").strip(),
            "CHARGE_AFFAIRE": r.get("CHARGE_AFFAIRE") or "",
            "CODE_GESTION_PRET": code,
            "ENCOURS_TOTAL": _safe_float(r, "ENCOURS_TOTAL"),
            "ENCOURS_IMPAYE": _safe_float(r, "ENCOURS_IMPAYE"),
            "NOMBRE_DOSSIER": int(_safe_float(r, "NOMBRE_DOSSIER")),
            "NOMBRE_DOSSIER_IMP": int(_safe_float(r, "NOMBRE_DOSSIER_IMP")),
            "RATIO_ENCOURS_IMPAYE": _safe_float(r, "RATIO_ENCOURS_IMPAYE"),
            "RATIO_NOMBRE_IMPAYE": _safe_float(r, "RATIO_NOMBRE_IMPAYE"),
            "PAR_0_M_1": _safe_float(r1, "ENCOURS_PAR_0") if r1 else 0,
            "PAR_0_M": _safe_float(r, "ENCOURS_PAR_0"),
            "PAR_30_M_1": _safe_float(r1, "ENCOURS_PAR_30") if r1 else 0,
            "PAR_30_M": _safe_float(r, "ENCOURS_PAR_30"),
            "PAR_90_M_1": _safe_float(r1, "ENCOURS_PAR_90") if r1 else 0,
            "PAR_90_M": _safe_float(r, "ENCOURS_PAR_90"),
            "PAR_180_M_1": _safe_float(r1, "ENCOURS_PAR_180") if r1 else 0,
            "PAR_180_M": _safe_float(r, "ENCOURS_PAR_180"),
            "PAR_360_M_1": _safe_float(r1, "ENCOURS_PAR_360") if r1 else 0,
            "PAR_360_M": _safe_float(r, "ENCOURS_PAR_360"),
        })

    logger.info("✅ PAR CAF: %d lignes M, %d M-1, %d CAF", len(rows_m), len(rows_m1), len(raw_data))
    set_cache(cache_key, raw_data, TTL_DASHBOARD)
    return raw_data


def get_portefeuille_risque_caf_data(
    agency: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    month_ref: Optional[int] = None,
    year_ref: Optional[int] = None
) -> List[Dict]:
    """
    Agrège les données PAR par CAF (chargé d'affaires).
    Si agency est fourni, filtre sur cette agence ; sinon retourne tous les CAF de toutes les agences.
    """
    agency_str = (agency or "").strip()
    all_agencies = not agency_str or agency_str.upper() in ("ALL", "TOUTES", "TOUTES LES AGENCES", "")
    logger.info(
        "🔍 get_portefeuille_risque_caf_data appelé agency=%s (toutes=%s), month=%s, year=%s, month_ref=%s, year_ref=%s",
        agency_str or "(toutes)", all_agencies, month, year, month_ref, year_ref
    )

    try:
        raw_data = _fetch_caf_raw_rows(month, year, month_ref, year_ref)
    except Exception as e:
        logger.error("❌ Requête PAR CAF a échoué: %s", e, exc_info=True)
        raise

    # Filtrer sur l'agence si une agence est choisie
    if all_agencies:
        filtered_rows = raw_data
        logger.info("ℹ️ Mode toutes agences : %d lignes PAR", len(filtered_rows))
    else:
        agency_upper = " ".join(agency_str.upper().split())
        agency_tokens = agency_upper.split()
        agency_last = agency_tokens[-1] if agency_tokens else ""
        filtered_rows = []
        for row in raw_data:
            agence_name_raw = str(row.get("AGENCE") or "").strip().upper()
            agence_name = " ".join(agence_name_raw.split())
            row_tokens = agence_name.split()
            row_last = row_tokens[-1] if row_tokens else ""
            if not agence_name:
                continue
            if (
                agence_name == agency_upper
                or agency_upper in agence_name
                or agence_name in agency_upper
                or (agency_last and row_last == agency_last)
            ):
                filtered_rows.append(row)
        if not filtered_rows:
            logger.info("ℹ️ Aucune ligne PAR trouvée pour l'agence %s", agency_str)
            return []

    # Agrégation par CHARGE_AFFAIRE
    # On calcule les montants PAR (PAR_0_M, PAR_30_M, ...) puis le % du portefeuille (encours) pour chaque palier
    def safe_float(v: object) -> float:
        try:
            return float(v or 0)
        except (TypeError, ValueError):
            return 0.0

    def row_val(r: dict, *key_variants: str) -> float:
        """Récupère une valeur dans la ligne en essayant plusieurs clés (casse variable Oracle)."""
        for k in key_variants:
            if k in r and r[k] is not None:
                return safe_float(r[k])
        target = (key_variants[0] or "").upper()
        for k in r:
            if (k or "").upper() == target:
                return safe_float(r[k])
        return 0.0

    # En mode "toutes agences", grouper par (agence, CAF) pour avoir une ligne par CAF par agence.
    # Sinon grouper par CAF uniquement (une agence = un CAF peut n'apparaître qu'une fois).
    caf_map: Dict = {}  # clé = (agence, caf_name) si all_agencies, sinon caf_name

    for row in filtered_rows:
        agence_name = str(row.get("AGENCE") or "").strip() or "-"
        caf_name = row.get("CHARGE_AFFAIRE") or row.get("charge_affaire") or "-"
        caf_name_str = str(caf_name).strip() or "-"

        if all_agencies:
            key = (agence_name, caf_name_str)
        else:
            key = caf_name_str

        if key not in caf_map:
            caf_map[key] = {
                "agence": agence_name if all_agencies else "",
                "nbre_dossiers": 0,
                "nombre_dossier_query": 0,
                "nombre_dossier_imp": 0,
                "encours_credit": 0.0,
                "encours_impaye_sum": 0.0,
                "ratio_nombre_impaye_weighted": 0.0,
                "par0_montant": 0.0,
                "par30_montant": 0.0,
                "par90_montant": 0.0,
                "par180_montant": 0.0,
                "par360_montant": 0.0,
            }

        agg = caf_map[key]
        agg["nbre_dossiers"] += 1
        agg["nombre_dossier_query"] += int(row_val(row, "NOMBRE_DOSSIER", "nombre_dossier") or 0)
        agg["nombre_dossier_imp"] += int(row_val(row, "NOMBRE_DOSSIER_IMP", "nombre_dossier_imp") or 0)
        enc_imp = row_val(row, "ENCOURS_IMPAYE", "encours_impaye")
        ratio_nb = row_val(row, "RATIO_NOMBRE_IMPAYE", "ratio_nombre_impaye")
        agg["encours_impaye_sum"] += enc_imp

        par0_m = row_val(row, "PAR_0_M", "par_0_m")
        par30_m = row_val(row, "PAR_30_M", "par_30_m")
        par90_m = row_val(row, "PAR_90_M", "par_90_m")
        par180_m = row_val(row, "PAR_180_M", "par_180_m")
        par360_m = row_val(row, "PAR_360_M", "par_360_m")

        encours_ligne = row_val(row, "ENCOURS_TOTAL", "encours_total")
        if encours_ligne <= 0:
            encours_ligne = par0_m + par30_m + par90_m + par180_m + par360_m
        agg["encours_credit"] += encours_ligne
        if encours_ligne > 0:
            agg["ratio_nombre_impaye_weighted"] += ratio_nb * encours_ligne
        agg["par0_montant"] += par0_m
        agg["par30_montant"] += par30_m
        agg["par90_montant"] += par90_m
        agg["par180_montant"] += par180_m
        agg["par360_montant"] += par360_m

    # Construire la liste finale : PAR en % de l'encours (niveau de risque, pas variation)
    caf_list: List[Dict] = []
    for key, agg in caf_map.items():
        caf_name = key[1] if isinstance(key, tuple) else key
        encours = agg["encours_credit"] or 0
        if encours > 0:
            par0 = (agg["par0_montant"] / encours) * 100
            par30 = (agg["par30_montant"] / encours) * 100
            par90 = (agg["par90_montant"] / encours) * 100
            par180 = (agg["par180_montant"] / encours) * 100
            par360 = (agg["par360_montant"] / encours) * 100
        else:
            par0 = par30 = par90 = par180 = par360 = 0.0

        encours = agg["encours_credit"] or 0
        encours_impaye_sum = agg.get("encours_impaye_sum") or 0
        nbre_dossiers = int(agg["nombre_dossier_query"] or agg["nbre_dossiers"] or 0)
        nbre_dossiers_imp = int(agg.get("nombre_dossier_imp") or 0)
        ratio_encours_impaye = round((encours_impaye_sum / encours * 100), 2) if encours > 0 else 0.0
        ratio_nombre_impaye = (
            round((nbre_dossiers_imp / nbre_dossiers) * 100, 2) if nbre_dossiers > 0 else 0.0
        )

        item = {
            "nom": caf_name,
            "nbreDossiers": nbre_dossiers,
            "nbreDossiersImpayes": nbre_dossiers_imp,
            "encoursCredit": float(encours),
            "encoursPar0": round(agg["par0_montant"], 2),
            "encoursPar30": round(agg["par30_montant"], 2),
            "encoursPar90": round(agg["par90_montant"], 2),
            "encoursPar180": round(agg["par180_montant"], 2),
            "encoursPar360": round(agg["par360_montant"], 2),
            "encoursImpayes": round(encours_impaye_sum, 2),
            "ratioEncoursImpayes": ratio_encours_impaye,
            "ratioNbreImpayes": ratio_nombre_impaye,
            "par0": round(par0, 2),
            "par30": round(par30, 2),
            "par90": round(par90, 2),
            "par180": round(par180, 2),
            "par360": round(par360, 2),
        }
        if all_agencies and agg.get("agence"):
            item["agence"] = agg["agence"]
        caf_list.append(item)

    logger.info("✅ %d CAF agrégés%s", len(caf_list), f" pour l'agence {agency_str}" if not all_agencies else " (toutes agences)")
    return caf_list


def _is_grand_compte_agency_name(agency_name: str) -> bool:
    """Détecte l’agence « Grand compte » (même logique que les autres services)."""
    if not agency_name:
        return False
    n = " ".join(str(agency_name).upper().split())
    return "GRAND COMPTE" in n or "GRAND COMPTES" in n or "GRAND_COMPTE" in n


def organize_par_data(raw_data: List[Dict]) -> Dict:
    """
    Organise les données PAR en structure hiérarchique (points de service sous TERRITOIRE DAKAR VILLE)
    
    Args:
        raw_data: Liste de dictionnaires avec les données brutes
        
    Returns:
        Dictionnaire avec la structure hiérarchique
    """
    hierarchical = {
        "TERRITOIRE": {},
        "POINT SERVICES": {}
    }
    
    # Grouper par agence
    agencies_map = {}
    
    for row in raw_data:
        agency_name = row.get('AGENCE') or '-'
        code_agency = row.get('CODE_AGENCE') or ''
        
        if not agencies_map.get(agency_name):
            agencies_map[agency_name] = {
                "name": agency_name,
                "code": code_agency,
                "data": [],
                "totals": {
                    "par0M1": 0, "par0M": 0, "par0Ecart": 0, "par0Percent": 0,
                    "par30M1": 0, "par30M": 0, "par30Ecart": 0, "par30Percent": 0,
                    "par90M1": 0, "par90M": 0, "par90Ecart": 0, "par90Percent": 0,
                    "par180M1": 0, "par180M": 0, "par180Ecart": 0, "par180Percent": 0,
                    "par360M1": 0, "par360M": 0, "par360Ecart": 0, "par360Percent": 0,
                    "nbreDossiers": 0,
                    "encoursM": 0,
                    "encoursM1": 0,
                    "provisions": 0
                }
            }
        
        agencies_map[agency_name]["data"].append(row)
        
        # Agréger les totaux (gérer les valeurs None)
        try:
            agencies_map[agency_name]["totals"]["nbreDossiers"] += int(row.get("NBRE_DOSSIERS") or row.get("NOMBRE_DOSSIER") or 0)
            agencies_map[agency_name]["totals"]["encoursM"] += float(row.get("ENCOURS_M") or 0)
            agencies_map[agency_name]["totals"]["encoursM1"] += float(row.get("ENCOURS_M_1") or 0)
            agencies_map[agency_name]["totals"]["provisions"] += float(row.get("PROVISIONS") or 0)
            agencies_map[agency_name]["totals"]["par0M1"] += float(row.get('PAR_0_M_1') or 0)
            agencies_map[agency_name]["totals"]["par0M"] += float(row.get('PAR_0_M') or 0)
            agencies_map[agency_name]["totals"]["par30M1"] += float(row.get('PAR_30_M_1') or 0)
            agencies_map[agency_name]["totals"]["par30M"] += float(row.get('PAR_30_M') or 0)
            agencies_map[agency_name]["totals"]["par90M1"] += float(row.get('PAR_90_M_1') or 0)
            agencies_map[agency_name]["totals"]["par90M"] += float(row.get('PAR_90_M') or 0)
            agencies_map[agency_name]["totals"]["par180M1"] += float(row.get('PAR_180_M_1') or 0)
            agencies_map[agency_name]["totals"]["par180M"] += float(row.get('PAR_180_M') or 0)
            agencies_map[agency_name]["totals"]["par360M1"] += float(row.get('PAR_360_M_1') or 0)
            agencies_map[agency_name]["totals"]["par360M"] += float(row.get('PAR_360_M') or 0)
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Erreur lors de l'agrégation des totaux pour {agency_name}: {e}")
            continue
    
    # Calculer les écarts et pourcentages pour chaque agence
    for agency in agencies_map.values():
        agency["totals"]["par0Ecart"] = agency["totals"]["par0M"] - agency["totals"]["par0M1"]
        agency["totals"]["par30Ecart"] = agency["totals"]["par30M"] - agency["totals"]["par30M1"]
        agency["totals"]["par90Ecart"] = agency["totals"]["par90M"] - agency["totals"]["par90M1"]
        agency["totals"]["par180Ecart"] = agency["totals"]["par180M"] - agency["totals"]["par180M1"]
        agency["totals"]["par360Ecart"] = agency["totals"]["par360M"] - agency["totals"]["par360M1"]
        
        # Calculer les pourcentages (variation en pourcentage)
        if agency["totals"]["par0M1"] != 0:
            agency["totals"]["par0Percent"] = (agency["totals"]["par0Ecart"] / agency["totals"]["par0M1"]) * 100
        if agency["totals"]["par30M1"] != 0:
            agency["totals"]["par30Percent"] = (agency["totals"]["par30Ecart"] / agency["totals"]["par30M1"]) * 100
        if agency["totals"]["par90M1"] != 0:
            agency["totals"]["par90Percent"] = (agency["totals"]["par90Ecart"] / agency["totals"]["par90M1"]) * 100
        if agency["totals"]["par180M1"] != 0:
            agency["totals"]["par180Percent"] = (agency["totals"]["par180Ecart"] / agency["totals"]["par180M1"]) * 100
        if agency["totals"]["par360M1"] != 0:
            agency["totals"]["par360Percent"] = (agency["totals"]["par360Ecart"] / agency["totals"]["par360M1"]) * 100
    
    # Organiser par territoire et points de service
    for agency_name, agency_data in agencies_map.items():
        if _is_grand_compte_agency_name(agency_name):
            continue

        # Vérifier d'abord si c'est un point de service
        from services.utils import SERVICE_POINT_MAPPING
        
        is_service_point = False
        normalized_name = ' '.join(str(agency_name).upper().split())
        
        # Vérifier si c'est un point de service en comparant avec SERVICE_POINT_MAPPING
        for service_point_name in SERVICE_POINT_MAPPING.keys():
            service_point_str = str(service_point_name) if service_point_name else ''
            service_point_normalized = ' '.join(service_point_str.upper().split())
            
            # Normaliser aussi en supprimant les préfixes comme "C-E" pour comparaison
            agency_name_without_prefix = normalized_name.replace('C-E ', '').replace('CE ', '').strip()
            service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
            
            # Vérifier plusieurs conditions pour une meilleure détection
            if (service_point_normalized == normalized_name or 
                service_point_without_prefix == agency_name_without_prefix or
                service_point_normalized in normalized_name or 
                normalized_name in service_point_normalized or
                (service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5) or
                (agency_name_without_prefix in service_point_without_prefix and len(agency_name_without_prefix) > 5)):
                is_service_point = True
                logger.info(f"✅ Point de service identifié (PAR): {agency_name} -> {service_point_name}")
                break
        
        if is_service_point:
            territory_key = "territoire_dakar_ville"
            territory_name = get_all_territories()["territoire_dakar_ville"]["name"]
        else:
            territory_name = get_territory_from_agency(agency_name)
            if territory_name:
                territory_key = get_territory_key(territory_name)
            else:
                code = agency_data.get('code', '')
                if code:
                    territory_name = get_territory_from_branch_code(code)
                    if territory_name:
                        territory_key = get_territory_key(territory_name)
                    else:
                        territory_key = "territoire_autre"
                        territory_name = agency_name
                else:
                    territory_key = "territoire_autre"
                    territory_name = agency_name
        
        if not hierarchical["TERRITOIRE"].get(territory_key):
            hierarchical["TERRITOIRE"][territory_key] = {
                "name": territory_name,
                "agencies": [],
                "totals": {
                    "par0M1": 0, "par0M": 0, "par0Ecart": 0, "par0Percent": 0,
                    "par30M1": 0, "par30M": 0, "par30Ecart": 0, "par30Percent": 0,
                    "par90M1": 0, "par90M": 0, "par90Ecart": 0, "par90Percent": 0,
                    "par180M1": 0, "par180M": 0, "par180Ecart": 0, "par180Percent": 0,
                    "par360M1": 0, "par360M": 0, "par360Ecart": 0, "par360Percent": 0,
                    "nbreDossiers": 0, "encoursM": 0, "encoursM1": 0, "provisions": 0
                }
            }

        hierarchical["TERRITOIRE"][territory_key]["agencies"].append(agency_data)

        territory = hierarchical["TERRITOIRE"][territory_key]
        territory["totals"]["par0M1"] += agency_data["totals"]["par0M1"]
        territory["totals"]["par0M"] += agency_data["totals"]["par0M"]
        territory["totals"]["par30M1"] += agency_data["totals"]["par30M1"]
        territory["totals"]["par30M"] += agency_data["totals"]["par30M"]
        territory["totals"]["par90M1"] += agency_data["totals"]["par90M1"]
        territory["totals"]["par90M"] += agency_data["totals"]["par90M"]
        territory["totals"]["par180M1"] += agency_data["totals"]["par180M1"]
        territory["totals"]["par180M"] += agency_data["totals"]["par180M"]
        territory["totals"]["par360M1"] += agency_data["totals"]["par360M1"]
        territory["totals"]["par360M"] += agency_data["totals"]["par360M"]
        territory["totals"]["nbreDossiers"] += agency_data["totals"].get("nbreDossiers", 0)
        territory["totals"]["encoursM"] += agency_data["totals"].get("encoursM", 0)
        territory["totals"]["encoursM1"] += agency_data["totals"].get("encoursM1", 0)
        territory["totals"]["provisions"] += agency_data["totals"].get("provisions", 0)

    hierarchical["POINT SERVICES"] = {}
    
    # Calculer les écarts et pourcentages pour les territoires
    for territory in hierarchical["TERRITOIRE"].values():
        territory["totals"]["par0Ecart"] = territory["totals"]["par0M"] - territory["totals"]["par0M1"]
        territory["totals"]["par30Ecart"] = territory["totals"]["par30M"] - territory["totals"]["par30M1"]
        territory["totals"]["par90Ecart"] = territory["totals"]["par90M"] - territory["totals"]["par90M1"]
        territory["totals"]["par180Ecart"] = territory["totals"]["par180M"] - territory["totals"]["par180M1"]
        territory["totals"]["par360Ecart"] = territory["totals"]["par360M"] - territory["totals"]["par360M1"]
        
        # Calculer les pourcentages (variation en pourcentage)
        if territory["totals"]["par0M1"] != 0:
            territory["totals"]["par0Percent"] = (territory["totals"]["par0Ecart"] / territory["totals"]["par0M1"]) * 100
        if territory["totals"]["par30M1"] != 0:
            territory["totals"]["par30Percent"] = (territory["totals"]["par30Ecart"] / territory["totals"]["par30M1"]) * 100
        if territory["totals"]["par90M1"] != 0:
            territory["totals"]["par90Percent"] = (territory["totals"]["par90Ecart"] / territory["totals"]["par90M1"]) * 100
        if territory["totals"]["par180M1"] != 0:
            territory["totals"]["par180Percent"] = (territory["totals"]["par180Ecart"] / territory["totals"]["par180M1"]) * 100
        if territory["totals"]["par360M1"] != 0:
            territory["totals"]["par360Percent"] = (territory["totals"]["par360Ecart"] / territory["totals"]["par360M1"]) * 100

    grand_compte_agencies = [
        agency_data for agency_name, agency_data in agencies_map.items()
        if _is_grand_compte_agency_name(agency_name)
    ]
    if grand_compte_agencies:
        gc_totals = {
            "par0M1": 0, "par0M": 0, "par0Ecart": 0, "par0Percent": 0,
            "par30M1": 0, "par30M": 0, "par30Ecart": 0, "par30Percent": 0,
            "par90M1": 0, "par90M": 0, "par90Ecart": 0, "par90Percent": 0,
            "par180M1": 0, "par180M": 0, "par180Ecart": 0, "par180Percent": 0,
            "par360M1": 0, "par360M": 0, "par360Ecart": 0, "par360Percent": 0,
            "nbreDossiers": 0, "encoursM": 0, "encoursM1": 0, "provisions": 0,
        }
        for agency_data in grand_compte_agencies:
            t = agency_data["totals"]
            gc_totals["par0M1"] += t.get("par0M1", 0) or 0
            gc_totals["par0M"] += t.get("par0M", 0) or 0
            gc_totals["par30M1"] += t.get("par30M1", 0) or 0
            gc_totals["par30M"] += t.get("par30M", 0) or 0
            gc_totals["par90M1"] += t.get("par90M1", 0) or 0
            gc_totals["par90M"] += t.get("par90M", 0) or 0
            gc_totals["par180M1"] += t.get("par180M1", 0) or 0
            gc_totals["par180M"] += t.get("par180M", 0) or 0
            gc_totals["par360M1"] += t.get("par360M1", 0) or 0
            gc_totals["par360M"] += t.get("par360M", 0) or 0
            gc_totals["nbreDossiers"] += t.get("nbreDossiers", 0) or 0
            gc_totals["encoursM"] += t.get("encoursM", 0) or 0
            gc_totals["encoursM1"] += t.get("encoursM1", 0) or 0
            gc_totals["provisions"] += t.get("provisions", 0) or 0
        gc_totals["par0Ecart"] = gc_totals["par0M"] - gc_totals["par0M1"]
        gc_totals["par30Ecart"] = gc_totals["par30M"] - gc_totals["par30M1"]
        gc_totals["par90Ecart"] = gc_totals["par90M"] - gc_totals["par90M1"]
        gc_totals["par180Ecart"] = gc_totals["par180M"] - gc_totals["par180M1"]
        gc_totals["par360Ecart"] = gc_totals["par360M"] - gc_totals["par360M1"]
        if gc_totals["par0M1"] != 0:
            gc_totals["par0Percent"] = (gc_totals["par0Ecart"] / gc_totals["par0M1"]) * 100
        if gc_totals["par30M1"] != 0:
            gc_totals["par30Percent"] = (gc_totals["par30Ecart"] / gc_totals["par30M1"]) * 100
        if gc_totals["par90M1"] != 0:
            gc_totals["par90Percent"] = (gc_totals["par90Ecart"] / gc_totals["par90M1"]) * 100
        if gc_totals["par180M1"] != 0:
            gc_totals["par180Percent"] = (gc_totals["par180Ecart"] / gc_totals["par180M1"]) * 100
        if gc_totals["par360M1"] != 0:
            gc_totals["par360Percent"] = (gc_totals["par360Ecart"] / gc_totals["par360M1"]) * 100
        hierarchical["TERRITOIRE"]["grand_compte"] = {
            "name": "GRAND COMPTE",
            "agencies": grand_compte_agencies,
            "totals": gc_totals,
        }
    
    return hierarchical
