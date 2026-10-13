"""
Suivi de la production de crédits : mois en cours et cumul YTD.

Un prêt compte une fois, à sa date de déblocage (écriture CL / DSBR / 040).
FAMILLE_CREDIT est le libellé UDTM_LOV (FIELD_NAME = FAM_CRED) de FIELD_CHAR_4.
Les quatre types du tableau (restructuré, protocole, rebocker, simple) restent
un classement exclusif à part :
  1. Crédit Restructuré — FIELD_CHAR_7 = YES
  2. Crédit Protocole   — FIELD_CHAR_13 commence par PC
  3. Rebocker           — FIELD_CHAR_19 = YES
  4. Crédit Simple      — le reste
"""
import logging
from calendar import monthrange
from datetime import date as dt_date
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional

from services.cache_service import TTL_DASHBOARD, get_cache, set_cache
from services.production_dash_service import _as_date
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
_SQL_PATH = _PY_ROOT / "requete mobile" / "production" / "suivi_production.sql"
_CALL_TIMEOUT_MS = 240_000

TYPE_KEYS = ("restructure", "protocole", "rebooker", "simple")
MONTHS = (
    "",
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def _load_sql() -> str:
    if not _SQL_PATH.is_file():
        raise FileNotFoundError(f"Requête introuvable : {_SQL_PATH}")
    return _SQL_PATH.read_text(encoding="utf-8").strip().rstrip(";").strip()


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _amount(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def classify_type(code_restructure: Any, id_protocoles: Any, rebooker: Any) -> str:
    if _text(code_restructure).upper() == "YES":
        return "restructure"
    if _text(id_protocoles).upper().startswith("PC"):
        return "protocole"
    if _text(rebooker).upper() == "YES":
        return "rebooker"
    return "simple"


def _pretty_name(value: str) -> str:
    text = " ".join(_text(value).split())
    if text.isupper():
        return text.title()
    return text


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _month_last(year: int, month: int) -> dt_date:
    return dt_date(year, month, monthrange(year, month)[1])


def _clamp_day(year: int, month: int, day: int) -> dt_date:
    return dt_date(year, month, min(day, monthrange(year, month)[1]))


def resolve_windows(
    scope: Optional[str],
    year: Optional[int],
    month: Optional[int],
    today: Optional[dt_date] = None,
) -> dict:
    today = today or dt_date.today()
    mode = (scope or "ytd").strip().lower()
    if mode not in ("ytd", "month"):
        mode = "ytd"

    if mode == "month":
        y = int(year or today.year)
        m = int(month or today.month)
        m = min(12, max(1, m))
        start = dt_date(y, m, 1)
        end = _month_last(y, m)
        partial = (y, m) == (today.year, today.month) and today < end
        if partial:
            end = today
        py, pm = _shift_month(y, m, -1)
        prev_start = dt_date(py, pm, 1)
        prev_end = _clamp_day(py, pm, end.day) if partial else _month_last(py, pm)
        compare = "vs. mois précédent, à date" if partial else "vs. mois précédent"
        label = f"{MONTHS[m].capitalize()} {y}"
        if partial:
            label = f"{label} · au {end.day}"
    else:
        y = int(year or today.year)
        start = dt_date(y, 1, 1)
        end = today if y == today.year else dt_date(y, 12, 31)
        if y > today.year:
            end = dt_date(y, 1, 1)
        prev_start = dt_date(y - 1, 1, 1)
        prev_end = _clamp_day(y - 1, end.month, end.day)
        compare = f"vs. YTD {y - 1}"
        label = f"Cumul {y} · au {end.day} {MONTHS[end.month]}"

    series_y, series_m = _shift_month(end.year, end.month, -5)
    series_start = dt_date(series_y, series_m, 1)
    fetch_start = min(prev_start, series_start, dt_date(end.year - 1, 1, 1))
    ytd_start = dt_date(end.year, 1, 1)
    return {
        "scope": mode,
        "start": start,
        "end": end,
        "prev_start": prev_start,
        "prev_end": prev_end,
        "fetch_start": fetch_start,
        "ytd_start": ytd_start,
        "compare_label": compare,
        "period_label": label,
        "ytd_label": f"YTD {end.year}",
    }


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _cell(index: dict, *names: str):
    for name in names:
        if name in index and index[name] is not None:
            return index[name]
    return None


def _normalize_row(raw: dict) -> Optional[dict]:
    index = {str(key).strip().upper(): value for key, value in raw.items()}
    trn = _as_date(_cell(index, "DATE_DEBLOCAGE"))
    if trn is None:
        return None
    code = _text(_cell(index, "CODE AGENCE", "CODE_AGENCE"), "-")
    return {
        "date": trn,
        "agence_code": code,
        "agence": _pretty_name(_text(_cell(index, "NOM AGENCE", "NOM_AGENCE"), code)),
        "no_pret": _text(_cell(index, "NO_PRET", "NO PRET"), ""),
        "secteur": _pretty_name(_text(_cell(index, "SECTEUR_ACTIVITE", "SECTEUR"), "Non renseigné")),
        "famille": _pretty_name(_text(_cell(index, "FAMILLE_CREDIT"), "Non renseigné")),
        "type": classify_type(
            _cell(index, "CODE_REF_CREDIT_RESTRUCTURE", "CODE_RESTRUCTURE"),
            _cell(index, "ID_PROTOCOLES"),
            _cell(index, "REBOOKE", "REBOOKER"),
        ),
        "montant": _amount(_cell(index, "MONTANT CAPITAL ACCORDE", "MONTANT")),
        "caf_code": _text(_cell(index, "CODE_GESTION_PRET"), ""),
        "caf_name": _pretty_name(_text(_cell(index, "CHARGE_D'AFFAIRE", "CHARGE_D_AFFAIRE", "CHARGE_AFFAIRE"), "")),
    }


def _one_loan(rows: list[dict]) -> list[dict]:
    kept: dict[str, dict] = {}
    for row in rows:
        key = row["no_pret"] or f"{row['agence_code']}|{row['date'].isoformat()}|{row['montant']}"
        previous = kept.get(key)
        if previous is None or row["date"] < previous["date"]:
            kept[key] = row
    return list(kept.values())


def _split(value: Optional[str]) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in str(value).split(",") if part.strip()}


def _filter_rows(rows: list[dict], agencies: set[str], sectors: set[str], types: set[str]) -> list[dict]:
    kept = []
    for row in rows:
        if agencies and row["agence_code"] not in agencies:
            continue
        if sectors and row["secteur"] not in sectors:
            continue
        if types and row["type"] not in types:
            continue
        kept.append(row)
    return kept


def _between(rows: list[dict], start: dt_date, end: dt_date) -> list[dict]:
    return [row for row in rows if start <= row["date"] <= end]


def _sum_type(rows: list[dict], type_key: Optional[str] = None) -> float:
    if type_key is None:
        return sum(row["montant"] for row in rows)
    return sum(row["montant"] for row in rows if row["type"] == type_key)


def _kpi(rows: list[dict], previous: list[dict]) -> dict:
    total = _sum_type(rows)
    out = {
        "total": {
            "amount": round(total, 2),
            "variation_pct": _pct_change(total, _sum_type(previous)),
        }
    }
    for type_key in TYPE_KEYS:
        amount = _sum_type(rows, type_key)
        out[type_key] = {
            "amount": round(amount, 2),
            "share_pct": round(amount / total * 100, 1) if total else 0.0,
            "variation_pct": _pct_change(amount, _sum_type(previous, type_key)),
        }
    return out


def _ranked(rows: list[dict], key_fn, limit: Optional[int] = None) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        key, label = key_fn(row)
        bucket = grouped.get(key)
        if bucket is None:
            bucket = {"key": key, "label": label, "total": 0.0}
            grouped[key] = bucket
        bucket["total"] += row["montant"]
    items = sorted(grouped.values(), key=lambda item: item["total"], reverse=True)
    total = sum(item["total"] for item in items)
    if limit:
        items = items[:limit]
    for index, item in enumerate(items, start=1):
        item["rank"] = index
        item["total"] = round(item["total"], 2)
        item["share_pct"] = round(item["total"] / total * 100, 1) if total else 0.0
    return items


_MONTH_SHORT = (
    "",
    "Janv.",
    "Févr.",
    "Mars",
    "Avr.",
    "Mai",
    "Juin",
    "Juil.",
    "Août",
    "Sept.",
    "Oct.",
    "Nov.",
    "Déc.",
)


def _month_axis_label(year: int, month: int) -> str:
    return f"{_MONTH_SHORT[month]} {year}"


def _months(end: dt_date) -> list[tuple[int, int]]:
    points = []
    year, month = end.year, end.month
    for _ in range(6):
        points.append((year, month))
        year, month = _shift_month(year, month, -1)
    points.reverse()
    return points


def _series(rows: list[dict], end: dt_date) -> list[dict]:
    series = []
    for year, month in _months(end):
        start = dt_date(year, month, 1)
        last = _month_last(year, month)
        if (year, month) == (end.year, end.month):
            last = min(last, end)
        bucket = _between(rows, start, last)
        point = {
            "key": f"{year:04d}-{month:02d}",
            "label": _month_axis_label(year, month),
            "total": round(_sum_type(bucket), 2),
        }
        for type_key in TYPE_KEYS:
            point[type_key] = round(_sum_type(bucket, type_key), 2)
        series.append(point)
    return series


def _famille_months(rows: list[dict], end: dt_date, limit: int = 6) -> dict:
    points = _months(end)
    buckets: list[dict[str, float]] = []
    totals: dict[str, float] = {}
    for year, month in points:
        start = dt_date(year, month, 1)
        last = _month_last(year, month)
        if (year, month) == (end.year, end.month):
            last = min(last, end)
        by_famille: dict[str, float] = {}
        for row in _between(rows, start, last):
            key = row["famille"]
            by_famille[key] = by_famille.get(key, 0.0) + row["montant"]
            totals[key] = totals.get(key, 0.0) + row["montant"]
        buckets.append(by_famille)
    ranked = sorted(totals, key=lambda key: totals[key], reverse=True)
    head = ranked[:limit]
    rest = ranked[limit:]
    series = [
        {
            "key": key,
            "label": key,
            "values": [round(bucket.get(key, 0.0), 2) for bucket in buckets],
        }
        for key in head
    ]
    if rest:
        series.append({
            "key": "autres",
            "label": "Autres",
            "values": [
                round(sum(bucket.get(key, 0.0) for key in rest), 2)
                for bucket in buckets
            ],
        })
    return {
        "labels": [_month_axis_label(year, month) for year, month in points],
        "series": series,
    }


def _lines(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda row: row["montant"], reverse=True)
    return [
        {
            "pret": row.get("no_pret", ""),
            "date": row["date"].isoformat(),
            "agence": row["agence"],
            "secteur": row["secteur"],
            "type": row["type"],
            "montant": round(row["montant"], 2),
        }
        for row in ordered
    ]


def _options(rows: list[dict]) -> dict:
    agencies: dict[str, str] = {}
    sectors: set[str] = set()
    for row in rows:
        agencies[row["agence_code"]] = row["agence"]
        if row["secteur"]:
            sectors.add(row["secteur"])
    return {
        "agencies": [
            {"code": code, "label": label}
            for code, label in sorted(agencies.items(), key=lambda item: item[1])
        ],
        "sectors": sorted(sectors),
    }


_TERRITORY_LABELS = {
    "territoire_dakar_ville": "TERRITOIRE DAKAR VILLE",
    "territoire_dakar_banlieue": "TERRITOIRE DAKAR BANLIEUE",
    "territoire_province_centre_sud": "TERRITOIRE PROVINCE CENTRE-SUD",
    "territoire_province_nord": "TERRITOIRE PROVINCE NORD",
}


def _territory_of(row: dict) -> tuple[str, str]:
    name = get_territory_from_agency(row.get("agence")) or get_territory_from_branch_code(row.get("agence_code"))
    if not name:
        return "non_rattache", "NON RATTACHÉ"
    key = get_territory_key(name)
    return key, _TERRITORY_LABELS.get(key, name)


def _empty_amounts() -> dict:
    return {
        "restructure": 0.0,
        "protocole": 0.0,
        "rebooker": 0.0,
        "simple": 0.0,
        "total": 0.0,
    }


def _add_amount(target: dict, row: dict) -> None:
    target[row["type"]] += row["montant"]
    target["total"] += row["montant"]


def _round_amounts(item: dict) -> None:
    for key in ("restructure", "protocole", "rebooker", "simple", "total"):
        item[key] = round(item[key], 2)


def _agency_matrix(current: list[dict], previous: list[dict]) -> list[dict]:
    buckets: dict[str, dict] = {}

    def bucket_for(row: dict) -> dict:
        key = row["agence_code"]
        bucket = buckets.get(key)
        if bucket is None:
            territory_key, territory = _territory_of(row)
            bucket = {
                "key": key,
                "label": row["agence"],
                "territory_key": territory_key,
                "territory": territory,
                "cafs": {},
                **_empty_amounts(),
                "previous_total": 0.0,
            }
            buckets[key] = bucket
        return bucket

    for row in current:
        bucket = bucket_for(row)
        _add_amount(bucket, row)
        caf_code = row.get("caf_code") or "-"
        caf_name = row.get("caf_name") or ""
        caf = bucket["cafs"].get(caf_code)
        if caf is None:
            caf = {
                "key": f"{bucket['key']}|{caf_code}",
                "code": caf_code,
                "label": caf_name or "Non renseigné",
                **_empty_amounts(),
            }
            bucket["cafs"][caf_code] = caf
        elif caf_name and caf["label"] == "Non renseigné":
            caf["label"] = caf_name
        _add_amount(caf, row)
    for row in previous:
        bucket_for(row)["previous_total"] += row["montant"]

    items = [item for item in buckets.values() if item["total"] > 0]
    items.sort(key=lambda item: item["total"], reverse=True)
    for item in items:
        _round_amounts(item)
        item["previous_total"] = round(item["previous_total"], 2)
        item["variation_pct"] = _pct_change(item["total"], item["previous_total"])
        cafs = [caf for caf in item["cafs"].values() if caf["total"] > 0]
        cafs.sort(key=lambda caf: caf["total"], reverse=True)
        for caf in cafs:
            _round_amounts(caf)
        item["cafs"] = cafs
    return items


def build_suivi_payload(
    rows: list[dict],
    windows: dict,
    agencies: set[str],
    sectors: set[str],
    types: set[str],
    include_lines: bool = False,
) -> dict:
    start, end = windows["start"], windows["end"]
    current_all = _between(rows, start, end)
    options = _options(current_all)
    filtered = _filter_rows(rows, agencies, sectors, types)
    current = _between(filtered, start, end)
    previous = _between(filtered, windows["prev_start"], windows["prev_end"])
    ytd_rows = _between(filtered, windows["ytd_start"], end)
    agencies_ranked = _ranked(current, lambda row: (row["agence_code"], row["agence"]))
    payload = {
        "scope": windows["scope"],
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "previous_period": {
            "start": windows["prev_start"].isoformat(),
            "end": windows["prev_end"].isoformat(),
        },
        "period_label": windows["period_label"],
        "compare_label": windows["compare_label"],
        "ytd_label": windows["ytd_label"],
        "kpis": _kpi(current, previous),
        "ytd": {
            "total": round(_sum_type(ytd_rows), 2),
            **{key: round(_sum_type(ytd_rows, key), 2) for key in TYPE_KEYS},
        },
        "agencies": agencies_ranked[:12],
        "sectors": _ranked(current, lambda row: (row["secteur"], row["secteur"])),
        "months": _series(filtered, end),
        "famille_months": _famille_months(filtered, end),
        "familles": _ranked(current, lambda row: (row["famille"], row["famille"])),
        "options": options,
        "loan_count": len(current),
        "agency_matrix": _agency_matrix(current, previous),
    }
    if include_lines:
        payload["lines"] = _lines(current)
    return payload


def fetch_suivi_rows(range_start: dt_date, range_end: dt_date) -> list[dict]:
    cache_key = f"suivi-prod:v4:{range_start.isoformat()}:{range_end.isoformat()}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ suivi production cache hit %s → %s (%s)", range_start, range_end, len(cached))
        return cached

    from services.suivi_production_backup_service import load_suivi_backup_rows

    saved = load_suivi_backup_rows(range_start, range_end)
    if saved is None:
        logger.warning(
            "Suivi production %s → %s : pas de sauvegarde, aucune requête Flexcube",
            range_start,
            range_end,
        )
        raw_rows = []
        source = "sauvegarde absente"
    else:
        raw_rows = saved
        source = "sauvegarde"

    rows = _one_loan([row for row in (_normalize_row(raw) for raw in raw_rows) if row is not None])
    logger.info(
        "📊 suivi production %s → %s : %s prêts (%s)",
        range_start,
        range_end,
        len(rows),
        source,
    )
    set_cache(cache_key, rows, TTL_DASHBOARD)
    return rows


def get_suivi_production_data(
    scope: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    agences: Optional[str] = None,
    secteurs: Optional[str] = None,
    types: Optional[str] = None,
    include_lines: bool = False,
) -> dict:
    windows = resolve_windows(scope, year, month)
    rows = fetch_suivi_rows(windows["fetch_start"], windows["end"])
    return build_suivi_payload(
        rows,
        windows,
        _split(agences),
        _split(secteurs),
        _split(types),
        include_lines=include_lines,
    )
