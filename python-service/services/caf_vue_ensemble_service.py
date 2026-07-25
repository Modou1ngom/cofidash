"""
Vue d'ensemble CAF (mobile) — exécution des requêtes Flexcube uniquement.

Requêtes SQL : python-service/requete mobile/caf_vue_ensemble/
Pas de dépendance aux tables DASH_* (REPORT_GROUPE).
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.oracle_pool import get_pool_flexcube

logger = logging.getLogger(__name__)

_QUERIES_DIR = (
    Path(__file__).resolve().parent.parent / "requete mobile" / "caf_vue_ensemble"
)

_TOP_ENCOURS_FILES = {
    "par_0": "les_20_gros_encours_par_0.sql",
    "par_30": "les_20_gros_encours_par_30.sql",
    "par_90": "les_20_gros_encours_par_90.sql",
    "par_180": "les_20_gros_encours_par_180.sql",
    "par_360": "les_20_gros_encours_par_360.sql",
}

# Entrées PAR : paliers DASH (DUREE_IMP_A_DATE = 1/31/91/181/361).
_ENTREES_PAR_BUCKETS = {
    "par_0": 0,
    "par_30": 30,
    "par_90": 90,
    "par_180": 180,
    "par_360": 360,
}

# Entrées PAR live Flexcube (NBRE_JOUR_RETARD = 1/31/91/181/361).
_ENTREES_PAR_ENTRY_DAYS = {
    "par_0": 1,
    "par_30": 31,
    "par_90": 91,
    "par_180": 181,
    "par_360": 361,
}


def _load_query(filename: str) -> str:
    path = _QUERIES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Requête introuvable : {path}")
    text = path.read_text(encoding="utf-8")
    return re.sub(r"^--.*\n", "", text, flags=re.MULTILINE).strip()


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [str(col[0]).lower() for col in cursor.description]
    rows = []
    for raw in cursor.fetchall():
        row = {}
        for key, value in zip(columns, raw):
            if hasattr(value, "isoformat"):
                try:
                    row[key] = value.isoformat()
                except Exception:
                    row[key] = str(value)
            else:
                row[key] = value
        rows.append(row)
    return rows


def _execute_flexcube(
    query: str,
    params: Optional[dict] = None,
    timeout_ms: int = 90_000,
) -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = timeout_ms
            cursor.execute(query, params or {})
            return _rows_to_dicts(cursor)
        finally:
            cursor.close()


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_portefeuille_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "charge_affaire": row.get("charge_affaire"),
        "branch_name": row.get("branch_name"),
        "code_gestion_pret": row.get("code_gestion_pret"),
        "encours_total": _to_float(row.get("encours_total")),
        "encours_impaye": _to_float(row.get("encours_impaye")),
        "nombre_dossier": int(_to_float(row.get("nombre_dossier"))),
        "ratio_encours_impaye": _to_float(row.get("ratio_encours_impaye")),
        "ratio_nombre_impaye": _to_float(row.get("ratio_nombre_impaye")),
        "provision_total": _to_float(row.get("provision_total")),
        "encours_par_0": _to_float(row.get("encours_par_0")),
        "par_0": _to_float(row.get("par_0")),
        "encours_par_30": _to_float(row.get("encours_par_30")),
        "par_30": _to_float(row.get("par_30")),
        "encours_par_90": _to_float(row.get("encours_par_90")),
        "par_90": _to_float(row.get("par_90")),
        "encours_par_180": _to_float(row.get("encours_par_180")),
        "par_180": _to_float(row.get("par_180")),
        "encours_par_360": _to_float(row.get("encours_par_360")),
        "par_360": _to_float(row.get("par_360")),
    }


def _normalize_top_encours_row(row: Dict[str, Any], par_key: str) -> Dict[str, Any]:
    return {
        "code_gestion_pret": row.get("code_gestion_pret"),
        "loan_number": row.get("no_dossier"),
        "client_name": row.get("nom_client"),
        "outstanding": _to_float(row.get(par_key)),
        "exigible": _to_float(row.get("exigible")),
        "par_days": int(_to_float(row.get("nbre_jour_retard"))),
        "declassement_status": row.get("statut_declassement"),
        "rank": int(_to_float(row.get("rn"))),
    }


def _resolve_month_year(
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Tuple[int, int]:
    today = date.today()
    m = int(month) if month else today.month
    y = int(year) if year else today.year
    m = max(1, min(12, m))
    return m, y


def _prev_month(month: int, year: int) -> Tuple[int, int]:
    if month == 1:
        return 12, year - 1
    return month - 1, year


def _month_year_label(month: int, year: int) -> str:
    return f"{month:02d}/{year}"


def _is_current_month(month: int, year: int) -> bool:
    today = date.today()
    return month == today.month and year == today.year


def _is_future_month(month: int, year: int) -> bool:
    today = date.today()
    return (year, month) > (today.year, today.month)


def _empty_caf_vue_ensemble(
    branch_code: Optional[str],
    caf_code: Optional[str],
    charge_affaire: Optional[str],
    month: int,
    year: int,
) -> Dict[str, Any]:
    return {
        "branch_code": branch_code,
        "caf_code": caf_code,
        "charge_affaire": charge_affaire,
        "month": month,
        "year": year,
        "portefeuille": None,
        "portefeuille_prev": None,
        "portefeuille_rows": [],
        "production": {
            "loan_count": 0.0,
            "loan_count_prev": 0.0,
            "monthly_volume": 0.0,
            "monthly_volume_prev": 0.0,
        },
        "comparison": {
            "encours_mom_pct": 0.0,
            "par_mom_pct": 0.0,
        },
        "top_encours": {},
        "par_dossier_counts": {},
        "top_provisions": [],
        "entrees_par": {},
        "production_loans": [],
        "encours_evolution": [0.0] * 12,
    }




def _rolling_month_years(
    end_month: int, end_year: int, count: int = 12
) -> List[Tuple[int, int]]:
    months: List[Tuple[int, int]] = []
    m, y = end_month, end_year
    for _ in range(count):
        months.append((m, y))
        m, y = _prev_month(m, y)
    months.reverse()
    return months


def _fetch_caf_encours_evolution_12m(
    caf_code: Optional[str],
    branch_code: Optional[str],
    month: int,
    year: int,
) -> List[float]:
    """
    Série 12 mois : Flexcube ne conserve pas de snapshot mensuel historique.
    On place l'encours live sur le mois courant (dernier point), le reste à 0.
    """
    code = str(caf_code or "").strip()
    series = [0.0] * 12
    if not code or not _is_current_month(month, year):
        return series
    try:
        rows = get_portefeuille_caf(branch_code, code)
        if rows:
            series[-1] = round(_to_float(rows[0].get("encours_total")) / 1_000_000, 3)
    except Exception as exc:
        logger.warning("Évolution encours CAF (Flexcube) indisponible pour %s: %s", code, exc)
    return series


def _fetch_dash_par_rows(month_year: str) -> List[Dict[str, Any]]:
    """Conservé pour compatibilité — Vue 360 CAF n'utilise plus DASH."""
    return []


