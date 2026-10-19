"""
Suivi des échéances de crédit pour un mois.

Le mois choisi borne l'échéance du mois (TA_ECH_M) et l'exigible antérieur
(échéances dues avant le 1er du mois). Le statut I / R / A reste calculé
par rapport à la date du jour, comme dans la requête métier.
"""
import logging
from calendar import monthrange
from datetime import date as dt_date
from pathlib import Path
from typing import Any, Optional

from database.oracle_pool import get_pool_flexcube
from services.cache_service import TTL_DASHBOARD, get_cache, set_cache
from services.production_dash_service import _as_date

logger = logging.getLogger(__name__)

_PY_ROOT = Path(__file__).resolve().parent.parent
_SQL_PATH = _PY_ROOT / "requete mobile" / "production" / "suivi_echeance.sql"
_CALL_TIMEOUT_MS = 300_000

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


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _amount(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _cell(index: dict, *names: str):
    for name in names:
        if name in index:
            return index[name]
    return None


def _normalize_row(raw: dict) -> dict:
    index = {str(key).strip().upper(): value for key, value in raw.items()}
    due = _as_date(_cell(index, "SCHEDULE_DUE_DATE"))
    deblocage = _as_date(_cell(index, "DATE_DEBLOCAGE"))
    numero = _cell(index, "NUMERO_ECHEANCE")
    try:
        numero = int(numero) if numero is not None and numero != "" else None
    except (TypeError, ValueError):
        numero = None
    status = _text(_cell(index, "STATUS_ECH")).upper()
    return {
        "code_agence": _text(_cell(index, "CODE_AGENCE")),
        "nom_agence": _text(_cell(index, "NOM_AGENCE")),
        "no_pret": _text(_cell(index, "NO_PRET")),
        "matricule_client": _text(_cell(index, "MATRICULE_CLIENT")),
        "nom_client": _text(_cell(index, "NOM_CLIENT")),
        "compte": _text(_cell(index, "COMPTE")),
        "type_pret": _text(_cell(index, "TYPE_PRET")),
        "date_deblocage": deblocage.isoformat() if deblocage else None,
        "montant_capital_accorde": _amount(_cell(index, "MONTANT_CAPITAL_ACCORDE")),
        "encours_total": _amount(_cell(index, "ENCOURS_TOTAL")),
        "encours_sain": _amount(_cell(index, "ENCOURS_SAIN")),
        "encours_impaye": _amount(_cell(index, "ENCOURS_IMPAYE")),
        "pourcentage_remboursement": _amount(_cell(index, "POURCENTAGE_REMBOURSEMENT")),
        "statut_pret": _text(_cell(index, "STATUT_PRET")),
        "statut_declassement": _text(_cell(index, "STATUT_DECLASSEMENT")),
        "code_gestion_pret": _text(_cell(index, "CODE_GESTION_PRET")),
        "charge_affaire": _text(_cell(index, "CHARGE_AFFAIRE")),
        "montant_depot_garantie_initial": _amount(_cell(index, "MONTANT_DEPOT_GARANTIE_INITIAL")),
        "solde_depot_garantie": _amount(_cell(index, "SOLDE_DEPOT_GARANTIE")),
        "schedule_due_date": due.isoformat() if due else None,
        "numero_echeance": numero,
        "solde_cpte": _amount(_cell(index, "SOLDE_CPTE")),
        "mt_global_due_a_date": _amount(_cell(index, "MT_GLOBAL_DUE_A_DATE")),
        "etat_exigible_m_1": _amount(_cell(index, "ETAT_EXIGIBLE_M_1")),
        "total_charge": _amount(_cell(index, "TOTAL_CHARGE")),
        "montant_echeance_m": _amount(_cell(index, "MONTANT_ECHEANCE_M")),
        "montant_echeance_paye": _amount(_cell(index, "MONTANT_ECHEANCE_PAYE")),
        "montant_echeance_impy": _amount(_cell(index, "MONTANT_ECHEANCE_IMPY")),
        "penalite": _amount(_cell(index, "PENALITE")),
        "exigible_ech": _amount(_cell(index, "EXIGIBLE_ECH")),
        "status_ech": status or None,
    }


def resolve_month(year: Optional[int], month: Optional[int], today: Optional[dt_date] = None) -> dict:
    today = today or dt_date.today()
    y = int(year or today.year)
    m = int(month or today.month)
    m = min(12, max(1, m))
    start = dt_date(y, m, 1)
    end = dt_date(y, m, monthrange(y, m)[1])
    return {
        "year": y,
        "month": m,
        "start": start,
        "end": end,
        "label": f"{MONTHS[m].capitalize()} {y}",
    }


def fetch_suivi_echeance_rows(start: dt_date, end: dt_date) -> list[dict]:
    cache_key = f"suivi-echeance:v1:{start.isoformat()}:{end.isoformat()}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("suivi échéance cache hit %s → %s (%s)", start, end, len(cached))
        return cached

    logger.info("suivi échéance Flexcube %s → %s", start, end)
    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _CALL_TIMEOUT_MS
            cursor.arraysize = 1000
            cursor.prefetchrows = 1000
            cursor.execute(_load_sql(), {"date_debut": start, "date_fin": end})
            columns = [desc[0] for desc in cursor.description]
            raw_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    rows = [_normalize_row(raw) for raw in raw_rows]
    logger.info("suivi échéance %s → %s : %s lignes", start, end, len(rows))
    set_cache(cache_key, rows, TTL_DASHBOARD)
    return rows


def get_suivi_echeance_data(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Lit la photo journalière la plus récente du mois demandé."""
    from services.suivi_echeance_backup_service import load_suivi_echeance_rows

    window = resolve_month(year, month)
    saved = load_suivi_echeance_rows(window["year"], window["month"])
    rows = saved["rows"] if saved else []
    meta = saved["meta"] if saved else None
    return {
        "period": {
            "year": window["year"],
            "month": window["month"],
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
            "label": window["label"],
        },
        "count": len(rows),
        "source": "sauvegarde" if saved else "sauvegarde absente",
        "snapshot": meta,
        "warning": None if saved else "Aucune sauvegarde pour ce mois. La photo est rafraîchie toutes les 30 minutes.",
        "generated_at": (meta or {}).get("refreshed_at") if meta else None,
        "rows": rows,
    }
