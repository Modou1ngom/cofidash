"""Dashboard PI — enrôlements SPI / Mobile+ / USSD des nouveaux clients."""
import logging
import re
import unicodedata
from calendar import monthrange
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import generate_cache_key, get_cache, set_cache
from services.pi_enrollement_query import PI_ENROLLEMENT_QUERY
from services.pi_fiche_targets import (
    IGNORED_AGENCIES,
    PI_FICHE_TARGETS,
    TERRITORY_ZONES,
    ZONE_ORDER,
)

logger = logging.getLogger(__name__)

MONTH_LABELS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _serialize_cell(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if isinstance(value, (int, float, str, bool)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_enrolled(value: Any) -> bool:
    return _text(value).casefold() == "enrôlé"


def _is_active(value: Any) -> bool:
    return _text(value).casefold() == "actif"


def _date_key(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = _text(value)
    if not text:
        return None
    return text[:10]


def _period_bounds(month: int, year: int) -> Dict[str, str]:
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    if month == 12:
        end_exclusive = date(year + 1, 1, 1)
    else:
        end_exclusive = date(year, month + 1, 1)
    return {
        "date_debut": start.strftime("%Y-%m-%d"),
        "date_fin_exclusive": end_exclusive.strftime("%Y-%m-%d"),
        "date_fin": date(year, month, last_day).strftime("%Y-%m-%d"),
        "label": f"{MONTH_LABELS[month - 1]} {year}",
    }


def _rate(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def _fetch_rows(date_debut: str, date_fin_exclusive: str) -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 180_000
            cursor.arraysize = 2000
            cursor.prefetchrows = 2000
            cursor.execute(
                PI_ENROLLEMENT_QUERY,
                {
                    "date_debut": date_debut,
                    "date_fin_exclusive": date_fin_exclusive,
                },
            )
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for raw in cursor.fetchall():
                row = {
                    columns[i]: _serialize_cell(raw[i])
                    for i in range(len(columns))
                }
                rows.append(row)
            return rows
        finally:
            cursor.close()


def _prefer_enrolled(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    if _is_enrolled(incoming.get("STATUT_ENROLLEMENT_SPI")) and not _is_enrolled(
        existing.get("STATUT_ENROLLEMENT_SPI")
    ):
        return incoming
    return existing


def _dedupe_clients(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_cust: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = _text(row.get("CUST_NO")) or f"row-{len(by_cust)}"
        if key in by_cust:
            by_cust[key] = _prefer_enrolled(by_cust[key], row)
        else:
            by_cust[key] = row
    return list(by_cust.values())


def _map_client(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "branch_code": _text(row.get("LOCAL_BRANCH")),
        "branch_name": _text(row.get("BRANCH_NAME")),
        "cust_no": _text(row.get("CUST_NO")),
        "ac_desc": _text(row.get("AC_DESC")),
        "ac_open_date": _date_key(row.get("AC_OPEN_DATE")),
        "date_creation": _date_key(row.get("DATE_CREATION")),
        "categorie_compte": _text(row.get("CATEGORIE_COMPTE")),
        "categorie": _text(row.get("CATEGORIE")).replace("PARTICULIER", "PARTICULIER ").replace("ENTREPRISE", "ENTREPRISE ").strip(),
        "mobile_number": _text(row.get("MOBILE_NUMBER")),
        "gestionnaire": _text(row.get("GESTIONNAIRE_CLIENT")),
        "code_gestionnaire": _text(row.get("CODE_GESTIONNAIRE_CLIENT")),
        "apporteur": _text(row.get("NOM_APPORTEUR_AFFAIRE")),
        "code_apporteur": _text(row.get("CODE_APPORTEUR_AFFAIRE")),
        "statut_mobile_plus": _text(row.get("STATUT_ENROLLEMENT_MOBILE_PLUS")) or "Non enrôlé",
        "dt_cre_mobile_plus": _date_key(row.get("DT_CRE_ENREG_MOBILE_PLUS")),
        "statut_cofina_mobile_plus": _text(row.get("STATUT_COFINA_MOBILE_PLUS")),
        "derniere_connexion_mobile_plus": _date_key(row.get("DERN_CONNEXION_MOBILE_PLUS")),
        "statut_pi": _text(row.get("STATUT_ENROLLEMENT_SPI")) or "Non enrôlé",
        "dt_cre_pi": _date_key(row.get("DT_CRE_ENREG_PI_SPI")),
        "statut_pi_actif": _text(row.get("STATUT_PI_SPI")),
        "telephone_pi": _text(row.get("TELEPHONECLIENT_PI_SPI")),
        "statut_ussd": _text(row.get("STATUT_ENROLLEMENT_USSD")) or "Non enrôlé",
        "dt_cre_ussd": _date_key(row.get("DT_CRE_ENREG_USSD")),
        "statut_ussd_actif": _text(row.get("STATUT_USSD")),
    }


def _build_volume(clients: List[Dict[str, Any]], month: int, year: int) -> List[Dict[str, Any]]:
    last_day = monthrange(year, month)[1]
    today = date.today()
    max_day = last_day
    if year == today.year and month == today.month:
        max_day = today.day

    buckets = {
        day: {"day": day, "label": f"{day:02d}", "clients": 0, "enrolled_pi": 0}
        for day in range(1, max_day + 1)
    }
    for client in clients:
        key = client.get("ac_open_date") or client.get("date_creation")
        if not key:
            continue
        try:
            parsed = datetime.strptime(key, "%Y-%m-%d").date()
        except ValueError:
            continue
        if parsed.year != year or parsed.month != month:
            continue
        if parsed.day not in buckets:
            continue
        buckets[parsed.day]["clients"] += 1
        if _is_enrolled(client.get("statut_pi")):
            buckets[parsed.day]["enrolled_pi"] += 1
    return [buckets[day] for day in range(1, max_day + 1)]


def _normalize_agency(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = re.sub(r"\b(AGENCE|C-E|C E|CE|PRINCIPALE)\b", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return " ".join(text.split())


def _match_target(branch_name: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_agency(branch_name)
    if not normalized or normalized in IGNORED_AGENCIES:
        return None
    if normalized in PI_FICHE_TARGETS:
        return PI_FICHE_TARGETS[normalized]
    stripped = normalized.rstrip("S")
    if stripped in PI_FICHE_TARGETS:
        return PI_FICHE_TARGETS[stripped]
    return None


def _is_fiche_agency(zone: str) -> bool:
    return zone in TERRITORY_ZONES or zone == "GRAND COMPTE"


def _as_of_date(month: int, year: int) -> date:
    today = date.today()
    last_day = monthrange(year, month)[1]
    if year == today.year and month == today.month:
        return today
    return date(year, month, last_day)


def _enrollment_day(client: Dict[str, Any]) -> Optional[str]:
    return client.get("dt_cre_pi") or client.get("ac_open_date") or client.get("date_creation")


def _build_fiche(clients: List[Dict[str, Any]], month: int, year: int) -> Dict[str, Any]:
    as_of = _as_of_date(month, year)
    as_of_key = as_of.strftime("%Y-%m-%d")
    days_in_month = monthrange(year, month)[1]
    agencies: Dict[str, Dict[str, Any]] = {}

    for client in clients:
        code = client.get("branch_code") or client.get("branch_name") or "INCONNU"
        if code not in agencies:
            target = _match_target(client.get("branch_name") or "")
            if not target or not _is_fiche_agency(target.get("zone") or ""):
                agencies[code] = None
                continue
            obj_month = int(target.get("obj_month") or 0)
            obj_daily = int(target.get("obj_daily") or 0)
            if obj_month and not obj_daily:
                obj_daily = max(1, round(obj_month / days_in_month))
            agencies[code] = {
                "branch_code": client.get("branch_code") or "",
                "branch_name": client.get("branch_name") or code,
                "zone": target.get("zone") or "—",
                "obj_daily": obj_daily,
                "obj_month": obj_month,
                "enrolled_day": 0,
                "cumul_month": 0,
            }
        if agencies.get(code) is None:
            continue
        if not _is_enrolled(client.get("statut_pi")):
            continue
        agencies[code]["cumul_month"] += 1
        if _enrollment_day(client) == as_of_key:
            agencies[code]["enrolled_day"] += 1

    merged: Dict[str, Dict[str, Any]] = {}
    for row in agencies.values():
        if not row:
            continue
        key = _normalize_agency(row["branch_name"]) or row["branch_code"] or row["branch_name"]
        if key not in merged:
            merged[key] = {
                **row,
                "branch_name": key,
                "branch_codes": [row["branch_code"] or row["branch_name"]],
            }
        else:
            target = merged[key]
            target["enrolled_day"] += row["enrolled_day"]
            target["cumul_month"] += row["cumul_month"]
            code = row["branch_code"] or row["branch_name"]
            if code not in target["branch_codes"]:
                target["branch_codes"].append(code)

    rows = list(merged.values())
    for row in rows:
        obj_month = row["obj_month"]
        row["rate_month"] = _rate(row["cumul_month"], obj_month) if obj_month else 0.0
        row["ahead"] = row["cumul_month"] >= obj_month if obj_month else False

    rows.sort(
        key=lambda item: (
            ZONE_ORDER.get(item["zone"], 99),
            item["zone"],
            item["branch_name"],
        )
    )

    totals = {
        "obj_daily": sum(row["obj_daily"] for row in rows),
        "enrolled_day": sum(row["enrolled_day"] for row in rows),
        "cumul_month": sum(row["cumul_month"] for row in rows),
        "obj_month": sum(row["obj_month"] for row in rows),
    }
    totals["rate_month"] = _rate(totals["cumul_month"], totals["obj_month"]) if totals["obj_month"] else 0.0
    totals["ahead"] = totals["cumul_month"] >= totals["obj_month"] if totals["obj_month"] else False

    return {
        "as_of": as_of_key,
        "label": as_of.strftime("%d/%m/%Y"),
        "rows": rows,
        "totals": totals,
    }


def _build_agencies(clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agencies: Dict[str, Dict[str, Any]] = {}
    for client in clients:
        code = client.get("branch_code") or client.get("branch_name") or "INCONNU"
        if code not in agencies:
            agencies[code] = {
                "branch_code": client.get("branch_code") or "",
                "branch_name": client.get("branch_name") or code,
                "total": 0,
                "enrolled_pi": 0,
                "enrolled_mobile": 0,
                "enrolled_ussd": 0,
            }
        agency = agencies[code]
        agency["total"] += 1
        if _is_enrolled(client.get("statut_pi")):
            agency["enrolled_pi"] += 1
        if _is_enrolled(client.get("statut_mobile_plus")):
            agency["enrolled_mobile"] += 1
        if _is_enrolled(client.get("statut_ussd")):
            agency["enrolled_ussd"] += 1

    rows = list(agencies.values())
    rows.sort(key=lambda item: (-item["enrolled_pi"], -item["total"], item["branch_name"]))
    return rows


def get_pi_dashboard_data(
    month: Optional[int] = None,
    year: Optional[int] = None,
    refresh: bool = False,
) -> Dict[str, Any]:
    now = datetime.now()
    month = int(month or now.month)
    year = int(year or now.year)
    if month < 1 or month > 12:
        raise ValueError("month doit être compris entre 1 et 12")

    cache_key = f"pi-dashboard:v6:{generate_cache_key(month, year)}"
    if not refresh:
        cached = get_cache(cache_key)
        if cached is not None:
            logger.info("⚡ pi-dashboard cache hit month=%s year=%s", month, year)
            return cached

    period = _period_bounds(month, year)
    logger.info(
        "📊 pi-dashboard Flexcube %s → %s",
        period["date_debut"],
        period["date_fin_exclusive"],
    )

    raw_rows = _fetch_rows(period["date_debut"], period["date_fin_exclusive"])
    clients = [_map_client(row) for row in _dedupe_clients(raw_rows)]

    total = len(clients)
    enrolled_pi = sum(1 for client in clients if _is_enrolled(client.get("statut_pi")))
    enrolled_mobile = sum(1 for client in clients if _is_enrolled(client.get("statut_mobile_plus")))
    enrolled_ussd = sum(1 for client in clients if _is_enrolled(client.get("statut_ussd")))
    active_pi = sum(
        1
        for client in clients
        if _is_enrolled(client.get("statut_pi")) and _is_active(client.get("statut_pi_actif"))
    )
    not_enrolled_pi = total - enrolled_pi

    agencies = _build_agencies(clients)
    volume = _build_volume(clients, month, year)
    fiche = _build_fiche(clients, month, year)

    payload = {
        "period": {
            "month": month,
            "year": year,
            "date_debut": period["date_debut"],
            "date_fin": period["date_fin"],
            "label": period["label"],
        },
        "updated_at": now.isoformat(timespec="seconds"),
        "kpis": {
            "total_clients": total,
            "enrolled_pi": enrolled_pi,
            "enrolled_mobile": enrolled_mobile,
            "enrolled_ussd": enrolled_ussd,
            "not_enrolled_pi": not_enrolled_pi,
            "active_pi": active_pi,
            "rate_pi": _rate(enrolled_pi, total),
            "rate_mobile": _rate(enrolled_mobile, total),
            "rate_ussd": _rate(enrolled_ussd, total),
            "rate_not_enrolled_pi": _rate(not_enrolled_pi, total),
        },
        "volume": volume,
        "canals": [
            {"label": "PI / SPI", "value": enrolled_pi, "color": "#2563EB"},
            {"label": "Mobile +", "value": enrolled_mobile, "color": "#F59E0B"},
            {"label": "USSD", "value": enrolled_ussd, "color": "#10B981"},
        ],
        "statuts": [
            {"label": "Enrôlé", "value": enrolled_pi, "color": "#16A34A"},
            {"label": "Non enrôlé", "value": not_enrolled_pi, "color": "#EF4444"},
        ],
        "agencies": agencies,
        "fiche": fiche,
        "clients": clients,
    }
    set_cache(cache_key, payload)
    logger.info("✅ pi-dashboard: %s clients, %s enrôlés PI", total, enrolled_pi)
    return payload