def _pick_caf_dash_row(
    rows: List[Dict[str, Any]],
    caf_code: Optional[str],
    branch_code: Optional[str],
) -> Optional[Dict[str, Any]]:
    return None


def _normalize_dash_portefeuille_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return _normalize_portefeuille_row(row)


def _par_global_rate(portefeuille: Optional[Dict[str, Any]]) -> float:
    if not portefeuille:
        return 0.0
    rates = [
        _to_float(portefeuille.get("par_0")),
        _to_float(portefeuille.get("par_30")),
        _to_float(portefeuille.get("par_90")),
        _to_float(portefeuille.get("par_180")),
        _to_float(portefeuille.get("par_360")),
    ]
    total_rate = sum(rates)
    if total_rate > 0:
        return total_rate
    encours_total = _to_float(portefeuille.get("encours_total"))
    encours_impaye = _to_float(portefeuille.get("encours_impaye"))
    if encours_total <= 0:
        return 0.0
    return round((encours_impaye / encours_total) * 100, 2)


def _mom_pct(current: float, previous: float) -> float:
    if previous <= 0:
        return 0.0 if current <= 0 else 100.0
    return round(((current - previous) / previous) * 100, 1)


def _row_matches_caf_code(row: Dict[str, Any], caf_code: str) -> bool:
    code = str(caf_code or "").strip()
    if not code:
        return False
    for key in ("CODE_GESTION_PRET", "FIELD_CHAR_2", "code_gestion_pret", "field_char_2"):
        if str(row.get(key) or "").strip() == code:
            return True
    return False


