"""
Ouvertures de comptes (courants 251 + épargne 253) — dashboard exécutif.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import generate_cache_key, get_cache, set_cache
from services.comptes_ouverts_query import COMPTES_OUVERTS_MENSUEL_QUERY
from services.utils import (
    get_territory_from_agency,
    get_territory_from_branch_code,
    get_territory_key,
)

logger = logging.getLogger(__name__)

MONTH_LABELS = [
    "JAN", "FÉV", "MAR", "AVR", "MAI", "JUN",
    "JUL", "AOÛ", "SEP", "OCT", "NOV", "DÉC",
]

TERRITORY_DISPLAY = {
    "DAKAR VILLE": "DAKAR CENTRE",
    "DAKAR CENTRE VILLE": "DAKAR CENTRE",
    "DAKAR BANLIEUE": "DAKAR BANLIEUE",
    "PROVINCE CENTRE SUD": "PROVINCE CENTRE SUD",
    "PROVINCE CENTRE-SUD": "PROVINCE CENTRE SUD",
    "PROVINCE NORD": "PROVINCE NORD",
}

TERRITORY_ORDER = [
    "DAKAR BANLIEUE",
    "DAKAR CENTRE",
    "GRANDS COMPTES",
    "PROVINCE CENTRE SUD",
    "PROVINCE NORD",
    "AUTRES",
]


def _to_int(value) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def _is_grand_compte(name: str) -> bool:
    upper = (name or "").upper()
    return "GRAND COMPTE" in upper or "GRAND_COMPTE" in upper


def _territory_display(agency_name: str, branch_code: str) -> str:
    if _is_grand_compte(agency_name):
        return "GRANDS COMPTES"
    territory = get_territory_from_agency(agency_name)
    if not territory:
        territory = get_territory_from_branch_code(branch_code)
    if not territory:
        return "AUTRES"
    return TERRITORY_DISPLAY.get(territory, territory)


def _empty_metrics() -> Dict[str, int]:
    return {
        "realise_m": 0,
        "realise_m_251": 0,
        "realise_m_253": 0,
        "realise_ytd": 0,
        "realise_ytd_251": 0,
        "realise_ytd_253": 0,
    }


def _period_bounds(month: int, year: int) -> Dict[str, str]:
    today = date.today()
    month_start = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    fin_exclusive = next_month
    if year == today.year and month == today.month:
        fin_exclusive = min(next_month, today + timedelta(days=1))

    return {
        "date_debut": f"{year}-01-01",
        "date_fin_exclusive": fin_exclusive.strftime("%Y-%m-%d"),
        "date_mois_debut": month_start.strftime("%Y-%m-%d"),
        "label": f"{MONTH_LABELS[month - 1]} {year}",
    }


def _fetch_monthly_rows(date_debut: str, date_fin_exclusive: str) -> List[Dict]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 180_000
            cursor.arraysize = 2000
            cursor.prefetchrows = 2000
            cursor.execute(
                COMPTES_OUVERTS_MENSUEL_QUERY,
                {
                    "date_debut": date_debut,
                    "date_fin_exclusive": date_fin_exclusive,
                },
            )
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for raw in cursor.fetchall():
                row = dict(zip(columns, raw))
                rows.append(
                    {
                        "branch_code": str(row.get("BRANCH_CODE") or "").strip(),
                        "branch_name": str(row.get("BRANCH_NAME") or "").strip(),
                        "mois": _to_int(row.get("MOIS")),
                        "realise": _to_int(row.get("REALISE")),
                        "realise_251": _to_int(row.get("REALISE_251")),
                        "realise_253": _to_int(row.get("REALISE_253")),
                    }
                )
            return rows
        finally:
            cursor.close()


def get_comptes_ouverts_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict:
    now = datetime.now()
    month = int(month or now.month)
    year = int(year or now.year)
    if month < 1 or month > 12:
        raise ValueError("month doit être compris entre 1 et 12")

    cache_key = f"comptes-ouverts:{generate_cache_key(month, year)}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ comptes-ouverts cache hit month=%s year=%s", month, year)
        return cached

    period = _period_bounds(month, year)
    logger.info(
        "📊 comptes-ouverts Flexcube %s → %s (mois=%s)",
        period["date_debut"],
        period["date_fin_exclusive"],
        month,
    )

    raw_rows = _fetch_monthly_rows(period["date_debut"], period["date_fin_exclusive"])

    agencies: Dict[str, Dict] = {}
    monthly_totals = {
        m: {"month": m, "label": MONTH_LABELS[m - 1], "total": 0, "courants": 0, "epargne": 0, "ytd": 0}
        for m in range(1, 13)
    }

    for row in raw_rows:
        code = row["branch_code"] or row["branch_name"] or "INCONNU"
        if code not in agencies:
            agencies[code] = {
                "branch_code": row["branch_code"],
                "branch_name": row["branch_name"] or code,
                "territory": _territory_display(row["branch_name"], row["branch_code"]),
                **_empty_metrics(),
            }
        agency = agencies[code]
        mois = row["mois"]
        if mois < 1 or mois > 12:
            continue

        monthly_totals[mois]["total"] += row["realise"]
        monthly_totals[mois]["courants"] += row["realise_251"]
        monthly_totals[mois]["epargne"] += row["realise_253"]

        agency["realise_ytd"] += row["realise"]
        agency["realise_ytd_251"] += row["realise_251"]
        agency["realise_ytd_253"] += row["realise_253"]
        if mois == month:
            agency["realise_m"] += row["realise"]
            agency["realise_m_251"] += row["realise_251"]
            agency["realise_m_253"] += row["realise_253"]

    ytd_running = 0
    monthly = []
    for m in range(1, 13):
        item = monthly_totals[m]
        if m <= month:
            ytd_running += item["total"]
            item["ytd"] = ytd_running
        else:
            item["ytd"] = 0
        monthly.append(item)

    kpis = _empty_metrics()
    territories_map: Dict[str, Dict] = {}

    for agency in agencies.values():
        kpis["realise_m"] += agency["realise_m"]
        kpis["realise_m_251"] += agency["realise_m_251"]
        kpis["realise_m_253"] += agency["realise_m_253"]
        kpis["realise_ytd"] += agency["realise_ytd"]
        kpis["realise_ytd_251"] += agency["realise_ytd_251"]
        kpis["realise_ytd_253"] += agency["realise_ytd_253"]

        territory_name = agency["territory"]
        if territory_name not in territories_map:
            territories_map[territory_name] = {
                "key": get_territory_key(territory_name) if territory_name != "GRANDS COMPTES" else "grands_comptes",
                "name": territory_name,
                **_empty_metrics(),
                "agencies": [],
            }
        bucket = territories_map[territory_name]
        for field in _empty_metrics():
            bucket[field] += agency[field]
        bucket["agencies"].append(agency)

    for bucket in territories_map.values():
        bucket["agencies"].sort(key=lambda a: a.get("branch_name") or "")

    territories = []
    remaining = dict(territories_map)
    for name in TERRITORY_ORDER:
        if name in remaining:
            territories.append(remaining.pop(name))
    territories.extend(sorted(remaining.values(), key=lambda t: t["name"]))

    agency_list = sorted(
        agencies.values(),
        key=lambda a: (a.get("branch_code") or "", a.get("branch_name") or ""),
    )

    result = {
        "month": month,
        "year": year,
        "period": period,
        "kpis": kpis,
        "monthly": monthly,
        "territories": territories,
        "agencies": agency_list,
    }
    set_cache(cache_key, result, ttl=300)
    logger.info(
        "✅ comptes-ouverts: %s agences, réalisé YTD=%s, mois=%s",
        len(agency_list),
        kpis["realise_ytd"],
        kpis["realise_m"],
    )
    return result
