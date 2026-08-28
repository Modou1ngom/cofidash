"""
Service pour la gestion des données de transferts d'argent (Flexcube).
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import TTL_DASHBOARD, generate_cache_key, get_cache, set_cache
from services.transfers_backup_service import (
    ensure_transfers_snapshot,
    load_transfers_month,
    prev_month,
)
from services.transfers_flexcube_query import (
    SERVICE_COMMISSION_GL_WHERE,
    SERVICE_VOLUME_GL_WHERE,
    sql_transfers_flexcube,
)
from services.utils import calculate_period_dates

logger = logging.getLogger(__name__)

SERVICE_LABELS = {
    "om": "Orange Money",
    "wave": "Wave",
    "ria": "Ria",
    "wu": "Western Union",
    "moneygram": "MoneyGram",
    "wizzal": "Wizzal",
    "free_money": "FREE Money",
}


def _dd_mm_yyyy_to_iso(date_str: str) -> str:
    return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")


def _exclusive_iso(date_str: str) -> str:
    return (datetime.strptime(date_str, "%d/%m/%Y") + timedelta(days=1)).strftime("%Y-%m-%d")


def _float_cell(row: dict, *keys: str) -> float:
    for k in keys:
        for cand in (k, k.upper(), k.lower()):
            if cand in row and row[cand] is not None:
                try:
                    return float(row[cand])
                except (TypeError, ValueError):
                    return 0.0
    return 0.0


def get_transfer_volumes(
    service: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    """
    Volumes envoi + paiement par agence depuis le journal Flexcube
    (GL d'attente / transit de l'opérateur).
    """
    svc = (service or "om").strip().lower()
    if svc not in SERVICE_VOLUME_GL_WHERE:
        logger.warning("Service '%s' inconnu, repli Orange Money", svc)
        svc = "om"

    dates = calculate_period_dates(period or "month", month, year, date_str)
    binds = {
        "date_m_debut": _dd_mm_yyyy_to_iso(dates["date_m_debut_str"]),
        "date_m_fin_exclusive": _exclusive_iso(dates["date_m_fin_str"]),
        "date_m1_debut": _dd_mm_yyyy_to_iso(dates["date_m1_debut_str"]),
    }
    sql = sql_transfers_flexcube(
        SERVICE_VOLUME_GL_WHERE[svc],
        SERVICE_COMMISSION_GL_WHERE[svc],
    )
    label = SERVICE_LABELS.get(svc, svc)

    logger.info(
        "📅 transferts Flexcube %s period=%s M=%s → %s, M-1=%s → %s",
        label,
        period,
        binds["date_m_debut"],
        binds["date_m_fin_exclusive"],
        binds["date_m1_debut"],
        binds["date_m_debut"],
    )

    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        cursor.callTimeout = 180_000
        cursor.arraysize = 500
        cursor.prefetchrows = 500
        try:
            cursor.execute(sql, binds)
            columns = [d[0] for d in cursor.description]
            rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
        finally:
            cursor.close()

    result: List[Dict] = []
    for row in rows:
        code = str(row.get("CODE_AGENCE") or "").strip()
        if not code:
            continue
        vm = _float_cell(row, "VOLUME_M")
        vm1 = _float_cell(row, "VOLUME_M_1")
        var_vol = _float_cell(row, "VARIATION_VOLUME")
        var_pct = _float_cell(row, "VARIATION_PCT")
        commission = _float_cell(row, "COMMISSION")
        lib = (row.get("LIBELLE_AGENCE") or "").strip()
        result.append(
            {
                "agence": lib,
                "code_agence": code,
                "volume_m": round(vm, 2),
                "volume_m1": round(vm1, 2),
                "variation_volume": round(var_vol, 2),
                "variation_pct": round(var_pct, 2),
                "commission": round(commission, 2),
            }
        )

    logger.info("✅ Données %s (Flexcube live): %s agences", label, len(result))
    return result


def _volumes_from_snapshots(service: str, month: int, year: int) -> List[Dict]:
    """Combine les snapshots SQLite du mois M et M-1."""
    svc = (service or "om").strip().lower()
    ensure_transfers_snapshot(month, year, svc)
    pm, py = prev_month(month, year)
    ensure_transfers_snapshot(pm, py, svc)

    rows_m = load_transfers_month(month, year, svc)
    rows_m1 = load_transfers_month(pm, py, svc)
    by_m = {r["code_agence"]: r for r in rows_m}
    by_m1 = {r["code_agence"]: r for r in rows_m1}
    all_codes = sorted(set(by_m) | set(by_m1))

    result: List[Dict] = []
    for code in all_codes:
        cur = by_m.get(code, {})
        prev = by_m1.get(code, {})
        vm = float(cur.get("volume") or 0)
        vm1 = float(prev.get("volume") or 0)
        var_vol = vm - vm1
        var_pct = round((var_vol / vm1 * 100), 2) if vm1 else 0.0
        lib = (cur.get("agence") or prev.get("agence") or "").strip()
        result.append(
            {
                "agence": lib,
                "code_agence": code,
                "volume_m": round(vm, 2),
                "volume_m1": round(vm1, 2),
                "variation_volume": round(var_vol, 2),
                "variation_pct": var_pct,
                "commission": round(float(cur.get("commission") or 0), 2),
            }
        )
    logger.info(
        "✅ Données %s (snapshot SQLite): %s agences",
        SERVICE_LABELS.get(svc, svc),
        len(result),
    )
    return result


def get_orange_money_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("om", month, year, period, date_str)


def get_wave_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("wave", month, year, period, date_str)


def get_ria_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("ria", month, year, period, date_str)


def get_wu_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("wu", month, year, period, date_str)


def get_moneygram_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("moneygram", month, year, period, date_str)


def get_wizzal_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("wizzal", month, year, period, date_str)


def get_free_money_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: str = "month",
    date_str: Optional[str] = None,
) -> List[Dict]:
    return get_transfer_volumes("free_money", month, year, period, date_str)


def get_transfer_data(
    period: str = "month",
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
    service: str = "om",
):
    """
    Récupère les données de transferts d'argent depuis Flexcube.

    Returns:
        Dictionnaire avec les données de transferts organisées par agences
    """
    logger.info(
        "🔍 get_transfer_data period=%s month=%s year=%s date=%s service=%s",
        period,
        month,
        year,
        date,
        service,
    )

    if month is not None:
        month = int(month)
    if year is not None:
        year = int(year)

    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year

    cache_key = f"transfers:flex:{generate_cache_key(period, month, year, date, service)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ transfers cache hit service=%s period=%s", service, period)
        return cached

    try:
        period_n = (period or "month").strip().lower()
        if period_n == "month":
            om_data = _volumes_from_snapshots(service or "om", month, year)
        else:
            om_data = get_transfer_volumes(
                service or "om",
                month=month,
                year=year,
                period=period_n,
                date_str=date,
            )

        agencies = []
        for om_item in om_data:
            try:
                objectif = 0
                tro = 0
                volume_m = om_item.get("volume_m", 0)
                if objectif > 0 and volume_m:
                    tro = (volume_m / objectif) * 100

                agencies.append(
                    {
                        "agence": om_item.get("agence", ""),
                        "objectif": objectif,
                        "volume_m": volume_m,
                        "volume_m1": om_item.get("volume_m1", 0),
                        "variation_volume": om_item.get("variation_volume", 0),
                        "variation_pct": om_item.get("variation_pct", 0),
                        "tro": round(tro, 2),
                        "contribution": 0,
                        "commission": om_item.get("commission", 0),
                    }
                )
            except Exception as item_error:
                logger.error("❌ Erreur lors du traitement d'un item: %s", item_error)
                logger.error("   Item: %s", om_item)
                continue

        total_volume_m = sum(a["volume_m"] for a in agencies)
        for agency in agencies:
            if total_volume_m > 0:
                agency["contribution"] = round((agency["volume_m"] / total_volume_m) * 100, 2)

        result_data = {
            "agencies": agencies,
            "services": [],
        }

        logger.info("✅ Données de transferts récupérées: %s agences", len(result_data["agencies"]))
        set_cache(cache_key, result_data, TTL_DASHBOARD)
        return result_data

    except Exception as e:
        logger.error("❌ Erreur lors de la récupération des données de transferts: %s", e, exc_info=True)
        raise