def _production_totals_from_dash_rows(
    volume_rows: list[dict],
    nombre_rows: list[dict],
    caf_code: str,
) -> Dict[str, float]:
    volume_matches = [row for row in volume_rows if _row_matches_caf_code(row, caf_code)]
    nombre_matches = [row for row in nombre_rows if _row_matches_caf_code(row, caf_code)]
    monthly_volume = sum(_to_float(r.get("VOLUME_DEBLOQUE_M")) for r in volume_matches)
    monthly_volume_prev = sum(
        _to_float(r.get("VOLUME_DEBLOQUE_M_1")) for r in volume_matches
    )
    loan_count = sum(_to_float(r.get("NB_CRED_DECAISSES_M")) for r in nombre_matches)
    loan_count_prev = sum(
        _to_float(r.get("NB_CRED_DECAISSES_M_1")) for r in nombre_matches
    )
    return {
        "loan_count": loan_count,
        "loan_count_prev": loan_count_prev,
        "monthly_volume": monthly_volume,
        "monthly_volume_prev": monthly_volume_prev,
    }


def _fetch_caf_production_live(
    month: int,
    year: int,
    caf_code: str,
) -> Dict[str, float]:
    """Décaissements réels Flexcube du mois (et du mois précédent pour MoM)."""
    import calendar

    code = str(caf_code or "").strip()
    if not code:
        return {
            "loan_count": 0.0,
            "loan_count_prev": 0.0,
            "monthly_volume": 0.0,
            "monthly_volume_prev": 0.0,
        }

    last_day = calendar.monthrange(int(year), int(month))[1]
    month_start = f"{int(year):04d}-{int(month):02d}-01"
    month_end = f"{int(year):04d}-{int(month):02d}-{last_day:02d}"
    prev_m, prev_y = _prev_month(int(month), int(year))
    prev_last_day = calendar.monthrange(prev_y, prev_m)[1]
    prev_start = f"{prev_y:04d}-{prev_m:02d}-01"
    prev_end = f"{prev_y:04d}-{prev_m:02d}-{prev_last_day:02d}"

    sql = """
WITH DEBLOCAGE AS (
    SELECT
        account_number,
        MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
    FROM (
        SELECT
            account_number,
            COALESCE(DTYPE, 'VIDE') AS DTYPE,
            MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES
        WHERE (DTYPE <> 'X') OR DTYPE IS NULL
        GROUP BY account_number, COALESCE(DTYPE, 'VIDE')
    )
    GROUP BY account_number
)
SELECT
    COUNT(DISTINCT c.ACCOUNT_NUMBER) AS LOAN_COUNT,
    NVL(SUM(c.AMOUNT_FINANCED), 0) AS MONTHLY_VOLUME
FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
LEFT JOIN DEBLOCAGE d ON d.account_number = c.ACCOUNT_NUMBER
WHERE c.FIELD_CHAR_2 = :caf_code
  AND c.ACCOUNT_STATUS NOT IN ('L', 'V')
  AND TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)) >= TO_DATE(:month_start, 'YYYY-MM-DD')
  AND TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)) <= TO_DATE(:month_end, 'YYYY-MM-DD')
"""

    def _query_period(start: str, end: str) -> tuple[float, float]:
        rows = _execute_flexcube(
            sql,
            {
                "caf_code": code,
                "month_start": start,
                "month_end": end,
            },
        )
        if not rows:
            return 0.0, 0.0
        row = rows[0]
        return (
            _to_float(row.get("loan_count") or row.get("LOAN_COUNT")),
            _to_float(row.get("monthly_volume") or row.get("MONTHLY_VOLUME")),
        )

    try:
        loan_count, monthly_volume = _query_period(month_start, month_end)
        loan_count_prev, monthly_volume_prev = _query_period(prev_start, prev_end)
        return {
            "loan_count": loan_count,
            "loan_count_prev": loan_count_prev,
            "monthly_volume": monthly_volume,
            "monthly_volume_prev": monthly_volume_prev,
        }
    except Exception as exc:
        logger.warning("Production live CAF indisponible: %s", exc)
        return {
            "loan_count": 0.0,
            "loan_count_prev": 0.0,
            "monthly_volume": 0.0,
            "monthly_volume_prev": 0.0,
        }


