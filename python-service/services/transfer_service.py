"""
Service pour la gestion des données de transferts d'argent
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection

from services.orange_money_dash_query import (
    sql_dash_envoi_orange_money,
    sql_dash_paiement_orange_money,
)
from services.wave_dash_query import (
    sql_dash_envoi_wave,
    sql_dash_paiement_wave,
)
from services.ria_dash_query import (
    sql_dash_envoi_ria,
    sql_dash_paiement_ria,
)
from services.wiz_dash_query import (
    sql_dash_envoi_wiz,
    sql_dash_paiement_wiz,
)
from services.moneygram_dash_query import (
    sql_dash_envoi_moneygram,
    sql_dash_paiement_moneygram,
)
from services.wizzal_dash_query import (
    sql_dash_envoi_wizzal,
    sql_dash_paiement_wizzal,
)
from services.free_money_dash_query import (
    sql_dash_envoi_free_money,
    sql_dash_paiement_free_money,
)
from services.production_dash_service import _inner_sql_fragment
from services.volume_dat_service import _ref_month_year, _week_range_dd_mm_yyyy

logger = logging.getLogger(__name__)


def _migration_mode_and_binds_transfers_dash(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> Tuple[str, Dict[str, Any]]:
    """
    Snapshot DASH pour OM / Wave : semaine et année inchangés ;
    pour un mois calendaire, toujours MM/YYYY (pas de mode « jour » / veille).

    Les tables DASH transferts n’ont souvent pas de chargement quotidien :
    le mode jour renvoie alors 0 ligne alors que le mois est peuplé.
    """
    from datetime import date as dt_date

    p = (period or "month").strip().lower()
    today = dt_date.today()
    ref_m, ref_y = _ref_month_year(p, month, year, date_str)
    week_range = _week_range_dd_mm_yyyy(p, date_str)

    year_only_str: Optional[str] = None
    if p == "year":
        y = int(year) if year is not None else today.year
        year_only_str = f"{y:04d}"

    if week_range:
        ws, we = week_range
        return "week", {"week_start": ws, "week_end": we}
    if year_only_str is not None:
        return "year", {"year_only": year_only_str}
    return "month", {"month_year": f"{ref_m:02d}/{ref_y}"}


def _float_cell(row: dict, *keys: str) -> float:
    for k in keys:
        for cand in (k, k.upper(), k.lower()):
            if cand in row and row[cand] is not None:
                try:
                    return float(row[cand])
                except (TypeError, ValueError):
                    return 0.0
    return 0.0


def _rows_by_agence_sum_volumes(
    rows: List[Dict],
    key_m: str,
    key_m1: str,
) -> Dict[str, Dict]:
    """Agrège par CODE_AGENCE (somme des volumes si plusieurs lignes)."""
    by: Dict[str, Dict] = {}
    for row in rows:
        code = str(row.get("CODE_AGENCE") or row.get("code_agence") or "").strip()
        if not code:
            continue
        vm = _float_cell(row, key_m)
        vm1 = _float_cell(row, key_m1)
        lib = (row.get("LIBELLE_AGENCE") or row.get("libelle_agence") or "").strip()
        if code not in by:
            by[code] = {"vm": 0.0, "vm1": 0.0, "lib": lib}
        by[code]["vm"] += vm
        by[code]["vm1"] += vm1
        if lib and (not by[code]["lib"] or len(lib) > len(by[code]["lib"])):
            by[code]["lib"] = lib
    return by


def _get_dash_transfer_envoi_paiement_merged(
    binds: Dict,
    sql_env: str,
    sql_pay: str,
    env_m_key: str,
    env_m1_key: str,
    pay_m_key: str,
    pay_m1_key: str,
    log_label: str,
    mode: str,
) -> List[Dict]:
    """Exécute deux requêtes DASH (envoi + paiement) et fusionne les volumes par CODE_AGENCE."""
    conn = get_oracle_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_env, binds)
        cols_e = [d[0] for d in cursor.description]
        env_rows = [dict(zip(cols_e, r)) for r in cursor.fetchall()]

        cursor.execute(sql_pay, binds)
        cols_p = [d[0] for d in cursor.description]
        pay_rows = [dict(zip(cols_p, r)) for r in cursor.fetchall()]

        logger.info(
            "📊 %s DASH: %s lignes envoi, %s lignes paiement (mode=%s)",
            log_label,
            len(env_rows),
            len(pay_rows),
            mode,
        )

        env_by = _rows_by_agence_sum_volumes(env_rows, env_m_key, env_m1_key)
        pay_by = _rows_by_agence_sum_volumes(pay_rows, pay_m_key, pay_m1_key)

        all_codes = set(env_by.keys()) | set(pay_by.keys())
        result: List[Dict] = []
        for code in sorted(all_codes):
            e = env_by.get(code, {"vm": 0.0, "vm1": 0.0, "lib": ""})
            p = pay_by.get(code, {"vm": 0.0, "vm1": 0.0, "lib": ""})
            lib = e["lib"] or p["lib"] or ""
            vm = e["vm"] + p["vm"]
            vm1 = e["vm1"] + p["vm1"]
            var_vol = vm - vm1
            var_pct = round((var_vol / vm1 * 100), 2) if vm1 else 0.0
            result.append(
                {
                    "agence": lib,
                    "code_agence": code,
                    "volume_m": round(vm, 2),
                    "volume_m1": round(vm1, 2),
                    "variation_volume": round(var_vol, 2),
                    "variation_pct": var_pct,
                }
            )

        logger.info(f"✅ Données {log_label} (DASH): {len(result)} agences")
        return result

    except Exception as e:
        logger.error(
            f"❌ Erreur lors de la récupération des données {log_label}: {str(e)}",
            exc_info=True,
        )
        raise
    finally:
        cursor.close()
        conn.close()


def get_orange_money_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """
    Données Orange Money depuis DASH_ENVOIE_ORANGE_MONEY et DASH_PAIEMENT_ORANGE_MONEY
    (snapshot MAX(MIGRATION_DATETIME) comme les autres DASH).

    Envois + paiements sont fusionnés par CODE_AGENCE (volume M / M-1 et variations globales).
    """
    logger.info(
        f"📅 get_orange_money_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_orange_money(inner),
        sql_dash_paiement_orange_money(inner),
        "VOLUME_ENVOIE_OM_M",
        "VOLUME_ENVOIE_OM_M_1",
        "VOLUME_PAIEMENT_OM_M",
        "VOLUME_PAIEMENT_OM_M_1",
        "Orange Money",
        mode,
    )


def get_wave_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """
    Données Wave depuis DASH_ENVOIE_WAVE et DASH_PAIEMENT_WAVE (même logique qu’Orange Money DASH).
    """
    logger.info(
        f"📅 get_wave_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_wave(inner),
        sql_dash_paiement_wave(inner),
        "VOLUME_ENVOIE_WAV_M",
        "VOLUME_ENVOIE_WAV_M_1",
        "VOLUME_PAIEMENT_WAV_M",
        "VOLUME_PAIEMENT_WAV_M_1",
        "Wave",
        mode,
    )


def get_ria_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """
    Données Ria depuis DASH_ENVOIE_RIA et DASH_PAIEMENT_RIA (même logique qu’Orange Money / Wave DASH).
    """
    logger.info(
        f"📅 get_ria_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_ria(inner),
        sql_dash_paiement_ria(inner),
        "VOLUME_ENVOIE_RIA_M",
        "VOLUME_ENVOIE_RIA_M_1",
        "VOLUME_PAIEMENT_RIA_M",
        "VOLUME_PAIEMENT_RIA_M_1",
        "Ria",
        mode,
    )


def get_wu_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """
    Western Union (WIZ) : DASH_ENVOI_WIZ + DASH_PAIEMENT_WIZ (même logique que les autres transferts DASH).
    """
    logger.info(
        f"📅 get_wu_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_wiz(inner),
        sql_dash_paiement_wiz(inner),
        "VOLUME_ENVOIE_WIZ_M",
        "VOLUME_ENVOIE_WIZ_M_1",
        "VOLUME_PAIEMENT_WIZ_M",
        "VOLUME_PAIEMENT_WIZ_M_1",
        "Western Union",
        mode,
    )


def get_moneygram_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """MoneyGram : DASH_ENVOIE_MONEYGRAM + DASH_PAIEMENT_MONEYGRAM."""
    logger.info(
        f"📅 get_moneygram_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_moneygram(inner),
        sql_dash_paiement_moneygram(inner),
        "VOLUME_ENVOIE_MONEYGRAM_M",
        "VOLUME_ENVOIE_MONEYGRAM_M_1",
        "VOLUME_PAIEMENT_MONEYGRAM_M",
        "VOLUME_PAIEMENT_MONEYGRAM_M_1",
        "MoneyGram",
        mode,
    )


def get_wizzal_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """Wizzal : DASH_ENVOIE_WIZZAL + DASH_PAIEMENT_WIZZAL."""
    logger.info(
        f"📅 get_wizzal_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_wizzal(inner),
        sql_dash_paiement_wizzal(inner),
        "VOLUME_ENVOIE_WIZZAL_M",
        "VOLUME_ENVOIE_WIZZAL_M_1",
        "VOLUME_PAIEMENT_WIZZAL_M",
        "VOLUME_PAIEMENT_WIZZAL_M_1",
        "Wizzal",
        mode,
    )


def get_free_money_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """FREE Money : DASH_ENVOIE_FREE_MONEY + DASH_PAIEMENT_FREE_MONEY."""
    logger.info(
        f"📅 get_free_money_data (DASH) period={period}, month={month}, year={year}, date={date_str}"
    )
    now = datetime.now()
    m = int(month) if month is not None else now.month
    y = int(year) if year is not None else now.year
    mode, binds = _migration_mode_and_binds_transfers_dash(period or "month", m, y, date_str)
    inner = _inner_sql_fragment(mode)
    return _get_dash_transfer_envoi_paiement_merged(
        binds,
        sql_dash_envoi_free_money(inner),
        sql_dash_paiement_free_money(inner),
        "VOLUME_ENVOIE_FREE_MONEY_M",
        "VOLUME_ENVOIE_FREE_MONEY_M_1",
        "VOLUME_PAIEMENT_FREE_MONEY_M",
        "VOLUME_PAIEMENT_FREE_MONEY_M_1",
        "FREE Money",
        mode,
    )


def calculate_month_dates(month: int, year: int) -> Dict[str, str]:
    """
    Calcule les dates du mois M et M-1
    
    Args:
        month: Mois (1-12)
        year: Année
        
    Returns:
        Dictionnaire avec les dates au format DD/MM/YYYY et YYYY-MM-DD
    """
    # S'assurer que month et year sont des entiers
    month = int(month)
    year = int(year)
    
    logger.info(f"📅 calculate_month_dates appelé avec month={month}, year={year}")
    
    # Premier jour du mois M
    first_day = datetime(year, month, 1)
    # Dernier jour du mois M
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Mois précédent (M-1)
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    prev_last_day = datetime(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
    prev_first_day = datetime(prev_year, prev_month, 1)
    
    return {
        'm_debut': first_day.strftime("%d/%m/%Y"),
        'm_fin': last_day.strftime("%d/%m/%Y"),
        'm1_debut': prev_first_day.strftime("%d/%m/%Y"),
        'm1_fin': prev_last_day.strftime("%d/%m/%Y"),
        # Format DATE pour Oracle (YYYY-MM-DD)
        'm_debut_date': first_day.strftime("%Y-%m-%d"),
        'm_fin_date': last_day.strftime("%Y-%m-%d"),
        'm1_debut_date': prev_first_day.strftime("%Y-%m-%d"),
        'm1_fin_date': prev_last_day.strftime("%Y-%m-%d"),
    }


def get_transfer_data(period: str = "month", month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None, service: str = "om"):
    """
    Récupère les données de transferts d'argent depuis Oracle
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date au format YYYY-MM-DD pour period="week"
        service: Service de transfert ("om", "wave", "ria", "wu", "moneygram", "wizzal", "free_money")
    
    Returns:
        Dictionnaire avec les données de transferts organisées par agences et services
    """
    logger.info(f"🔍 get_transfer_data appelé avec period={period}, month={month} (type: {type(month)}), year={year} (type: {type(year)}), date={date}, service={service}")
    
    # S'assurer que month et year sont des entiers
    if month is not None:
        month = int(month)
    if year is not None:
        year = int(year)
    
    # Utiliser le mois et l'année actuels si non fournis
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    logger.info(f"📅 Paramètres de date finaux (après conversion): month={month} (type: {type(month)}), year={year} (type: {type(year)})")
    
    # Calculer les dates - IMPORTANT: recalculer à chaque appel pour éviter le cache
    dates = calculate_month_dates(month, year)
    
    logger.info(f"📅 Dates calculées: M={dates['m_debut']} à {dates['m_fin']}, M-1={dates['m1_debut']} à {dates['m1_fin']}")
    
    try:
        # Récupérer les données selon le service sélectionné
        if service == "om":
            logger.info("📊 Récupération des données Orange Money (DASH) depuis Oracle")
            om_data = get_orange_money_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "wave":
            logger.info("📊 Récupération des données Wave (DASH) depuis Oracle")
            om_data = get_wave_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "ria":
            logger.info("📊 Récupération des données Ria (DASH) depuis Oracle")
            om_data = get_ria_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "wu":
            logger.info("📊 Récupération des données Western Union / WIZ (DASH) depuis Oracle")
            om_data = get_wu_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "moneygram":
            logger.info("📊 Récupération des données MoneyGram (DASH) depuis Oracle")
            om_data = get_moneygram_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "wizzal":
            logger.info("📊 Récupération des données Wizzal (DASH) depuis Oracle")
            om_data = get_wizzal_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        elif service == "free_money":
            logger.info("📊 Récupération des données FREE Money (DASH) depuis Oracle")
            om_data = get_free_money_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        else:
            logger.warning(f"⚠️ Service '{service}' non reconnu. Utilisation d'Orange Money par défaut.")
            om_data = get_orange_money_data(
                month=month, year=year, period=period or "month", date_str=date
            )
        
        # Formater les données pour correspondre au format attendu
        agencies = []
        for om_item in om_data:
            try:
                # Calculer le TRO (Taux de Réalisation de l'Objectif)
                # Pour l'instant, objectif = 0 (à définir selon votre logique métier)
                objectif = 0
                tro = 0
                volume_m = om_item.get('volume_m', 0)
                if objectif > 0 and volume_m:
                    tro = (volume_m / objectif) * 100
                
                agencies.append({
                    "agence": om_item.get('agence', ''),
                    "objectif": objectif,
                    "volume_m": volume_m,
                    "volume_m1": om_item.get('volume_m1', 0),
                    "variation_volume": om_item.get('variation_volume', 0),
                    "variation_pct": om_item.get('variation_pct', 0),
                    "tro": round(tro, 2),
                    "contribution": 0,  # Sera calculé après
                    "commission": 0  # À calculer selon votre logique métier
                })
            except Exception as item_error:
                logger.error(f"❌ Erreur lors du traitement d'un item: {str(item_error)}")
                logger.error(f"   Item: {om_item}")
                continue
        
        # Calculer les contributions
        total_volume_m = sum(a['volume_m'] for a in agencies)
        for agency in agencies:
            if total_volume_m > 0:
                agency['contribution'] = round((agency['volume_m'] / total_volume_m) * 100, 2)
        
        result_data = {
            "agencies": agencies,
            "services": []  # Services seront ajoutés séparément si nécessaire
        }
        
        logger.info(f"✅ Données de transferts récupérées: {len(result_data['agencies'])} agences")
        return result_data
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données de transferts: {str(e)}", exc_info=True)
        raise
