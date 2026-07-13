"""
Service Vue 360 mobile — agrégation Oracle Flexcube.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from database.oracle_pool import get_pool, get_pool_flexcube
from services.c360_oracle_service import fetch_remboursements_from_oracle
from services.c360_sync_service import sync_customer_c360
from services.vue360_kpi_queries import (
    AGENCY_STATS_FLEXCUBE,
    DASH_ENCOURS_12M,
    DASH_ENCOURS_12M_BY_AGENCY,
    DASH_NETWORK_PRODUCTION_BY_BRANCH,
    DASH_PAR_12M_BY_BRANCH,
    DASH_PRODUCTION_BY_AGENCY,
)
from services.vue360_dash_queries import (
    CUSTOMERS_LIST_DASH,
    CREDITS_DASH_LIST,
    CUSTOMER_BY_ID_DASH,
    CUSTOMER_BY_ID_FLEX_ONLY,
    KYC_DASH_FLEX_ONLY,
    KYC_DASH_QUERY,
)
from services.encours_repartition_query import (
    ENCOURS_REPARTITION_DETAIL,
    aggregate_encours_repartition_rows,
)
from services.vue360_queries import (
    CLIENTS_SEARCH_FLEX,
    CLIENTS_SEARCH_FLEX_PHONE_UNION,
    CREDIT_AMORTIZATION_SCHEDULE,
    CREDIT_BY_ID,
    CREDITS_LIST,
    CUSTOMER_BY_ID_LIGHT_FLEX,
    DAT_DEPOSITS,
    DASHBOARD_KPIS,
    RISKS_PAR,
)

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 50
SEARCH_LIMIT = 20


def _serialize_cell(val: Any) -> Any:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    if isinstance(val, (int, float, str, bool)):
        return val
    try:
        return float(val)
    except (TypeError, ValueError):
        return str(val)


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out: List[Dict[str, Any]] = []
    for row in rows:
        item: Dict[str, Any] = {}
        for col, cell in zip(columns, row):
            key = col.upper() if isinstance(col, str) else col
            item[key] = _serialize_cell(cell)
        out.append(item)
    return out


def _execute_query(query: str, params: dict) -> List[Dict[str, Any]]:
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 20_000
            cursor.execute(query, params)
            return _rows_to_dicts(cursor)
        finally:
            cursor.close()


def _execute_query_flexcube(query: str, params: dict) -> List[Dict[str, Any]]:
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.callTimeout = 20_000
            cursor.execute(query, params)
            return _rows_to_dicts(cursor)
        finally:
            cursor.close()


def _branch_placeholders(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders = ", ".join(f":b{i}" for i in range(len(branch_codes)))
    params = {f"b{i}": code for i, code in enumerate(branch_codes)}
    return placeholders, params


def _branch_filter(alias: str, branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND {alias}.BRANCH_CODE IN ({placeholders})", params


def _branch_filter_local(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND sc.LOCAL_BRANCH IN ({placeholders})", params


def _branch_filter_ca(branch_codes: Optional[List[str]]) -> str:
    clause, _ = _branch_filter("ca", branch_codes)
    return clause


def _branch_filter_c(branch_codes: Optional[List[str]]) -> str:
    clause, _ = _branch_filter("c", branch_codes)
    return clause


def _branch_filter_sc(branch_codes: Optional[List[str]]) -> str:
    clause, _ = _branch_filter_local(branch_codes)
    return clause.replace("sc.LOCAL_BRANCH", "sc.LOCAL_BRANCH")


def _dashboard_branch_filters(
    branch_codes: Optional[List[str]],
) -> tuple[str, str, str, dict]:
    """Filtres agence partagés pour DASHBOARD_KPIS (mêmes bind :bN réutilisés)."""
    if not branch_codes:
        return "", "", "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return (
        f"AND c.BRANCH_CODE IN ({placeholders})",
        f"AND sc.LOCAL_BRANCH IN ({placeholders})",
        f"AND ca.BRANCH_CODE IN ({placeholders})",
        params,
    )


def _to_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val or default)
    except (TypeError, ValueError):
        return default


def _repayment_rate(financed: float, outstanding: float) -> float:
    if financed <= 0:
        return 0.0
    repaid = max(0.0, financed - outstanding)
    return round((repaid / financed) * 100, 1)


def _client_status(row: Dict[str, Any]) -> str:
    par_days = int(_to_float(row.get("PAR_DAYS")))
    base = str(row.get("STATUS") or "active").lower()
    if base == "inactive":
        return "inactive"
    if par_days > 0:
        return "at_risk"
    return "active"


def _eligibility(par_days: int, outstanding: float) -> str:
    if par_days == 0 and outstanding > 0:
        return "eligible"
    if par_days <= 30:
        return "conditional"
    return "not_eligible"


def _risk_score(par_days: int, outstanding: float) -> int:
    base = min(900, int(outstanding / 100000))
    return max(100, base + par_days * 5)


def _branch_filter_customers(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND c.LOCAL_BRANCH IN ({placeholders})", params


def _branch_filter_flex_customer(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND c.LOCAL_BRANCH IN ({placeholders})", params


def _branch_filter_flex_account(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND a.BRANCH_CODE IN ({placeholders})", params


def _branch_filter_pret(branch_codes: Optional[List[str]]) -> tuple[str, dict]:
    if not branch_codes:
        return "", {}
    placeholders, params = _branch_placeholders(branch_codes)
    return f"AND p.BRANCH_CODE IN ({placeholders})", params


def _transform_client(row: Dict[str, Any]) -> Dict[str, Any]:
    customer_no = str(row.get("CUSTOMER_NO") or row.get("CUST_AC_NO") or "")
    outstanding = _to_float(row.get("TOTAL_OUTSTANDING"))
    par_days = int(_to_float(row.get("PAR_DAYS")))
    financed_proxy = outstanding + _to_float(row.get("SAVINGS_BALANCE"))
    branch = str(row.get("BRANCH_CODE") or "")
    sc_customer_no = str(row.get("SC_CUSTOMER_NO") or "").strip()
    if not sc_customer_no:
        sc_customer_no = customer_no
    return {
        "id": f"CLT-{customer_no}",
        "customer_no": customer_no,
        "sc_customer_no": sc_customer_no,
        "full_name": row.get("FULL_NAME") or "",
        "first_name": row.get("FIRST_NAME") or "",
        "last_name": row.get("LAST_NAME") or "",
        "matricule": row.get("MATRICULE") or customer_no,
        "account_number": row.get("ACCOUNT_NUMBER") or "",
        "phone": row.get("PHONE") or "",
        "segment": row.get("SEGMENT") or "Standard",
        "status": _client_status(row),
        "agency": row.get("AGENCY") or branch,
        "branch_code": branch,
        "risk_score": _risk_score(par_days, outstanding),
        "eligibility": _eligibility(par_days, outstanding),
        "total_outstanding": outstanding,
        "savings_balance": _to_float(row.get("SAVINGS_BALANCE")),
        "active_credits_count": int(_to_float(row.get("ACTIVE_CREDITS_COUNT"))),
        "repayment_rate": _repayment_rate(financed_proxy, outstanding),
        "par_days": par_days,
    }


def _finalize_credit_status(credit: Dict[str, Any]) -> Dict[str, Any]:
    account_status = str(credit.get("account_status") or "").upper()
    total_out = _to_float(credit.get("total_outstanding"))
    financed = _to_float(credit.get("financed_amount"))
    if account_status in ("L", "V") or (financed > 0 and total_out <= 0):
        credit["health_status"] = "solde"
        credit["status"] = "paid"
    return credit


def _transform_credit(row: Dict[str, Any]) -> Dict[str, Any]:
    loan_number = str(row.get("LOAN_NUMBER") or "")
    client_id = str(row.get("CLIENT_ID") or "")
    financed = _to_float(row.get("FINANCED_AMOUNT"))
    principal = _to_float(row.get("OUTSTANDING"))
    total_outstanding = _to_float(row.get("TOTAL_OUTSTANDING")) or principal
    par_days = int(_to_float(row.get("PAR_DAYS")))
    health_status = str(row.get("HEALTH_STATUS") or "sain").lower()
    unpaid = _to_float(row.get("UNPAID_AMOUNT") or row.get("OVERDUE_AMOUNT"))
    return _finalize_credit_status({
        "id": loan_number,
        "client_id": f"CLT-{client_id}" if client_id else "",
        "client_name": row.get("CLIENT_NAME") or "",
        "loan_number": loan_number,
        "financed_amount": financed,
        "outstanding": principal,
        "total_outstanding": total_outstanding,
        "status": str(row.get("STATUS") or "active").lower(),
        "health_status": health_status,
        "account_status": str(row.get("ACCOUNT_STATUS") or ""),
        "par_days": par_days,
        "repayment_percent": _to_float(row.get("REPAYMENT_PERCENT"))
        or _repayment_rate(financed, principal),
        "product_type": str(row.get("PRODUCT_TYPE") or "Crédit"),
        "product_code": str(row.get("PRODUCT_CODE") or row.get("PRODUCT_TYPE") or ""),
        "agency": row.get("AGENCY") or str(row.get("BRANCH_CODE") or ""),
        "manager": row.get("MANAGER") or row.get("MANAGER_CODE") or "",
        "loan_account": str(row.get("LOAN_ACCOUNT") or loan_number),
        "linked_account": str(row.get("LINKED_ACCOUNT") or ""),
        "account_balance": _to_float(row.get("ACCOUNT_BALANCE")),
        "disbursement_date": row.get("DISBURSEMENT_DATE") or "",
        "maturity_date": row.get("MATURITY_DATE") or "",
        "next_due_date": row.get("NEXT_DUE_DATE") or "",
        "capital_due": _to_float(row.get("CAPITAL_DUE")),
        "accrued_interest": _to_float(row.get("ACCURED_INTEREST") or row.get("ACCRUED_INTEREST")),
        "penalties": _to_float(row.get("PENALTIES")),
        "ftc_due": _to_float(row.get("FTC_DUE")),
        "acs_due": _to_float(row.get("ACS_DUE")),
        "opening_fee_due": _to_float(row.get("OPENING_FEE_DUE")),
        "coficarte_fee_due": _to_float(row.get("COFICARTE_FEE_DUE")),
        "due_amount": _to_float(row.get("DUE_AMOUNT")),
        "unpaid_amount": unpaid,
        "healthy_outstanding": _to_float(row.get("HEALTHY_OUTSTANDING")),
        "total_repaid": _to_float(row.get("TOTAL_REPAID")),
        "guarantee": "",
    })


def _parse_fr_date(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def _transform_repayment(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    debit = _to_float(row.get("MOUVEMENT_DEBIT"))
    credit = _to_float(row.get("MOUVEMENT_CREDIT"))
    amount = credit if credit > 0 else debit
    date_raw = row.get("DATE_VALEUR") or row.get("DATE_SAISIE") or ""
    return {
        "date": _parse_fr_date(str(date_raw)),
        "amount": amount,
        "method": row.get("TRN_DESC") or row.get("LIBELLE_OPERATION") or "Virement",
        "reference": f"PAY-{row.get('NO_PRET', 'REF')}-{index + 1}",
        "status": "Validé",
    }


def _normalize_customer_id(client_id: str) -> str:
    raw = str(client_id or "").strip()
    if raw.upper().startswith("CLT-"):
        return raw[4:]
    return raw


def _normalize_loan_id(loan_id: str) -> str:
    raw = str(loan_id or "").strip()
    if raw.upper().startswith("PRT-"):
        return raw[4:]
    return raw


def _is_phone_search(term: str) -> bool:
    digits = "".join(ch for ch in term if ch.isdigit())
    return len(digits) >= 7


def _infer_search_mode(term: str, field: Optional[str] = None) -> str:
    """Déduit le type de recherche pour éviter le scan UNION complet."""
    if field:
        normalized = field.strip().lower()
        aliases = {
            "account": "account",
            "account_number": "account",
            "phone": "phone",
            "mobile": "phone",
            "matricule": "matricule",
            "customer_id": "customer_id",
            "customer_no": "customer_id",
            "first_name": "first_name",
            "last_name": "name",
            "name": "name",
        }
        if normalized in aliases:
            return aliases[normalized]

    cleaned = term.strip()
    digits = "".join(ch for ch in cleaned if ch.isdigit())

    if cleaned.isdigit():
        if len(digits) == 9 and digits.startswith(("77", "78", "76", "70", "75")):
            return "phone"
        if len(digits) >= 10:
            return "account"
        if len(digits) == 8:
            return "account"
        # Matricule Flexcube (CUSTOMER_NO) — typiquement 4 à 7 chiffres.
        if 4 <= len(digits) <= 7:
            return "customer_id"
        if len(digits) == 9:
            return "phone"

    if cleaned.isalnum() and " " not in cleaned:
        if any(ch.isalpha() for ch in cleaned) and any(ch.isdigit() for ch in cleaned):
            return "customer_id"
        if any(ch.isalpha() for ch in cleaned):
            return "matricule"

    return "name"


def _search_clients_flexcube(
    search_term: str,
    mode: str,
    branch_codes: Optional[List[str]],
    limit: int,
) -> List[Dict[str, Any]]:
    """
    Recherche client Flexcube — UNION nom / n° client / n° compte
    (requête CLIENT + exclusion compte staff).
    """
    branch_filter_customer, branch_params = _branch_filter_flex_customer(branch_codes)
    branch_filter_account, _ = _branch_filter_flex_account(branch_codes)

    phone_union = ""
    if mode == "phone" or _is_phone_search(search_term):
        phone_union = CLIENTS_SEARCH_FLEX_PHONE_UNION.format(
            branch_filter_customer=branch_filter_customer
        )
        query_prefix = f"%{search_term.strip()}%"
    else:
        query_prefix = f"{search_term.strip()}%"

    sql = CLIENTS_SEARCH_FLEX.format(
        branch_filter_customer=branch_filter_customer,
        branch_filter_account=branch_filter_account,
        phone_union=phone_union,
    )
    params: dict = {
        "query_prefix": query_prefix,
        "limit": limit,
        **branch_params,
    }
    return _execute_query_flexcube(sql, params)


def _enrich_clients_sc_customer_no(clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pending: List[Dict[str, Any]] = []
    matricules: List[str] = []
    for client in clients:
        if str(client.get("sc_customer_no") or "").strip():
            continue
        matricule = str(client.get("matricule") or "").strip()
        if not matricule:
            continue
        pending.append(client)
        matricules.append(matricule)

    if not matricules:
        return clients

    unique_matricules = list(dict.fromkeys(matricules))
    placeholders = ", ".join(f":m{i}" for i in range(len(unique_matricules)))
    params = {f"m{i}": value for i, value in enumerate(unique_matricules)}
    sql = f"""