def _normalize_production_loan_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "loan_number": row.get("no_dossier") or row.get("NO_DOSSIER"),
        "client_name": row.get("nom_client") or row.get("NOM_CLIENT"),
        "outstanding": _to_float(row.get("montant") or row.get("MONTANT")),
        "disbursement_date": row.get("date_decaissement") or row.get("DATE_DECAISSEMENT"),
        "exigible": 0.0,
        "par_days": 0,
    }


def _fetch_caf_production_loans(
    month: int,
    year: int,
    caf_code: Optional[str],
) -> List[Dict[str, Any]]:
    """Liste des décaissements du mois (Flexcube) pour le détail production."""
    import calendar

    code = str(caf_code or "").strip()
    if not code:
        return []

    last_day = calendar.monthrange(int(year), int(month))[1]
    month_start = f"{int(year):04d}-{int(month):02d}-01"
    month_end = f"{int(year):04d}-{int(month):02d}-{last_day:02d}"

    sql = """
WITH DEBLOCAGE AS (
    SELECT
        account_number,
        MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
    FROM (
        SELECT
            account_number,
            COALESCE(DTYPE, 'VIDE') AS DTYPE,
            MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES
        WHERE (DTYPE <> 'X') OR DTYPE IS NULL
        GROUP BY account_number, COALESCE(DTYPE, 'VIDE')
    )
    GROUP BY account_number
)
SELECT
    c.ACCOUNT_NUMBER AS NO_DOSSIER,
    c.PRIMARY_APPLICANT_NAME AS NOM_CLIENT,
    c.AMOUNT_FINANCED AS MONTANT,
    TO_CHAR(TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)), 'YYYY-MM-DD') AS DATE_DECAISSEMENT
FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
LEFT JOIN DEBLOCAGE d ON d.account_number = c.ACCOUNT_NUMBER
WHERE c.FIELD_CHAR_2 = :caf_code
  AND c.ACCOUNT_STATUS NOT IN ('L', 'V')
  AND TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)) >= TO_DATE(:month_start, 'YYYY-MM-DD')
  AND TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)) <= TO_DATE(:month_end, 'YYYY-MM-DD')
ORDER BY TRUNC(COALESCE(d.SCHEDULE_LINKAGE, c.BOOK_DATE)) DESC, c.AMOUNT_FINANCED DESC
"""

    try:
        rows = _execute_flexcube(
            sql,
            {
                "caf_code": code,
                "month_start": month_start,
                "month_end": month_end,
            },
        )
        return [_normalize_production_loan_row(r) for r in rows]
    except Exception as exc:
        logger.warning("Liste production live CAF indisponible: %s", exc)
        return []


def _fetch_caf_production(
    month: int,
    year: int,
    caf_code: Optional[str],
) -> Dict[str, float]:
    """Production mensuelle — Flexcube uniquement (décaissements du mois)."""
    code = str(caf_code or "").strip()
    if not code:
        return {
            "loan_count": 0.0,
            "loan_count_prev": 0.0,
            "monthly_volume": 0.0,
            "monthly_volume_prev": 0.0,
        }
    return _fetch_caf_production_live(month, year, code)

def _normalize_provision_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "code_gestion_pret": row.get("code_gestion_pret"),
        "loan_number": row.get("no_pret"),
        "client_name": row.get("nom_client"),
        "charge_affaire": row.get("charge_affaire"),
        "provision_total": _to_float(row.get("provision_total")),
        "rank": int(_to_float(row.get("rn"))),
    }


def _append_where(sql: str, conditions: List[str]) -> str:
    if not conditions:
        return sql
    clause = " AND ".join(conditions)
    if re.search(r"\bORDER\s+BY\b", sql, flags=re.IGNORECASE):
        return re.sub(
            r"\bORDER\s+BY\b",
            f"AND {clause}\nORDER BY",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )
    return f"{sql}\nWHERE {clause}"


