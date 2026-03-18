"""
Service pour la gestion des données de portefeuille à risque (PAR)
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key, get_all_territories
from services.portefeuille_risque_global_query import get_query_for_date

logger = logging.getLogger(__name__)


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
    
    # Utiliser le mois et l'année courants si non fournis (mois en cours)
    if month is None or year is None:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Mois de référence : si fournis, les utiliser ; sinon prendre le mois précédent du mois en cours
    if month_ref is not None and year_ref is not None:
        month_m1 = month_ref
        year_m1 = year_ref
    else:
        if month == 1:
            month_m1 = 12
            year_m1 = year - 1
        else:
            month_m1 = month - 1
            year_m1 = year
    
    # Date de fin du mois M (dernier jour du mois)
    last_day_m = calendar.monthrange(year, month)[1]
    date_m = datetime(year, month, last_day_m)
    date_m_str = date_m.strftime("%d/%m/%Y")
    
    # Date de fin du mois M-1
    last_day_m1 = calendar.monthrange(year_m1, month_m1)[1]
    date_m1 = datetime(year_m1, month_m1, last_day_m1)
    date_m1_str = date_m1.strftime("%d/%m/%Y")
    
    logger.info(f"📅 Calcul des dates: M={date_m_str}, M-1={date_m1_str}")

    def _run_query(date_str: str):
        """Exécute la requête Portefeuille global pour une date et retourne la liste de lignes."""
        sql = get_query_for_date(date_str)
        conn = get_oracle_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def _safe_float(r: dict, *keys) -> float:
        for k in keys:
            if k in r and r[k] is not None:
                try:
                    return float(r[k])
                except (TypeError, ValueError):
                    pass
        return 0.0

    try:
        logger.info("🔍 Exécution requête Portefeuille global (date M)...")
        rows_m = _run_query(date_m_str)
        logger.info("🔍 Exécution requête Portefeuille global (date M-1)...")
        rows_m1 = _run_query(date_m1_str)

        # Index M-1 par (BRANCH_NAME, CODE_GESTION_PRET) pour rapprochement des lignes CAF
        key_m1 = {((r.get("BRANCH_NAME") or "").strip() or "-", (r.get("CODE_GESTION_PRET") or "").strip() or ""): r for r in rows_m1}

        # Lignes par CAF (pour onglet PAR | CAF) : une ligne par (BRANCH_NAME, CODE_GESTION_PRET)
        # raw_data = lignes par CAF avec montants PAR (pour get_portefeuille_risque_caf_data qui agrège par CAF)
        raw_data = []
        for r in rows_m:
            branch = (r.get("BRANCH_NAME") or "").strip() or "-"
            code = (r.get("CODE_GESTION_PRET") or "").strip() or ""
            r1 = key_m1.get((branch, code))
            raw_data.append({
                "AGENCE": branch,
                "CODE_AGENCE": "",
                "CHARGE_AFFAIRE": r.get("CHARGE_AFFAIRE") or "",
                "CODE_GESTION_PRET": code,
                "ENCOURS_TOTAL": _safe_float(r, "ENCOURS_TOTAL"),
                "ENCOURS_IMPAYE": _safe_float(r, "ENCOURS_IMPAYE"),
                "NOMBRE_DOSSIER": int(_safe_float(r, "NOMBRE_DOSSIER")),
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

        # Agréger par BRANCH_NAME pour la hiérarchie (PAR AGENCE / RECAP)
        agg_m = {}
        agg_m1 = {}
        for r in rows_m:
            branch = (r.get("BRANCH_NAME") or "").strip() or "-"
            if branch not in agg_m:
                agg_m[branch] = {"ENCOURS_TOTAL": 0.0, "NOMBRE_DOSSIER": 0, "PROVISION_TOTAL": 0.0,
                                 "ENCOURS_PAR_0": 0.0, "ENCOURS_PAR_30": 0.0, "ENCOURS_PAR_90": 0.0, "ENCOURS_PAR_180": 0.0, "ENCOURS_PAR_360": 0.0}
            agg_m[branch]["ENCOURS_TOTAL"] += _safe_float(r, "ENCOURS_TOTAL")
            agg_m[branch]["NOMBRE_DOSSIER"] += int(_safe_float(r, "NOMBRE_DOSSIER"))
            agg_m[branch]["PROVISION_TOTAL"] += _safe_float(r, "PROVISION_TOTAL")
            agg_m[branch]["ENCOURS_PAR_0"] += _safe_float(r, "ENCOURS_PAR_0")
            agg_m[branch]["ENCOURS_PAR_30"] += _safe_float(r, "ENCOURS_PAR_30")
            agg_m[branch]["ENCOURS_PAR_90"] += _safe_float(r, "ENCOURS_PAR_90")
            agg_m[branch]["ENCOURS_PAR_180"] += _safe_float(r, "ENCOURS_PAR_180")
            agg_m[branch]["ENCOURS_PAR_360"] += _safe_float(r, "ENCOURS_PAR_360")
        for r in rows_m1:
            branch = (r.get("BRANCH_NAME") or "").strip() or "-"
            if branch not in agg_m1:
                agg_m1[branch] = {"ENCOURS_TOTAL": 0.0, "NOMBRE_DOSSIER": 0, "PROVISION_TOTAL": 0.0,
                                  "ENCOURS_PAR_0": 0.0, "ENCOURS_PAR_30": 0.0, "ENCOURS_PAR_90": 0.0, "ENCOURS_PAR_180": 0.0, "ENCOURS_PAR_360": 0.0}
            agg_m1[branch]["ENCOURS_TOTAL"] += _safe_float(r, "ENCOURS_TOTAL")
            agg_m1[branch]["NOMBRE_DOSSIER"] += int(_safe_float(r, "NOMBRE_DOSSIER"))
            agg_m1[branch]["PROVISION_TOTAL"] += _safe_float(r, "PROVISION_TOTAL")
            agg_m1[branch]["ENCOURS_PAR_0"] += _safe_float(r, "ENCOURS_PAR_0")
            agg_m1[branch]["ENCOURS_PAR_30"] += _safe_float(r, "ENCOURS_PAR_30")
            agg_m1[branch]["ENCOURS_PAR_90"] += _safe_float(r, "ENCOURS_PAR_90")
            agg_m1[branch]["ENCOURS_PAR_180"] += _safe_float(r, "ENCOURS_PAR_180")
            agg_m1[branch]["ENCOURS_PAR_360"] += _safe_float(r, "ENCOURS_PAR_360")

        def _pct(enc, num):
            return round((num / enc * 100), 2) if enc else 0

        agency_rows = []
        for branch in set(agg_m.keys()) | set(agg_m1.keys()):
            m, m1 = agg_m.get(branch) or {}, agg_m1.get(branch) or {}
            enc_m, enc_m1 = m.get("ENCOURS_TOTAL") or 0, m1.get("ENCOURS_TOTAL") or 0
            agency_rows.append({
                "AGENCE": branch,
                "CODE_AGENCE": "",
                "ENCOURS_M": enc_m,
                "ENCOURS_M_1": enc_m1,
                "PROVISIONS": m.get("PROVISION_TOTAL") or 0,
                "NBRE_DOSSIERS": int(m.get("NOMBRE_DOSSIER") or 0),
                "PAR_0_M_1": _pct(enc_m1, m1.get("ENCOURS_PAR_0") or 0),
                "PAR_0_M": _pct(enc_m, m.get("ENCOURS_PAR_0") or 0),
                "PAR_30_M_1": _pct(enc_m1, m1.get("ENCOURS_PAR_30") or 0),
                "PAR_30_M": _pct(enc_m, m.get("ENCOURS_PAR_30") or 0),
                "PAR_90_M_1": _pct(enc_m1, m1.get("ENCOURS_PAR_90") or 0),
                "PAR_90_M": _pct(enc_m, m.get("ENCOURS_PAR_90") or 0),
                "PAR_180_M_1": _pct(enc_m1, m1.get("ENCOURS_PAR_180") or 0),
                "PAR_180_M": _pct(enc_m, m.get("ENCOURS_PAR_180") or 0),
                "PAR_360_M_1": _pct(enc_m1, m1.get("ENCOURS_PAR_360") or 0),
                "PAR_360_M": _pct(enc_m, m.get("ENCOURS_PAR_360") or 0),
            })

        logger.info(f"✅ Portefeuille global: {len(rows_m)} lignes M, {len(rows_m1)} M-1, {len(raw_data)} CAF, {len(agency_rows)} agences")

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
        
        return {
            "data": raw_data,
            "hierarchicalData": hierarchical_data
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"❌ Erreur lors de la récupération des données PAR: {str(e)}\n{error_detail}", exc_info=True)
        raise


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

    # Récupérer les données PAR complètes pour la période
    try:
        result = get_portefeuille_risque_data(
            month=month,
            year=year,
            month_ref=month_ref,
            year_ref=year_ref
        )
    except Exception as e:
        logger.error("❌ get_portefeuille_risque_data a échoué (PAR CAF): %s", e, exc_info=True)
        raise
    raw_data = result.get("data", []) or []

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
        enc_imp = row_val(row, "ENCOURS_IMPAYE", "encours_impaye")
        ratio_nb = row_val(row, "RATIO_NOMBRE_IMPAYE", "ratio_nombre_impaye")
        agg["encours_impaye_sum"] += enc_imp

        par0_m = row_val(row, "PAR_0_M", "par_0_m")
        par30_m = row_val(row, "PAR_30_M", "par_30_m")
        par90_m = row_val(row, "PAR_90_M", "par_90_m")
        par180_m = row_val(row, "PAR_180_M", "par_180_m")
        par360_m = row_val(row, "PAR_360_M", "par_360_m")

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
        ratio_encours_impaye = round((encours_impaye_sum / encours * 100), 2) if encours > 0 else 0.0
        ratio_nombre_impaye = round((agg.get("ratio_nombre_impaye_weighted") or 0) / encours, 2) if encours > 0 else None

        item = {
            "nom": caf_name,
            "nbreDossiers": int(agg["nombre_dossier_query"] or agg["nbre_dossiers"]),
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


def organize_par_data(raw_data: List[Dict]) -> Dict:
    """
    Organise les données PAR en structure hiérarchique (TERRITOIRE et POINT SERVICES)
    
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
            # C'est un point de service, l'ajouter à POINT SERVICES
            if not hierarchical["POINT SERVICES"].get("service_points"):
                hierarchical["POINT SERVICES"]["service_points"] = {
                    "name": "POINT SERVICES",
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
            
            hierarchical["POINT SERVICES"]["service_points"]["agencies"].append(agency_data)
            
            # Agréger les totaux des points de service
            service_point = hierarchical["POINT SERVICES"]["service_points"]
            service_point["totals"]["par0M1"] += agency_data["totals"]["par0M1"]
            service_point["totals"]["par0M"] += agency_data["totals"]["par0M"]
            service_point["totals"]["par30M1"] += agency_data["totals"]["par30M1"]
            service_point["totals"]["par30M"] += agency_data["totals"]["par30M"]
            service_point["totals"]["par90M1"] += agency_data["totals"]["par90M1"]
            service_point["totals"]["par90M"] += agency_data["totals"]["par90M"]
            service_point["totals"]["par180M1"] += agency_data["totals"]["par180M1"]
            service_point["totals"]["par180M"] += agency_data["totals"]["par180M"]
            service_point["totals"]["par360M1"] += agency_data["totals"]["par360M1"]
            service_point["totals"]["par360M"] += agency_data["totals"]["par360M"]
            service_point["totals"]["nbreDossiers"] += agency_data["totals"].get("nbreDossiers", 0)
            service_point["totals"]["encoursM"] += agency_data["totals"].get("encoursM", 0)
            service_point["totals"]["encoursM1"] += agency_data["totals"].get("encoursM1", 0)
            service_point["totals"]["provisions"] += agency_data["totals"].get("provisions", 0)
        else:
            # C'est une agence normale, l'ajouter à un territoire
            territory_name = get_territory_from_agency(agency_name)
            if territory_name:
                territory_key = get_territory_key(territory_name)
            else:
                # Si pas de territoire trouvé, utiliser le code de l'agence ou un défaut
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
            
            # Agréger les totaux du territoire
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
    
    # Calculer les écarts et pourcentages pour les points de service
    if hierarchical["POINT SERVICES"].get("service_points"):
        service_point = hierarchical["POINT SERVICES"]["service_points"]
        service_point["totals"]["par0Ecart"] = service_point["totals"]["par0M"] - service_point["totals"]["par0M1"]
        service_point["totals"]["par30Ecart"] = service_point["totals"]["par30M"] - service_point["totals"]["par30M1"]
        service_point["totals"]["par90Ecart"] = service_point["totals"]["par90M"] - service_point["totals"]["par90M1"]
        service_point["totals"]["par180Ecart"] = service_point["totals"]["par180M"] - service_point["totals"]["par180M1"]
        service_point["totals"]["par360Ecart"] = service_point["totals"]["par360M"] - service_point["totals"]["par360M1"]
        
        # Calculer les pourcentages (variation en pourcentage)
        if service_point["totals"]["par0M1"] != 0:
            service_point["totals"]["par0Percent"] = (service_point["totals"]["par0Ecart"] / service_point["totals"]["par0M1"]) * 100
        if service_point["totals"]["par30M1"] != 0:
            service_point["totals"]["par30Percent"] = (service_point["totals"]["par30Ecart"] / service_point["totals"]["par30M1"]) * 100
        if service_point["totals"]["par90M1"] != 0:
            service_point["totals"]["par90Percent"] = (service_point["totals"]["par90Ecart"] / service_point["totals"]["par90M1"]) * 100
        if service_point["totals"]["par180M1"] != 0:
            service_point["totals"]["par180Percent"] = (service_point["totals"]["par180Ecart"] / service_point["totals"]["par180M1"]) * 100
        if service_point["totals"]["par360M1"] != 0:
            service_point["totals"]["par360Percent"] = (service_point["totals"]["par360Ecart"] / service_point["totals"]["par360M1"]) * 100
    
    return hierarchical