SELECT EXT_REF_NO, CUSTOMER_NO
FROM TMP_CLIENTS_FLEX
WHERE EXT_REF_NO IN ({placeholders})
"""
    try:
        rows = _execute_query(sql, params)
    except Exception as exc:
        logger.warning("Enrichissement SC_CUSTOMER_NO indisponible: %s", exc)
        return clients

    by_ext_ref = {
        str(row.get("EXT_REF_NO") or "").strip(): str(row.get("CUSTOMER_NO") or "").strip()
        for row in rows
        if str(row.get("EXT_REF_NO") or "").strip()
        and str(row.get("CUSTOMER_NO") or "").strip()
    }
    for client in pending:
        matricule = str(client.get("matricule") or "").strip()
        sc_no = by_ext_ref.get(matricule)
        if sc_no:
            client["sc_customer_no"] = sc_no
    return clients


def list_clients(
    branch_codes: Optional[List[str]] = None,
    field: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    limit = max(1, min(limit, 200))
    search_term = (query or "").strip()
    params: dict = {"limit": min(limit, SEARCH_LIMIT) if search_term else limit}

    if search_term:
        mode = _infer_search_mode(search_term, field)
        rows = _search_clients_flexcube(
            search_term,
            mode,
            branch_codes=None,
            limit=min(limit, SEARCH_LIMIT),
        )
    else:
        if not branch_codes:
            return []
        placeholders, branch_params = _branch_placeholders(branch_codes)
        sql = CUSTOMERS_LIST_DASH.format(branch_placeholders=placeholders)
        params.update(branch_params)
        rows = _execute_query(sql, params)

    clients = [_transform_client(r) for r in rows]
    if search_term:
        clients = _enrich_clients_sc_customer_no(clients)
    return clients


def _eligibility_label(code: str) -> str:
    return {
        "eligible": "Éligible",
        "conditional": "Sous conditions",
        "not_eligible": "Non éligible",
    }.get(code, code)


def _risk_label(score: int, has_credit: bool = True) -> str:
    if not has_credit:
        return "Sans crédit actif"
    if score >= 600:
        return "Bon profil"
    if score >= 300:
        return "Profil moyen"
    return "Profil à surveiller"


def _suggested_credit_amount(
    eligibility: str,
    savings: float,
    outstanding: float,
    par_days: int,
) -> float:
    if eligibility == "not_eligible" or par_days > 30:
        return 0.0
    base = max(savings, outstanding * 0.5)
    if eligibility == "eligible":
        return round(min(max(base * 2, 500_000), 50_000_000), 0)
    if eligibility == "conditional":
        return round(min(max(base, 0), 10_000_000), 0)
    return 0.0


def _behavior_summary(par_days: int, active_credits: int) -> Dict[str, str]:
    if par_days > 30:
        return {
            "title": "Historique comportement",
            "subtitle": "Retards importants — suivi renforcé",
            "status": "critical",
            "status_label": "À risque",
        }
    if par_days > 0:
        return {
            "title": "Historique comportement",
            "subtitle": "Retards constatés — suivi renforcé",
            "status": "warning",
            "status_label": "À surveiller",
        }
    if active_credits > 0:
        return {
            "title": "Historique comportement",
            "subtitle": "Remboursements à jour",
            "status": "good",
            "status_label": "Satisfaisant",
        }
    return {
        "title": "Historique comportement",
        "subtitle": "Pas d'incident récent",
        "status": "neutral",
        "status_label": "Stable",
    }


def _balance_from_compte_row(row: Dict[str, Any]) -> float:
    from services.c360_oracle_service import compte_field

    return _to_float(
        compte_field(
            row,
            "SOLDE COMPTABLE",
            "SOLDE_COMPTABLE",
            "solde_Comptable",
            "solde_comptable",
        )
    )


def _net_balance_from_compte_row(row: Dict[str, Any]) -> float:
    from services.c360_oracle_service import compte_field

    return _to_float(
        compte_field(
            row,
            "SOLDE NET DISPONIBLE",
            "SOLDE_NET_DISPONIBLE",
            "solde_Net_Disponible",
            "solde_net_disponible",
        )
    )


def _courant_account_numbers(comptes_rows: List[Dict[str, Any]]) -> List[str]:
    from services.c360_oracle_service import compte_account_number

    numbers: List[str] = []
    for row in comptes_rows:
        if str(row.get("ACCOUNT_CODE") or "").strip() != "251":
            continue
        numero = compte_account_number(row)
        if numero:
            numbers.append(numero)
    return numbers


def _fetch_client_encours_repartition(customer_no: str) -> Optional[Dict[str, float]]:
    """Exécute la requête production auto-settle ; {} = client sans lignes, None = erreur."""
    try:
        rows = _execute_query_flexcube(
            ENCOURS_REPARTITION_DETAIL,
            {"customer_no": customer_no},
        )
        if not rows:
            return {}
        return aggregate_encours_repartition_rows(rows)
    except Exception as exc:
        logger.warning(
            "Répartition encours indisponible pour %s: %s",
            customer_no,
            exc,
        )
        return None


def _repartition_has_data(totals: Optional[Dict[str, float]]) -> bool:
    if not totals:
        return False
    return any(_to_float(v) > 0 for v in totals.values())


def _zero_repartition_totals() -> Dict[str, float]:
    return {
        "capital_due": 0.0,
        "interest_due": 0.0,
        "penalty_due": 0.0,
        "ftc_due": 0.0,
        "acs_due": 0.0,
        "opening_fee_due": 0.0,
        "coficarte_fee_due": 0.0,
        "total_exigible": 0.0,
        "total_charge": 0.0,
        "total_due_amount": 0.0,
    }


def _repartition_totals_from_fetch(
    repartition_totals: Optional[Dict[str, float]],
) -> tuple[Dict[str, float], str]:
    if repartition_totals is None:
        return _zero_repartition_totals(), "unavailable"
    if not repartition_totals:
        return _zero_repartition_totals(), "none"
    return {
        "capital_due": repartition_totals.get("capital_due", 0.0),
        "interest_due": repartition_totals.get("interest_due", 0.0),
        "penalty_due": repartition_totals.get("penalty_due", 0.0),
        "ftc_due": repartition_totals.get("ftc_due", 0.0),
        "acs_due": repartition_totals.get("acs_due", 0.0),
        "opening_fee_due": repartition_totals.get("opening_fee_due", 0.0),
        "coficarte_fee_due": repartition_totals.get("coficarte_fee_due", 0.0),
        "total_exigible": repartition_totals.get("total_exigible", 0.0),
        "total_charge": repartition_totals.get("total_charge", 0.0),
        "total_due_amount": repartition_totals.get("total_due_amount", 0.0),
    }, "auto_settle" if _repartition_has_data(repartition_totals) else "none"


def _aggregate_encours_breakdown(credits: List[Dict[str, Any]]) -> Dict[str, float]:
    active = [
        c
        for c in credits
        if str(c.get("health_status") or "").lower() != "solde"
        and str(c.get("status") or "").lower() not in ("paid", "solde")
    ]
    return {
        "capital_due": round(sum(_to_float(c.get("capital_due")) for c in active), 2),
        "interest_due": round(
            sum(_to_float(c.get("accrued_interest")) for c in active), 2
        ),
        "penalty_due": round(
            sum(
                _to_float(c.get("penalty"))
                or _to_float(c.get("penalties"))
                for c in active
            ),
            2,
        ),
        "ftc_due": round(sum(_to_float(c.get("ftc_due")) for c in active), 2),
        "acs_due": round(sum(_to_float(c.get("acs_due")) for c in active), 2),
        "opening_fee_due": round(
            sum(_to_float(c.get("opening_fee_due")) for c in active), 2
        ),
        "coficarte_fee_due": round(
            sum(_to_float(c.get("coficarte_fee_due")) for c in active), 2
        ),
    }


def _encours_breakdown_items(totals: Dict[str, float]) -> List[Dict[str, Any]]:
    items = [
        {
            "id": "capital",
            "label": "Capital dû",
            "amount": totals.get("capital_due", 0.0),
            "color": "#EAB308",
        },
        {
            "id": "interest",
            "label": "Intérêt dû",
            "amount": totals.get("interest_due", 0.0),
            "color": "#3B82F6",
        },
        {
            "id": "penalty",
            "label": "Pénalité dû",
            "amount": totals.get("penalty_due", 0.0),
            "color": "#EF4444",
        },
        {
            "id": "ftc",
            "label": "FTC dû",
            "amount": totals.get("ftc_due", 0.0),
            "color": "#F59E0B",
        },
        {
            "id": "acs",
            "label": "Charge ACS dû",
            "amount": totals.get("acs_due", 0.0),
            "color": "#8B5CF6",
        },
        {
            "id": "opening_fee",
            "label": "Frais d'ouverture dû",
            "amount": totals.get("opening_fee_due", 0.0),
            "color": "#14B8A6",
        },
        {
            "id": "coficarte_fee",
            "label": "Frais coficarte dû",
            "amount": totals.get("coficarte_fee_due", 0.0),
            "color": "#EC4899",
        },
    ]
    total = sum(_to_float(i["amount"]) for i in items)
    if total <= 0:
        for item in items:
            item["percent"] = 0.0
        return items
    for item in items:
        item["percent"] = round((_to_float(item["amount"]) / total) * 100, 1)
    return items


def _last_credit_movement(
    comptes_rows: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    from services.c360_oracle_service import ecriture_field, fetch_ecritures_from_oracle

    for account_no in _courant_account_numbers(comptes_rows or []):
        try:
            rows = fetch_ecritures_from_oracle(account_no, limit=30)
        except Exception:
            continue
        for row in rows:
            credit = _to_float(
                ecriture_field(
                    row,
                    "MOUVEMENT CREDIT",
                    "MOUVEMENT_CREDIT",
                    "mouvement_credit",
                )
            )
            if credit <= 0:
                continue
            date_raw = ecriture_field(
                row,
                "DATE VALEUR",
                "DATE_VALEUR",
                "date_valeur",
                "DATE COMPTABLE",
                "DATE_SAISIE",
            )
            label = str(
                ecriture_field(
                    row,
                    "LIBELLÉ ECRITURE",
                    "LIBELLE ECRITURE",
                    "TRN_DESC",
                    "DESCRIPTION",
                    "LIBELLE_OPERATION",
                )
                or "Mouvement crédit"
            ).strip()
            return {
                "date": _parse_fr_date(str(date_raw or "")),
                "amount": credit,
                "label": label,
                "account_number": account_no,
            }
    return None


def _fetch_client_credits(
    customer_no: str,
    branch_codes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    return _fetch_credits_flexcube(
        branch_codes=branch_codes,
        client_id=customer_no,
        limit=200,
    )


def _outstanding_distribution(
    credit: float,
    epargne: float,
    dat: float,
    courant: float = 0.0,
) -> List[Dict[str, Any]]:
    items = [
        {"id": "credit", "label": "Crédit", "amount": credit, "color": "#3B82F6"},
        {"id": "epargne", "label": "Épargne", "amount": epargne, "color": "#22C55E"},
        {"id": "dat", "label": "DAT", "amount": dat, "color": "#A855F7"},
    ]
    if courant > 0:
        items.append(
            {"id": "courant", "label": "Courant", "amount": courant, "color": "#F59E0B"}
        )
    total = sum(i["amount"] for i in items)
    if total <= 0:
        for item in items:
            item["percent"] = 0.0
        return items[:3]
    for item in items:
        item["percent"] = round((item["amount"] / total) * 100, 1)
    return [i for i in items if i["amount"] > 0] or items[:3]


def _build_client_summary(
    client: Dict[str, Any],
    comptes_rows: Optional[List[Dict[str, Any]]] = None,
    credits: Optional[List[Dict[str, Any]]] = None,
    repartition_totals: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    credit_outstanding = _to_float(client.get("total_outstanding"))
    savings = _to_float(client.get("savings_balance"))
    par_days = int(_to_float(client.get("par_days")))
    active_credits = int(_to_float(client.get("active_credits_count")))
    risk_score = int(_to_float(client.get("risk_score")))
    eligibility = str(client.get("eligibility") or "conditional")
    credits = credits or []

    balances = {"courant": 0.0, "epargne": 0.0, "dat": 0.0, "depot_garantie": 0.0}
    solde_comptable = 0.0
    solde_net = 0.0
    for row in comptes_rows or []:
        code = str(row.get("ACCOUNT_CODE") or "").strip()
        amount = _balance_from_compte_row(row)
        if code == "251":
            balances["courant"] += amount
            solde_comptable += amount
            solde_net += _net_balance_from_compte_row(row)
        elif code == "253":
            balances["epargne"] += amount
        elif code == "252":
            balances["dat"] += amount
        elif code == "254":
            balances["depot_garantie"] += amount

    if not comptes_rows and savings > 0:
        balances["epargne"] = savings

    if repartition_totals is not None:
        breakdown_totals, repartition_source = _repartition_totals_from_fetch(
            repartition_totals
        )
    else:
        breakdown_totals = _zero_repartition_totals()
        repartition_source = "unavailable"
    encours_breakdown = _encours_breakdown_items(breakdown_totals)
    total_due_amount = round(_to_float(breakdown_totals.get("total_due_amount")), 2)
    total_exigible_query = round(_to_float(breakdown_totals.get("total_exigible")), 2)
    total_charge_query = round(_to_float(breakdown_totals.get("total_charge")), 2)
    if total_due_amount > 0:
        credit_encours_global = total_due_amount
    elif total_exigible_query > 0 or total_charge_query > 0:
        credit_encours_global = round(total_exigible_query + total_charge_query, 2)
    else:
        credit_encours_global = 0.0

    active_credit_rows = [
        c
        for c in credits
        if str(c.get("health_status") or "").lower() != "solde"
        and str(c.get("status") or "").lower() not in ("paid", "solde")
    ]
    has_active_credit = (
        active_credits > 0
        or credit_encours_global > 0
        or credit_outstanding > 0
        or len(active_credit_rows) > 0
    )
    if not has_active_credit:
        risk_score = 700
        eligibility = "conditional"
        eligibility_label = "À étudier"
    else:
        eligibility_label = _eligibility_label(eligibility)
    # KPI « Exigible » = échéances exigibles à date (crédits), pas le total auto-settle.
    total_exigible = round(
        sum(_to_float(c.get("due_amount")) for c in active_credit_rows), 2
    )
    if total_exigible <= 0:
        total_exigible = round(
            sum(_to_float(c.get("unpaid_amount")) for c in active_credit_rows), 2
        )

    last_movement = _last_credit_movement(comptes_rows)

    encours_global = (
        credit_encours_global
        + balances["courant"]
        + balances["epargne"]
        + balances["dat"]
        + balances["depot_garantie"]
    )
    suggested = _suggested_credit_amount(
        eligibility, balances["epargne"] + savings, credit_outstanding, par_days
    )
    behavior = _behavior_summary(par_days, active_credits)
    distribution = _outstanding_distribution(
        credit_outstanding,
        balances["epargne"],
        balances["dat"],
        balances["courant"],
    )

    return {
        "risk_score": risk_score,
        "risk_score_max": 1000,
        "risk_label": _risk_label(risk_score, has_active_credit),
        "eligibility": eligibility,
        "eligibility_label": eligibility_label,
        "suggested_amount": suggested,
        "has_active_credit": has_active_credit,
        "solde_comptable": round(solde_comptable, 2),
        "solde_net": round(solde_net, 2),
        "total_exigible": total_exigible,
        "encours_global": credit_encours_global,
        "credit_encours_global": credit_encours_global,
        "encours_credit": credit_outstanding,
        "encours_epargne": balances["epargne"],
        "encours_dat": balances["dat"],
        "encours_courant": balances["courant"],
        "encours_garantie": balances["depot_garantie"],
        "encours_change_percent": 0.0,
        "outstanding_distribution": encours_breakdown,
        "encours_breakdown": encours_breakdown,
        "encours_repartition": encours_breakdown,
        "repartition_source": repartition_source,
        "total_due_amount": total_due_amount,
        "legacy_outstanding_distribution": distribution,
        "last_credit_movement": last_movement or {},
        "behavior": behavior,
        "segmentation": str(client.get("segment") or "Standard"),
        "agency": str(client.get("agency") or ""),
        "repayment_rate": _to_float(client.get("repayment_rate")),
        "par_days": par_days,
        "active_credits_count": active_credits,
    }


def _fetch_client_from_flexcube(
    customer_no: str,
    branch_codes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    branch_clause, branch_params = _branch_filter_local(branch_codes)
    sql = CUSTOMER_BY_ID_LIGHT_FLEX.format(branch_filter=branch_clause)
    rows = _execute_query_flexcube(sql, {"customer_no": customer_no, **branch_params})
    if rows:
        return rows
    return _execute_query_flexcube(
        CUSTOMER_BY_ID_LIGHT_FLEX.format(branch_filter=""),
        {"customer_no": customer_no},
    )


def _fetch_comptes_safe(customer_no: str) -> List[Dict[str, Any]]:
    try:
        from services.c360_oracle_service import fetch_comptes_from_oracle

        return fetch_comptes_from_oracle(customer_no)
    except Exception as exc:
        logger.warning("Comptes Flexcube indisponibles pour synthèse %s: %s", customer_no, exc)
        return []


def get_client(
    client_id: str,
    branch_codes: Optional[List[str]] = None,
    refresh_cache: bool = False,
) -> Optional[Dict[str, Any]]:
    customer_no = _normalize_customer_id(client_id)

    def resolve_client_rows() -> List[Dict[str, Any]]:
        rows = _fetch_client_from_flexcube(customer_no, branch_codes)
        if not rows:
            rows = _execute_query(CUSTOMER_BY_ID_FLEX_ONLY, {"customer_no": customer_no})
        if not rows:
            branch_clause, branch_params = _branch_filter_customers(branch_codes)
            sql = CUSTOMER_BY_ID_DASH.format(branch_filter=branch_clause)
            params = {"customer_no": customer_no, **branch_params}
            rows = _execute_query(sql, params)
        return rows

    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_rows = pool.submit(resolve_client_rows)
        fut_comptes = pool.submit(_fetch_comptes_safe, customer_no)
        fut_credits = pool.submit(_fetch_client_credits, customer_no, branch_codes)
        fut_repartition = pool.submit(_fetch_client_encours_repartition, customer_no)
        rows = fut_rows.result()
        comptes_rows = fut_comptes.result()
        credits = fut_credits.result()
        repartition_totals = fut_repartition.result()

    if not rows:
        return None

    client = _transform_client(rows[0])

    if comptes_rows:
        savings_total = sum(
            _balance_from_compte_row(r)
            for r in comptes_rows
            if str(r.get("ACCOUNT_CODE") or "").strip() == "253"
        )
        if savings_total > 0:
            client["savings_balance"] = savings_total

    summary = _build_client_summary(
        client,
        comptes_rows,
        credits,
        repartition_totals=repartition_totals,
    )
    client["summary"] = summary
    client["total_outstanding"] = summary.get("credit_encours_global") or summary.get(
        "encours_credit", client.get("total_outstanding")
    )
    client["active_credits_count"] = summary.get(
        "active_credits_count", client.get("active_credits_count")
    )
    client["par_days"] = summary.get("par_days", client.get("par_days"))

    if refresh_cache:
        try:
            sync_customer_c360(customer_no)
        except Exception as exc:
            logger.warning("Sync C360 client %s échouée: %s", customer_no, exc)

    return client


def _cell_str(row: Dict[str, Any], key: str) -> str:
    val = row.get(key)
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()[:10]
        except Exception:
            return str(val).strip()
    return str(val).strip()


def _transform_kyc(row: Dict[str, Any]) -> Dict[str, Any]:
    """Mappe les 37 colonnes KYC Oracle vers l'API mobile (snake_case)."""
    return {
        "customer_no": _cell_str(row, "CUSTOMER_NO"),
        "numero_nafa": _cell_str(row, "NUMERO_NAFA"),
        "customer_prefix": _cell_str(row, "CUSTOMER_PREFIX"),
        "categorie": _cell_str(row, "CATEGORIE"),
        "customer_type": _cell_str(row, "CUSTOMER_TYPE"),
        "type_1": _cell_str(row, "TYPE_1"),
        "identification_register": _cell_str(row, "IDENTIFICATIONREGISTER"),
        "identification_register_1": _cell_str(row, "IDENTIFICATIONREGISTER_1"),
        "country": _cell_str(row, "COUNTRY"),
        "language": _cell_str(row, "LANGUAGE"),
        "genre": _cell_str(row, "GENRE"),
        "middle_name": _cell_str(row, "MIDDLE_NAME"),
        "first_name": _cell_str(row, "FIRST_NAME"),
        "full_name": _cell_str(row, "FULL_NAME"),
        "date_of_birth": _cell_str(row, "DATE_OF_BIRTH"),
        "place_of_birth": _cell_str(row, "PLACE_OF_BIRTH"),
        "sex": _cell_str(row, "SEX"),
        "p_national_id": _cell_str(row, "P_NATIONAL_ID"),
        "passport_no": _cell_str(row, "PASSPORT_NO"),
        "ppt_iss_date": _cell_str(row, "PPT_ISS_DATE"),
        "ppt_exp_date": _cell_str(row, "PPT_EXP_DATE"),
        "d_address1": _cell_str(row, "D_ADDRESS1"),
        "e_mail": _cell_str(row, "E_MAIL"),
        "mob_isd_no": _cell_str(row, "MOB_ISD_NO"),
        "telephone": _cell_str(row, "TELEPHONE"),
        "mobile_number": _cell_str(row, "MOBILE_NUMBER"),
        "mother_maiden_name": _cell_str(row, "MOTHER_MAIDEN_NAME"),
        "sc_customer_no": _cell_str(row, "SC_CUSTOMER_NO"),
        "local_branch": _cell_str(row, "LOCAL_BRANCH"),
        "branch_name": _cell_str(row, "BRANCH_NAME"),
        "record_stat": _cell_str(row, "RECORD_STAT"),
        "date_creation": _cell_str(row, "DATE_CREATION"),
        "cust_cat": _cell_str(row, "CUST_CAT"),
        "cust_cat_desc": _cell_str(row, "CUST_CAT_DESC"),
        "unique_id_name": _cell_str(row, "UNIQUE_ID_NAME"),
        "unique_id_value": _cell_str(row, "UNIQUE_ID_VALUE"),
    }