def _inject_early_caf_filter(sql: str, caf_code: Optional[str]) -> str:
    """
    Pousse le filtre CODE_GESTION_PRET (FIELD_CHAR_2) dans les CTE Flexcube.
    Sans ça, les requêtes scannent tout le portefeuille puis filtrent à la fin → timeouts prod.
    """
    code = str(caf_code or "").strip()
    if not code:
        return sql

    # CTE NOMBRE_DOSSIER : FROM CLTB_ACCOUNT_MASTER p GROUP BY ...
    sql = re.sub(
        r"(FROM\s+CFSFCUBS145\.CLTB_ACCOUNT_MASTER\s+p)\s*\n(\s*)GROUP BY",
        r"\1\n\2WHERE p.FIELD_CHAR_2 = :caf_code\n\2GROUP BY",
        sql,
        count=1,
        flags=re.IGNORECASE,
    )

    # Filtres ACCOUNT_STATUS déjà présents (p / c / C)
    for alias in ("p", "c", "C"):
        pattern = (
            rf"(AND\s+{alias}\.ACCOUNT_STATUS\s+NOT\s+IN\s*\(\s*'L'\s*,\s*'V'\s*\))"
        )
        repl = rf"\1\n      AND {alias}.FIELD_CHAR_2 = :caf_code"
        sql = re.sub(pattern, repl, sql, flags=re.IGNORECASE)

    # Échéances IMPY (jointure p)
    sql = re.sub(
        r"(AND\s+CLS\.SCH_STATUS\s*=\s*'IMPY')",
        r"\1\n      AND p.FIELD_CHAR_2 = :caf_code",
        sql,
        flags=re.IGNORECASE,
    )
    return sql


def _scoped_portefeuille_query(
    branch_code: Optional[str],
    caf_code: Optional[str],
) -> tuple[str, dict]:
    sql = _load_query("portefeuille_caf.sql")
    conditions: List[str] = []
    params: dict = {}
    if caf_code:
        sql = _inject_early_caf_filter(sql, caf_code)
        conditions.append("PM.CODE_GESTION_PRET = :caf_code")
        params["caf_code"] = caf_code
    elif branch_code:
        conditions.append("PM.BRANCH_CODE = :branch_code")
        params["branch_code"] = branch_code
    if conditions:
        sql = f"{sql}\nWHERE {' AND '.join(conditions)}"
    return sql, params


def _scoped_top_encours_query(
    par_key: str,
    filename: str,
    caf_code: Optional[str],
    charge_affaire: Optional[str],
) -> tuple[str, dict]:
    sql = _load_query(filename)
    conditions: List[str] = []
    params: dict = {}
    if caf_code:
        sql = _inject_early_caf_filter(sql, caf_code)
        conditions.append("CODE_GESTION_PRET = :caf_code")
        params["caf_code"] = caf_code
    if charge_affaire:
        # Les requêtes top encours n'exposent pas CHARGE_AFFAIRE : filtre via code si fourni.
        pass
    if conditions:
        sql = _append_caf_filter_after_rn(sql, conditions)
    return sql, params


def get_portefeuille_caf(
    branch_code: Optional[str] = None,
    caf_code: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sql, params = _scoped_portefeuille_query(branch_code, caf_code)
    rows = _execute_flexcube(sql, params)
    return [_normalize_portefeuille_row(r) for r in rows]


def _normalize_dash_entree_par_row(row: Dict[str, Any]) -> Dict[str, Any]:
    par_days = int(
        _to_float(
            row.get("DUREE_IMPAYE_A_DATE")
            or row.get("duree_impaye_a_date")
            or row.get("DUREE_IMP_A_DATE")
            or row.get("duree_imp_a_date")
            or 0
        )
    )
    statut = (
        row.get("STATUT_DECLASSEMENT")
        or row.get("statut_declassement")
        or row.get("STATUT")
        or row.get("statut")
    )
    return {
        "code_gestion_pret": row.get("BLOC") or row.get("bloc"),
        "loan_number": row.get("NO_PRET") or row.get("no_pret"),
        "client_name": row.get("NOM_CLIENT") or row.get("nom_client"),
        "outstanding": _to_float(
            row.get("ENCOURS_IMPAYE") or row.get("encours_impaye")
        ),
        "exigible": _to_float(row.get("ENCOURS_TOTAL") or row.get("encours_total")),
        "par_days": par_days,
        "declassement_status": statut,
    }


def _normalize_live_entree_par_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "code_gestion_pret": row.get("code_gestion_pret"),
        "loan_number": row.get("no_dossier"),
        "client_name": row.get("nom_client"),
        "outstanding": _to_float(row.get("encours_par")),
        "exigible": _to_float(row.get("exigible")),
        "par_days": int(_to_float(row.get("nbre_jour_retard"))),
        "declassement_status": row.get("statut_declassement"),
    }


def _normalize_dash_text(value: Any) -> str:
    text = str(value or "").strip().upper()
    return re.sub(r"\s+", " ", text)


def _resolve_charge_affaire_for_caf(
    caf_code: Optional[str],
    charge_affaire: Optional[str],
) -> str:
    charge = str(charge_affaire or "").strip()
    if charge:
        return charge
    code = str(caf_code or "").strip()
    if not code:
        return ""
    try:
        from services.caf_manager_service import resolve_manager_code

        resolved = resolve_manager_code(manager_code=code)
        if resolved:
            return str(resolved.get("charge_affaire") or "").strip()
    except Exception as exc:
        logger.warning("Résolution charge affaire (%s): %s", code, exc)
    return ""


def _filter_dash_entrees_for_caf(
    rows: List[Dict[str, Any]],
    caf_code: Optional[str],
    charge_affaire: Optional[str],
    branch_code: Optional[str],
) -> List[Dict[str, Any]]:
    code = str(caf_code or "").strip()
    charge = _resolve_charge_affaire_for_caf(caf_code, charge_affaire)
    norm_charge = _normalize_dash_text(charge)
    branch = str(branch_code or "").strip()
    if not code and not charge and not branch:
        return rows

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        bloc = str(row.get("BLOC") or row.get("bloc") or "").strip()
        row_charge = str(
            row.get("CHARGE_AFFAIRE") or row.get("charge_affaire") or ""
        ).strip()
        row_branch = str(
            row.get("CODE_AGENCE") or row.get("code_agence") or ""
        ).strip()
        if code and bloc.upper() == code.upper():
            filtered.append(row)
            continue
        if charge and row_charge.upper() == charge.upper():
            filtered.append(row)
            continue
        if norm_charge and _normalize_dash_text(bloc) == norm_charge:
            filtered.append(row)
            continue
        if branch and row_branch == branch:
            filtered.append(row)
    return filtered


def _fetch_entrees_par_live(par_key: str, caf_code: str) -> List[Dict[str, Any]]:
    """Entrées PAR du mois courant via Flexcube (entre_par.sql)."""
    entry_day = _ENTREES_PAR_ENTRY_DAYS.get(par_key)
    code = str(caf_code or "").strip()
    if entry_day is None or not code:
        return []

    sql = _inject_early_caf_filter(_load_query("entre_par.sql"), code)
    sql = sql.replace(
        "WHERE NBRE_JOUR_RETARD = :par_entry_day",
        "WHERE NBRE_JOUR_RETARD = :par_entry_day\n  AND CODE_GESTION_PRET = :caf_code",
    )
    try:
        rows = _execute_flexcube(
            sql, {"par_entry_day": entry_day, "caf_code": code}
        )
    except Exception as exc:
        logger.warning("Entrées PAR live (%s) indisponible: %s", par_key, exc)
        return []

    normalized = [_normalize_live_entree_par_row(r) for r in rows]
    normalized.sort(
        key=lambda row: _to_float(row.get("outstanding")), reverse=True
    )
    return normalized