def get_kyc(
    client_id: str,
    branch_codes: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    lookup = _normalize_customer_id(client_id)

    try:
        from services.c360_oracle_service import fetch_kyc_from_oracle

        flex_row = fetch_kyc_from_oracle(lookup)
        if flex_row:
            return _transform_kyc(flex_row)
    except Exception as exc:
        logger.warning("KYC Flexcube indisponible pour %s: %s", lookup, exc)

    branch_clause, branch_params = _branch_filter_customers(branch_codes)
    sql = KYC_DASH_QUERY.format(branch_filter=branch_clause)
    params = {"customer_no": lookup, **branch_params}
    rows = _execute_query(sql, params)
    if not rows:
        rows = _execute_query(
            KYC_DASH_FLEX_ONLY,
            {"customer_no": lookup},
        )
    if not rows:
        return None

    return _transform_kyc(rows[0])


_ACCOUNT_CODE_TO_TYPE = {
    "251": "courant",
    "253": "epargne",
    "252": "dat",
    "254": "depot_garantie",
}

_ACCOUNT_TYPE_SUMMARIES = (
    ("courant", "Courant", "Comptes courants"),
    ("epargne", "Épargne", "Comptes épargne"),
    ("dat", "DAT", "Dépôts à terme"),
    ("depot_garantie", "Garantie", "Dépôts de garantie"),
)

_VALID_ACCOUNT_TYPES = frozenset(t[0] for t in _ACCOUNT_TYPE_SUMMARIES)


def _account_type_from_row(row: Dict[str, Any]) -> str:
    code = str(row.get("ACCOUNT_CODE") or "").strip()
    return _ACCOUNT_CODE_TO_TYPE.get(code, "courant")


def _account_status_api(statut: Any) -> str:
    label = str(statut or "").strip().lower()
    if "clôtur" in label or "clos" in label:
        return "closed"
    if "inactif" in label:
        return "inactive"
    return "active"


def _transform_account(row: Dict[str, Any]) -> Dict[str, Any]:
    from services.c360_oracle_service import compte_account_number, compte_field

    account_type = _account_type_from_row(row)
    numero = compte_account_number(row) or str(row.get("NUMERO_COMPTE") or "").strip()
    libelle = str(
        compte_field(
            row,
            "LIBELLÉ COMPTE",
            "LIBELLE COMPTE",
            "TYPE_COMPTE",
            "type_Compte",
            "DESCRIPTION",
        )
        or ""
    ).strip()
    branch_code = str(
        compte_field(row, "AGENCE_COMPTE", "agence_Compte", "agence_compte") or ""
    ).strip()
    branch_name = str(
        compte_field(row, "AGENCE", "BRANCH_NAME", "branch_name") or branch_code
    ).strip()
    balance = _to_float(
        compte_field(
            row,
            "SOLDE COMPTABLE",
            "SOLDE_COMPTABLE",
            "solde_Comptable",
            "solde_comptable",
        )
    )
    available = _to_float(
        compte_field(
            row,
            "SOLDE NET DISPONIBLE",
            "SOLDE_NET_DISPONIBLE",
            "solde_Net_Disponible",
            "solde_net_disponible",
        )
    )
    blocked = _to_float(
        compte_field(
            row,
            "MONTANT INDISPONIBLE",
            "MONTANT_INDISPONIBLE",
            "montant_Indisponible",
            "montant_indisponible",
        )
    )
    amount_due = _to_float(
        compte_field(row, "MONTANT_DUE", "montant_due", "MONTANT DUE")
    )
    opened_at = str(
        compte_field(
            row,
            "DATE OUVERTURE",
            "DATE_OUVERTURE",
            "date_Ouverture",
            "date_ouverture",
        )
        or ""
    ).strip()
    statut = compte_field(
        row,
        "STATUT COMPTE",
        "STATUT_COMPTE",
        "statut_Compte",
        "statut_compte",
    )
    return {
        "id": numero,
        "account_number": numero,
        "type": account_type,
        "type_label": next(
            (label for tid, label, _ in _ACCOUNT_TYPE_SUMMARIES if tid == account_type),
            "Compte",
        ),
        "type_description": libelle,
        "account_class": str(
            compte_field(row, "CODE_TYPE_COMPTE", "code_Type_Compte", "code_type_compte")
            or ""
        ).strip(),
        "branch_code": branch_code,
        "branch_name": branch_name,
        "balance": balance,
        "available_balance": available,
        "blocked_amount": blocked,
        "amount_due": amount_due,
        "montant_due": amount_due,
        "status": _account_status_api(statut),
        "opened_at": opened_at,
        "solde_comptable": balance,
        "solde_net_disponible": available,
        "montant_indisponible": blocked,
        "date_ouverture": opened_at,
        "statut_compte": str(statut or "").strip(),
        "libelle_compte": libelle,
        "agence": branch_name,
        "numero_compte": numero,
    }


def _transform_transaction(
    row: Dict[str, Any],
    *,
    client_name: str = "",
    account_number: str = "",
) -> Dict[str, Any]:
    from services.c360_oracle_service import ecriture_field

    nom_client = str(
        ecriture_field(row, "NOM CLIENT ", "NOM CLIENT", "DESCRIPTION") or client_name
    ).strip()
    numero = str(
        ecriture_field(row, "NUMERO COMPTE", "ACCOUNT_NO", "account_no")
        or account_number
    ).strip()
    debit = _to_float(
        ecriture_field(
            row,
            "MOUVEMENT DEBIT",
            "MOUVEMENT_DEBIT",
            "mouvement_debit",
        )
    )
    credit = _to_float(
        ecriture_field(
            row,
            "MOUVEMENT CREDIT",
            "MOUVEMENT_CREDIT",
            "mouvement_credit",
        )
    )
    date_comptable = str(
        ecriture_field(
            row,
            "DATE COMPTABLE",
            "DATE_SAISIE",
            "date_saisie",
        )
        or ""
    ).strip()
    date_valeur = str(
        ecriture_field(row, "DATE VALEUR", "DATE_VALEUR", "date_valeur") or ""
    ).strip()
    entry_label = str(
        ecriture_field(
            row,
            "LIBELLÉ ECRITURE",
            "LIBELLE ECRITURE",
            "TRN_DESC",
            "DESCRIPTION",
            "LIBELLE_OPERATION",
        )
        or ""
    ).strip()
    batch_label = str(
        ecriture_field(
            row,
            "LIBELLÉ N° BATCH",
            "LIBELLE N° BATCH",
            "LIBELLE N BATCH",
            "DESCRIPTION_BATCH",
            "description_batch",
        )
        or ""
    ).strip()
    amount = credit if credit > 0 else debit
    direction = "credit" if credit > 0 else "debit"
    return {
        "client_name": nom_client,
        "account_number": numero,
        "debit": debit,
        "credit": credit,
        "amount": amount,
        "direction": direction,
        "accounting_date": date_comptable,
        "value_date": date_valeur,
        "entry_label": entry_label,
        "batch_label": batch_label,
        "description": entry_label or batch_label,
        "nom_client": nom_client,
        "numero_compte": numero,
        "mouvement_debit": debit,
        "mouvement_credit": credit,
        "date_comptable": date_comptable,
        "date_valeur": date_valeur,
        "libelle_ecriture": entry_label,
        "libelle_batch": batch_label,
    }


def _fetch_client_accounts_rows(customer_no: str) -> List[Dict[str, Any]]:
    from services.c360_oracle_service import fetch_comptes_from_oracle

    try:
        return fetch_comptes_from_oracle(customer_no)
    except Exception as exc:
        logger.warning("Comptes Flexcube indisponibles pour %s: %s", customer_no, exc)
        return []


def list_client_accounts(
    client_id: str,
    account_type: Optional[str] = None,
    refresh: bool = False,
    ecritures_limit: int = 10,
) -> Dict[str, Any]:
    del refresh, ecritures_limit  # réservés pour cache C360 ultérieur
    customer_no = _normalize_customer_id(client_id)
    normalized_type: Optional[str] = None
    if account_type:
        normalized_type = account_type.strip().lower()
        if normalized_type not in _VALID_ACCOUNT_TYPES:
            raise ValueError(f"Type de compte invalide: {account_type}")

    rows = _fetch_client_accounts_rows(customer_no)
    all_accounts: List[Dict[str, Any]] = []
    for row in rows:
        account = _transform_account(row)
        if account.get("account_number"):
            all_accounts.append(account)

    counts = {tid: 0 for tid, _, _ in _ACCOUNT_TYPE_SUMMARIES}
    for account in all_accounts:
        counts[account["type"]] = counts.get(account["type"], 0) + 1

    types = [
        {
            "id": type_id,
            "label": label,
            "subtitle": subtitle,
            "count": counts.get(type_id, 0),
        }
        for type_id, label, subtitle in _ACCOUNT_TYPE_SUMMARIES
    ]

    accounts = all_accounts
    if normalized_type:
        accounts = [a for a in all_accounts if a["type"] == normalized_type]

    return {
        "types": types,
        "accounts": accounts,
        "total_accounts": len(all_accounts),
    }


def get_client_account(
    client_id: str,
    account_number: str,
    refresh: bool = False,
    transactions_limit: int = 20,
) -> Optional[Dict[str, Any]]:
    del refresh
    from services.c360_oracle_service import (
        compte_account_number,
        fetch_ecritures_from_oracle,
    )

    customer_no = _normalize_customer_id(client_id)
    account_key = str(account_number or "").strip()
    rows = _fetch_client_accounts_rows(customer_no)

    client_name = ""
    try:
        client = get_client(client_id)
        if client:
            client_name = str(client.get("full_name") or "").strip()
    except Exception as exc:
        logger.warning("Nom client indisponible pour %s: %s", client_id, exc)

    for row in rows:
        numero = compte_account_number(row) or str(row.get("NUMERO_COMPTE") or "").strip()
        if numero != account_key:
            continue
        account = _transform_account(row)
        if transactions_limit > 0:
            try:
                ecritures = fetch_ecritures_from_oracle(
                    account_key,
                    limit=max(1, min(transactions_limit, 100)),
                )
            except Exception as exc:
                logger.warning(
                    "Écritures indisponibles pour %s: %s", account_key, exc
                )
                ecritures = []
            account["transactions"] = [
                _transform_transaction(
                    entry,
                    client_name=client_name,
                    account_number=account_key,
                )
                for entry in ecritures
            ]
        return account

    return None


def _soft_scoring(
    total_outstanding: float,
    total_unpaid: float,
    max_par_days: int,
    avg_repayment: float,
) -> int:
    if total_outstanding <= 0:
        return 100
    unpaid_ratio = total_unpaid / total_outstanding if total_outstanding else 0.0
    score = 100.0
    score -= min(40.0, unpaid_ratio * 100.0)
    score -= min(30.0, max_par_days / 3.0)
    score += min(20.0, avg_repayment / 5.0)
    return max(0, min(100, int(round(score))))


def _build_credits_summary(credits: List[Dict[str, Any]]) -> Dict[str, Any]:
    active = [c for c in credits if c.get("health_status") not in ("solde",)]
    total_global = sum(_to_float(c.get("total_outstanding")) for c in active)
    total_healthy = sum(_to_float(c.get("healthy_outstanding")) for c in active)
    total_unpaid = sum(_to_float(c.get("unpaid_amount")) for c in active)
    total_due = sum(_to_float(c.get("due_amount")) for c in active)
    max_par = max((int(c.get("par_days") or 0) for c in active), default=0)
    repayments = [
        _to_float(c.get("repayment_percent"))
        for c in credits
        if _to_float(c.get("financed_amount")) > 0
    ]
    avg_repayment = sum(repayments) / len(repayments) if repayments else 0.0
    counts = {
        "sain": sum(1 for c in credits if c.get("health_status") == "sain"),
        "impaye": sum(1 for c in credits if c.get("health_status") == "impaye"),
        "solde": sum(1 for c in credits if c.get("health_status") == "solde"),
    }
    return {
        "encours_global": round(total_global, 2),
        "encours_global_label": "Capital + intérêts + pénalités",
        "total_encours_sain": round(total_healthy, 2),
        "total_encours_impaye": round(total_unpaid, 2),
        "total_exigible": round(total_due, 2),
        "soft_scoring": _soft_scoring(total_global, total_unpaid, max_par, avg_repayment),
        "counts": counts,
        "active_credits_count": len(active),
        "total_credits_count": len(credits),
    }


def list_credits(
    branch_codes: Optional[List[str]] = None,
    client_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> Any:
    limit = max(1, min(limit, 200))
    customer_no = _normalize_customer_id(client_id) if client_id else ""
    credits = _fetch_credits_flexcube(branch_codes, client_id, limit)
    if not credits and client_id:
        credits = _fetch_credits_dash(branch_codes, client_id, limit)
    if customer_no:
        for credit in credits:
            credit["client_id"] = f"CLT-{customer_no}"
    if client_id:
        return {
            "summary": _build_credits_summary(credits),
            "credits": credits,
        }
    return credits


def _fetch_credits_flexcube(
    branch_codes: Optional[List[str]] = None,
    client_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    if client_id:
        branch_clause, branch_params = "", {}
    else:
        branch_clause, branch_params = _branch_filter("c", branch_codes)
    client_filter = ""
    active_filter = "AND c.ACCOUNT_STATUS NOT IN ('L', 'V')"
    params: dict = {"limit": limit, **branch_params}

    if client_id:
        customer_no = _normalize_customer_id(client_id)
        client_filter = "AND c.CUSTOMER_ID = :customer_no"
        params["customer_no"] = customer_no
        active_filter = ""

    sql = CREDITS_LIST.format(
        client_filter=client_filter,
        branch_filter=branch_clause,
        active_filter=active_filter,
    )
    try:
        rows = _execute_query_flexcube(sql, params)
        return [_transform_credit(r) for r in rows]
    except Exception as exc:
        logger.warning("Crédits Flexcube indisponibles: %s", exc)
        return []


def _fetch_credits_dash(
    branch_codes: Optional[List[str]] = None,
    client_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    if client_id:
        branch_clause, branch_params = "", {}
    else:
        branch_clause, branch_params = _branch_filter_pret(branch_codes)
    client_filter = ""
    params: dict = {"limit": limit, **branch_params}

    if client_id:
        customer_no = _normalize_customer_id(client_id)
        client_filter = "AND (f.CUSTOMER_NO = :customer_no OR p.CR_PROD_AC LIKE :customer_like)"
        params["customer_no"] = customer_no
        params["customer_like"] = f"%{customer_no}%"

    sql = CREDITS_DASH_LIST.format(client_filter=client_filter, branch_filter=branch_clause)
    try:
        rows = _execute_query(sql, params)
        return [_transform_credit(r) for r in rows]
    except Exception as exc:
        logger.warning("Crédits DASH_PRET indisponibles: %s", exc)
        return []


def get_credit(
    loan_id: str,
    branch_codes: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    loan_number = _normalize_loan_id(loan_id)
    sql = CREDIT_BY_ID.format(branch_filter="")
    params = {"loan_number": loan_number}
    try:
        rows = _execute_query_flexcube(sql, params)
        if rows:
            return _transform_credit(rows[0])
    except Exception as exc:
        logger.warning("Crédit Flexcube indisponible pour %s: %s", loan_number, exc)

    if branch_codes:
        branch_clause, branch_params = _branch_filter("c", branch_codes)
        sql_scoped = CREDIT_BY_ID.format(branch_filter=branch_clause)
        params_scoped = {"loan_number": loan_number, **branch_params}
        try:
            rows = _execute_query_flexcube(sql_scoped, params_scoped)
            if rows:
                return _transform_credit(rows[0])
        except Exception as exc:
            logger.warning(
                "Crédit Flexcube (périmètre) indisponible pour %s: %s",
                loan_number,
                exc,
            )

    return None


def get_repayments(loan_id: str, refresh_cache: bool = False) -> List[Dict[str, Any]]:
    loan_number = _normalize_loan_id(loan_id)
    rows = fetch_remboursements_from_oracle(loan_number)
    return [_transform_repayment(r, i) for i, r in enumerate(rows)]


def _ta_status_label(code: Optional[str]) -> str:
    return {
        "I": "Impayé",
        "R": "Remboursé",
        "A": "Attente",
    }.get(str(code or "").upper(), "")


def _transform_ta_installment(row: Dict[str, Any]) -> Dict[str, Any]:
    status_code = str(row.get("STATUS") or "").upper()
    due_date = row.get("SCHEDULE_DUE_DATE")
    if hasattr(due_date, "isoformat"):
        due_date = due_date.isoformat()[:10]
    elif due_date is not None:
        due_date = str(due_date)[:10]
    else:
        due_date = ""
    return {
        "installment_number": int(_to_float(row.get("NUMERO_ECHEANCE"))),
        "due_date": due_date,
        "installment_amount": round(_to_float(row.get("MONTANT_ECHEANCE")), 2),
        "paid_amount": round(_to_float(row.get("MONTANT_ECHEANCE_PAYE")), 2),
        "unpaid_amount": round(_to_float(row.get("MONTANT_ECHEANCE_IMPY")), 2),
        "penalty": round(_to_float(row.get("PENALITE")), 2),
        "due_total": round(_to_float(row.get("EXIGIBLE")), 2),
        "status": status_code.lower() if status_code else "",
        "status_label": _ta_status_label(status_code),
    }


def get_amortization_schedule(loan_id: str) -> Dict[str, Any]:
    loan_number = _normalize_loan_id(loan_id)
    try:
        rows = _execute_query_flexcube(
            CREDIT_AMORTIZATION_SCHEDULE,
            {"loan_number": loan_number},
        )
    except Exception as exc:
        logger.warning("TA Flexcube indisponible pour %s: %s", loan_number, exc)
        rows = []

    installments: List[Dict[str, Any]] = []
    totals: Dict[str, Any] = {}
    for row in rows:
        if row.get("ACCOUNT_NUMBER") is None and row.get("NUMERO_ECHEANCE") is None:
            totals = {
                "installment_amount": round(_to_float(row.get("MONTANT_ECHEANCE")), 2),
                "paid_amount": round(_to_float(row.get("MONTANT_ECHEANCE_PAYE")), 2),
                "unpaid_amount": round(_to_float(row.get("MONTANT_ECHEANCE_IMPY")), 2),
                "penalty": round(_to_float(row.get("PENALITE")), 2),
                "due_total": round(_to_float(row.get("EXIGIBLE")), 2),
            }
            continue
        installments.append(_transform_ta_installment(row))

    return {
        "loan_number": loan_number,
        "installments": installments,
        "totals": totals,
    }


def list_dat_deposits(
    branch_codes: Optional[List[str]] = None,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    limit = max(1, min(limit, 200))
    branch_clause, branch_params = _branch_filter("ca", branch_codes)
    sql = DAT_DEPOSITS.format(branch_filter=branch_clause)
    params = {"limit": limit, **branch_params}
    rows = _execute_query(sql, params)
    return [
        {
            "id": f"DAT-{row.get('ID')}",
            "label": row.get("LABEL") or "DAT",
            "amount": _to_float(row.get("AMOUNT")),
            "maturity_date": row.get("MATURITY_DATE") or "",
            "client_id": f"CLT-{row.get('CLIENT_ID')}",
            "client_name": row.get("CLIENT_NAME") or "",
        }
        for row in rows
    ]


def get_dashboard_kpis(branch_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    branch_filter_c, branch_filter_sc, branch_filter_ca, params = _dashboard_branch_filters(
        branch_codes
    )
    sql = DASHBOARD_KPIS.format(
        branch_filter_c=branch_filter_c,
        branch_filter_sc=branch_filter_sc,
        branch_filter_ca=branch_filter_ca,
    )
    rows = _execute_query(sql, params)
    row = rows[0] if rows else {}
    active_credits = int(_to_float(row.get("ACTIVE_CREDITS")))
    global_outstanding = _to_float(row.get("GLOBAL_OUTSTANDING"))
    overdue = int(_to_float(row.get("OVERDUE_CREDITS")))
    repayment_rate = 100.0
    if active_credits > 0:
        repayment_rate = round(max(0.0, 100.0 - (overdue / active_credits * 100)), 1)

    production = _fetch_network_production(branch_codes)
    monthly_production = production.get("monthly_production", 0.0)
    monthly_prev = production.get("monthly_production_prev", 0.0)
    charts = _fetch_charts_12m(branch_codes)

    par30 = charts["par"][-1] if charts["par"] else (
        round((overdue / active_credits * 100) if active_credits else 0, 1)
    )
    par90 = round(par30 * 0.45, 1) if par30 else 0.0

    return {
        "active_credits": active_credits,
        "global_outstanding": global_outstanding,
        "repayment_rate": repayment_rate,
        "par30": par30,
        "par90": par90,
        "overdue_credits": overdue,
        "active_clients": int(_to_float(row.get("ACTIVE_CLIENTS"))),
        "savings_collected": _to_float(row.get("SAVINGS_COLLECTED")),
        "critical_alerts": overdue,
        "monthly_production": monthly_production,
        "monthly_production_target": monthly_prev if monthly_prev > 0 else monthly_production,
        "chart_encours": charts["encours"],
        "chart_par": charts["par"],
    }


def get_risks(branch_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    branch_filter_c, _, _, params = _dashboard_branch_filters(branch_codes)
    sql = RISKS_PAR.format(branch_filter_c=branch_filter_c)
    rows = _execute_query(sql, params)
    by_cat = {str(r.get("PAR_CATEGORY")): r for r in rows}
    result = []
    for cat in ("par0", "par30", "par90", "par180", "par360"):
        row = by_cat.get(cat, {})
        result.append(
            {
                "par_category": cat,
                "client_count": int(_to_float(row.get("CLIENT_COUNT"))),
                "total_exposure": _to_float(row.get("TOTAL_EXPOSURE")),
                "trend": 0.0,
            }
        )
    return result


def list_opportunities(clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    opportunities = []
    idx = 1
    for client in clients:
        if client.get("eligibility") != "eligible":
            continue
        if client.get("active_credits_count", 0) <= 0:
            continue
        opportunities.append(
            {
                "id": f"OPP-{idx:03d}",
                "client_id": client.get("id"),
                "client_name": client.get("full_name"),
                "type": "renewal",
                "risk_level": "good" if client.get("par_days", 0) == 0 else "medium",
                "recommended_amount": round(client.get("total_outstanding", 0) * 0.5),
                "score": client.get("risk_score", 500),
                "recommendation": "Renouvellement recommandé — bon historique de remboursement",
            }
        )
        idx += 1
        if idx > 20:
            break
    return opportunities


def list_notifications(clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    notifications = []
    idx = 1
    for client in clients:
        if client.get("status") != "at_risk":
            continue
        notifications.append(
            {
                "id": f"NOT-{idx:03d}",
                "title": "Client à risque",
                "body": (
                    f"{client.get('full_name')} — PAR {client.get('par_days')} jours, "
                    f"encours {client.get('total_outstanding'):,.0f} FCFA"
                ),
                "type": "risk",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_read": False,
                "priority": "high" if client.get("par_days", 0) > 30 else "medium",
            }
        )
        idx += 1
        if idx > 30:
            break
    return notifications


def _current_month_year() -> str:
    today = date.today()
    return f"{today.month:02d}/{today.year}"


def _performance_pct(current: float, previous: float) -> float:
    if previous <= 0:
        return 0.0 if current <= 0 else 100.0
    return round(((current - previous) / previous) * 100, 1)


def _normalize_branch_codes(branch_codes: Optional[List[str]]) -> List[str]:
    return [str(c).strip() for c in (branch_codes or []) if str(c).strip()]


def _fetch_flexcube_agency_stats(branch_codes: List[str]) -> Dict[str, Dict[str, Any]]:
    if not branch_codes:
        return {}
    placeholders, params = _branch_placeholders(branch_codes)
    sql = AGENCY_STATS_FLEXCUBE.format(branch_placeholders=placeholders)
    rows = _execute_query(sql, params)
    return {str(r.get("BRANCH_CODE", "")).strip(): r for r in rows}


def _fetch_production_by_agency(branch_codes: List[str]) -> Dict[str, Dict[str, float]]:
    if not branch_codes:
        return {}
    placeholders, params = _branch_placeholders(branch_codes)
    params["month_year"] = _current_month_year()
    sql = DASH_PRODUCTION_BY_AGENCY.format(branch_placeholders=placeholders)
    try:
        rows = _execute_query(sql, params)
    except Exception as exc:
        logger.warning("DASH production agences indisponible: %s", exc)
        return {}
    out: Dict[str, Dict[str, float]] = {}
    for row in rows:
        code = str(row.get("CODE_AGENCE", "")).strip()
        out[code] = {
            "monthly_production": _to_float(row.get("MONTHLY_PRODUCTION")),
            "monthly_production_prev": _to_float(row.get("MONTHLY_PRODUCTION_PREV")),
        }
    return out


def _fetch_network_production(branch_codes: Optional[List[str]]) -> Dict[str, float]:
    codes = _normalize_branch_codes(branch_codes)
    params: dict = {"month_year": _current_month_year()}
    try:
        if codes:
            placeholders, branch_params = _branch_placeholders(codes)
            sql = DASH_NETWORK_PRODUCTION_BY_BRANCH.format(
                branch_placeholders=placeholders,
            )
            params.update(branch_params)
        else:
            from services.vue360_kpi_queries import DASH_NETWORK_PRODUCTION
            sql = DASH_NETWORK_PRODUCTION.format(branch_filter="")
        rows = _execute_query(sql, params)
        row = rows[0] if rows else {}
        return {
            "monthly_production": _to_float(row.get("MONTHLY_PRODUCTION")),
            "monthly_production_prev": _to_float(row.get("MONTHLY_PRODUCTION_PREV")),
        }
    except Exception as exc:
        logger.warning("DASH production réseau indisponible: %s", exc)
        return {"monthly_production": 0.0, "monthly_production_prev": 0.0}


def _fetch_charts_12m(branch_codes: Optional[List[str]]) -> Dict[str, List[float]]:
    codes = _normalize_branch_codes(branch_codes)
    encours = [0.0] * 12
    par = [0.0] * 12
    if not codes:
        return {"encours": encours, "par": par}
    placeholders, params = _branch_placeholders(codes)
    try:
        enc_rows = _execute_query(
            DASH_ENCOURS_12M.format(branch_placeholders=placeholders),
            params,
        )
        encours = [_to_float(r.get("PTF_M")) / 1_000_000 for r in enc_rows]
        while len(encours) < 12:
            encours.insert(0, 0.0)
        encours = encours[-12:]
    except Exception as exc:
        logger.warning("DASH encours 12M indisponible: %s", exc)

    try:
        par_rows = _execute_query(
            DASH_PAR_12M_BY_BRANCH.format(branch_placeholders=placeholders),
            params,
        )
        par = [_to_float(r.get("PAR30")) for r in par_rows]
        while len(par) < 12:
            par.insert(0, 0.0)
        par = par[-12:]
    except Exception as exc:
        logger.warning("DASH PAR 12M indisponible: %s", exc)

    return {"encours": encours, "par": par}


def _fetch_encours_evolution_by_agency(branch_codes: List[str]) -> Dict[str, List[float]]:
    codes = _normalize_branch_codes(branch_codes)
    result = {code: [0.0] * 12 for code in codes}
    if not codes:
        return result
    placeholders, params = _branch_placeholders(codes)
    try:
        rows = _execute_query(
            DASH_ENCOURS_12M_BY_AGENCY.format(branch_placeholders=placeholders),
            params,
        )
        by_agency: Dict[str, List[float]] = {code: [] for code in codes}
        for row in rows:
            code = str(row.get("CODE_AGENCE", "")).strip()
            if code not in by_agency:
                by_agency[code] = []
            by_agency[code].append(_to_float(row.get("PTF_M")) / 1_000_000)
        for code in codes:
            series = by_agency.get(code, [])
            while len(series) < 12:
                series.insert(0, 0.0)
            result[code] = series[-12:]
    except Exception as exc:
        logger.warning("DASH encours par agence indisponible: %s", exc)
    return result


def get_agencies_kpis(
    agencies: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Enrichit la liste d'agences (code, name, zone) avec KPI Oracle.
    agencies: [{code, name, zone, category?}, ...]
    """
    if not agencies:
        return []

    branch_codes = [str(a.get("code", "")).strip() for a in agencies if a.get("code")]
    flex_stats = _fetch_flexcube_agency_stats(branch_codes)
    production = _fetch_production_by_agency(branch_codes)
    encours_by_agency = _fetch_encours_evolution_by_agency(branch_codes)

    enriched: List[Dict[str, Any]] = []
    for agency in agencies:
        code = str(agency.get("code", "")).strip()
        stats = flex_stats.get(code, {})
        prod = production.get(code, {})
        monthly = prod.get("monthly_production", 0.0)
        monthly_prev = prod.get("monthly_production_prev", 0.0)
        enriched.append(
            {
                "id": f"AG-{code}",
                "name": agency.get("name") or stats.get("BRANCH_NAME") or "",
                "zone": agency.get("zone") or "",
                "category": agency.get("category") or "agence",
                "branch_code": code,
                "active_clients": int(_to_float(stats.get("ACTIVE_CLIENTS"))),
                "active_credits": int(_to_float(stats.get("ACTIVE_CREDITS"))),
                "total_outstanding": _to_float(stats.get("TOTAL_OUTSTANDING")),
                "savings_collected": _to_float(stats.get("SAVINGS_COLLECTED")),
                "monthly_production": monthly,
                "performance_vs_last_year": _performance_pct(monthly, monthly_prev),
                "encours_evolution": encours_by_agency.get(code, [0.0] * 12),
            }
        )

    enriched.sort(key=lambda x: x.get("total_outstanding", 0), reverse=True)
    for rank, agency in enumerate(enriched, start=1):
        agency["ranking"] = rank
        outstanding = agency.get("total_outstanding", 0)
        agency["score"] = round(min(100.0, outstanding / 100_000_000), 1) if outstanding else 0.0

    return enriched


def get_zone_kpis(
    zone: Dict[str, Any],
    agencies_kpis: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Agrège les KPI agence Oracle pour une zone."""
    zone_codes = {str(a.get("code", "")).strip() for a in zone.get("agencies", [])}
    zone_agencies = [a for a in agencies_kpis if a.get("branch_code") in zone_codes]

    if not zone_agencies:
        return {
            "id": zone.get("id"),
            "name": zone.get("name"),
            "active_clients": 0,
            "active_credits": 0,
            "total_outstanding": 0.0,
            "savings_collected": 0.0,
            "agency_count": len(zone.get("agencies", [])),
            "top_agency": "",
            "flop_agency": "",
            "encours_evolution": [0.0] * 12,
            "agency_rankings": [],
        }

    sorted_agencies = sorted(
        zone_agencies,
        key=lambda x: x.get("total_outstanding", 0),
        reverse=True,
    )
    encours_sum = [0.0] * 12
    for agency in zone_agencies:
        evo = agency.get("encours_evolution") or []
        for i, val in enumerate(evo[-12:]):
            encours_sum[i] += _to_float(val)

    return {
        "id": zone.get("id"),
        "name": zone.get("name"),
        "active_clients": sum(a.get("active_clients", 0) for a in zone_agencies),
        "active_credits": sum(a.get("active_credits", 0) for a in zone_agencies),
        "total_outstanding": sum(a.get("total_outstanding", 0) for a in zone_agencies),
        "savings_collected": sum(a.get("savings_collected", 0) for a in zone_agencies),
        "agency_count": len(zone.get("agencies", [])),
        "top_agency": sorted_agencies[0].get("name", "") if sorted_agencies else "",
        "flop_agency": sorted_agencies[-1].get("name", "") if sorted_agencies else "",
        "encours_evolution": encours_sum,
        "agency_rankings": [
            {
                "agency_name": a.get("name"),
                "score": a.get("score", 0),
                "outstanding": a.get("total_outstanding", 0),
                "rank": a.get("ranking", idx + 1),
            }
            for idx, a in enumerate(sorted_agencies)
        ],
    }