def get_entrees_par(
    par_key: str,
    branch_code: Optional[str] = None,
    caf_code: Optional[str] = None,
    charge_affaire: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Dossiers entrés dans une tranche PAR — Flexcube live uniquement.
    """
    par_bucket = _ENTREES_PAR_BUCKETS.get(par_key)
    if par_bucket is None:
        raise ValueError(f"Palier entrées PAR inconnu : {par_key}")

    code = str(caf_code or "").strip()
    if not code:
        return []
    return _fetch_entrees_par_live(par_key, code)

_PAR_AMOUNT_COLUMNS = {
    "par_0": "ENCOURS_PAR_0",
    "par_30": "ENCOURS_PAR_30",
    "par_90": "ENCOURS_PAR_90",
    "par_180": "ENCOURS_PAR_180",
    "par_360": "ENCOURS_PAR_360",
}


def _count_encours_par_dossiers(
    par_key: str,
    caf_code: Optional[str],
) -> int:
    """Nombre total de dossiers dans une tranche PAR (Flexcube live)."""
    filename = _TOP_ENCOURS_FILES.get(par_key)
    amount_col = _PAR_AMOUNT_COLUMNS.get(par_key)
    if not filename or not amount_col:
        return 0

    sql = _load_query(filename)
    if caf_code:
        sql = _inject_early_caf_filter(sql, caf_code)
    ctes, _, _ = sql.partition("SELECT *")
    if not ctes.strip():
        return 0

    count_sql = f"""{ctes.strip()}
SELECT COUNT(DISTINCT NO_DOSSIER) AS CNT
FROM PAR_DETAIL PD
WHERE NVL(PD.{amount_col}, 0) <> 0
"""
    params: dict = {}
    if caf_code:
        count_sql += "\n  AND PD.CODE_GESTION_PRET = :caf_code"
        params["caf_code"] = caf_code

    try:
        rows = _execute_flexcube(count_sql, params)
    except Exception as exc:
        logger.warning("Comptage dossiers PAR %s indisponible: %s", par_key, exc)
        return 0
    if not rows:
        return 0
    row = rows[0]
    return int(_to_float(row.get("cnt") or row.get("CNT")))


def get_top_encours_par(
    par_key: str,
    branch_code: Optional[str] = None,
    caf_code: Optional[str] = None,
    charge_affaire: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filename = _TOP_ENCOURS_FILES.get(par_key)
    if not filename:
        raise ValueError(f"Palier PAR inconnu : {par_key}")
    amount_key = f"encours_{par_key}"
    try:
        sql, params = _scoped_top_encours_query(
            par_key, filename, caf_code, charge_affaire
        )
        rows = _execute_flexcube(sql, params)
        return [_normalize_top_encours_row(r, amount_key) for r in rows]
    except Exception as exc:
        logger.warning("Top encours %s indisponible: %s", par_key, exc)
        return []


def _append_caf_filter_after_rn(sql: str, conditions: List[str]) -> str:
    if not conditions:
        return sql
    clause = " AND ".join(conditions)
    if re.search(r"\bWHERE\s+RN\s*<=", sql, flags=re.IGNORECASE):
        return re.sub(
            r"(\bWHERE\s+RN\s*<=\s*20[^\n]*)",
            rf"\1\n  AND {clause}",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )
    return _append_where(sql, conditions)


def get_top_provisions(
    caf_code: Optional[str] = None,
    charge_affaire: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sql = _load_query("les_20_gros_encours_montant_a_provisionner_caf.sql")
    conditions: List[str] = []
    params: dict = {}
    if caf_code:
        sql = _inject_early_caf_filter(sql, caf_code)
        conditions.append("CODE_GESTION_PRET = :caf_code")
        params["caf_code"] = caf_code
    if charge_affaire:
        conditions.append("UPPER(CHARGE_AFFAIRE) = UPPER(:charge_affaire)")
        params["charge_affaire"] = charge_affaire.strip()
    if conditions:
        sql = _append_caf_filter_after_rn(sql, conditions)
    try:
        rows = _execute_flexcube(sql, params)
        return [_normalize_provision_row(r) for r in rows]
    except Exception as exc:
        logger.warning("Top provisions CAF indisponible: %s", exc)
        return []


def get_caf_vue_ensemble(
    branch_codes: Optional[List[str]] = None,
    caf_code: Optional[str] = None,
    charge_affaire: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Agrège les données vue d'ensemble CAF — Flexcube uniquement.

    - portefeuille / tops / entrées PAR : live Flexcube (snapshot courant)
    - production : décaissements Flexcube du mois sélectionné
    """
    branch_code = branch_codes[0] if branch_codes else None
    selected_month, selected_year = _resolve_month_year(month, year)
    try:
        return _build_caf_vue_ensemble(
            branch_code=branch_code,
            caf_code=caf_code,
            charge_affaire=charge_affaire,
            selected_month=selected_month,
            selected_year=selected_year,
        )
    except Exception as exc:
        logger.error(
            "vue ensemble CAF échouée (mois=%s/%s, caf=%s): %s",
            selected_month,
            selected_year,
            caf_code,
            exc,
            exc_info=True,
        )
        return _empty_caf_vue_ensemble(
            branch_code, caf_code, charge_affaire, selected_month, selected_year
        )


def _build_caf_vue_ensemble(
    branch_code: Optional[str],
    caf_code: Optional[str],
    charge_affaire: Optional[str],
    selected_month: int,
    selected_year: int,
) -> Dict[str, Any]:
    if _is_future_month(selected_month, selected_year):
        return _empty_caf_vue_ensemble(
            branch_code, caf_code, charge_affaire, selected_month, selected_year
        )

    current_month = _is_current_month(selected_month, selected_year)

    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_portefeuille = (
            pool.submit(get_portefeuille_caf, branch_code, caf_code) if caf_code else None
        )
        fut_production = pool.submit(
            _fetch_caf_production, selected_month, selected_year, caf_code
        )
        fut_production_loans = (
            pool.submit(
                _fetch_caf_production_loans,
                selected_month,
                selected_year,
                caf_code,
            )
            if caf_code
            else None
        )
        fut_encours_evo = pool.submit(
            _fetch_caf_encours_evolution_12m,
            caf_code,
            branch_code,
            selected_month,
            selected_year,
        )
        live_rows = fut_portefeuille.result() if fut_portefeuille is not None else []
        production = fut_production.result()
        production_loans = (
            fut_production_loans.result() if fut_production_loans is not None else []
        )
        encours_evolution = fut_encours_evo.result()

    portefeuille = live_rows[0] if live_rows else None
    # Sans snapshot historique Flexcube : pas de portefeuille M-1 fiable.
    portefeuille_prev = None

    if caf_code and production_loans:
        production = {
            **production,
            "loan_count": float(len(production_loans)),
            "monthly_volume": sum(
                _to_float(loan.get("outstanding")) for loan in production_loans
            ),
        }

    encours_m = _to_float((portefeuille or {}).get("encours_total"))
    encours_m1 = _to_float((portefeuille_prev or {}).get("encours_total"))
    par_m = _par_global_rate(portefeuille)
    par_m1 = _par_global_rate(portefeuille_prev)

    top_encours: Dict[str, List[Dict[str, Any]]] = {}
    par_dossier_counts: Dict[str, int] = {}
    top_provisions: List[Dict[str, Any]] = []
    entrees_par: Dict[str, List[Dict[str, Any]]] = {}

    # Tops / entrées PAR : snapshot live Flexcube (utile surtout pour le mois courant).
    if caf_code and current_month:
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                entree_futs = {
                    key: pool.submit(
                        get_entrees_par,
                        key,
                        branch_code,
                        caf_code,
                        charge_affaire,
                        selected_month,
                        selected_year,
                    )
                    for key in _ENTREES_PAR_BUCKETS
                }
                entrees_par = {key: fut.result() for key, fut in entree_futs.items()}
        except Exception as exc:
            logger.warning("Entrées PAR live CAF indisponibles: %s", exc)

        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                top_futs = {
                    key: pool.submit(
                        get_top_encours_par, key, branch_code, caf_code, charge_affaire
                    )
                    for key in _TOP_ENCOURS_FILES
                }
                count_futs = {
                    key: pool.submit(_count_encours_par_dossiers, key, caf_code)
                    for key in _TOP_ENCOURS_FILES
                }
                fut_provisions = pool.submit(get_top_provisions, caf_code, charge_affaire)
                top_encours = {key: fut.result() for key, fut in top_futs.items()}
                par_dossier_counts = {
                    key: fut.result() for key, fut in count_futs.items()
                }
                top_provisions = fut_provisions.result()
        except Exception as exc:
            logger.warning("Top encours / provisions CAF indisponibles: %s", exc)

    return {
        "branch_code": branch_code,
        "caf_code": caf_code,
        "charge_affaire": charge_affaire,
        "month": selected_month,
        "year": selected_year,
        "portefeuille": portefeuille,
        "portefeuille_prev": portefeuille_prev,
        "portefeuille_rows": [portefeuille] if portefeuille else [],
        "production": production,
        "comparison": {
            "encours_mom_pct": _mom_pct(encours_m, encours_m1),
            "par_mom_pct": round(par_m - par_m1, 1),
        },
        "top_encours": top_encours,
        "par_dossier_counts": par_dossier_counts,
        "top_provisions": top_provisions,
        "entrees_par": entrees_par,
        "production_loans": production_loans,
        "encours_evolution": encours_evolution,
    }
