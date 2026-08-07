"""
Encours / montant dû Vue 360 — charge les SQL depuis requete mobile/vue360/.

Les requêtes vivent dans les fichiers .sql ; ce module ne fait que
les charger et agréger les résultats côté Python.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

_QUERIES_DIR = Path(__file__).resolve().parent.parent / "requete mobile" / "vue360"


@lru_cache(maxsize=8)
def _load_query(filename: str) -> str:
    path = _QUERIES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Requête introuvable : {path}")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^--.*\n", "", text, flags=re.MULTILINE).strip()
    return text.rstrip(";").strip()


ENCOURS_REPARTITION_DETAIL = _load_query("montant_global_du.sql")
ENCOURS_GLOBAL_DETAIL = _load_query("encours_global_caf.sql")


def _to_float(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def aggregate_encours_repartition_rows(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Agrège les lignes détail en totaux client (charges dédupliquées par compte)."""
    if not rows:
        return {}

    def _val(row: Dict[str, Any], *keys: str) -> float:
        for key in keys:
            if key in row and row.get(key) is not None:
                return _to_float(row.get(key))
            upper = key.upper()
            if upper in row and row.get(upper) is not None:
                return _to_float(row.get(upper))
            lower = key.lower()
            if lower in row and row.get(lower) is not None:
                return _to_float(row.get(lower))
        return 0.0

    capital = interest = penalty = total_exigible = 0.0
    charges_by_account: dict[str, dict] = {}

    for row in rows:
        capital += _val(row, "CHARGE_DUE_PRINC")
        penalty += _val(row, "CHARGE_DUE_PEN")
        interest += _val(row, "CHARGE_DUE_INT")
        total_exigible += _val(row, "EXIGIBLE")

        account = str(
            row.get("NUMERO_COMPTE")
            or row.get("numero_compte")
            or ""
        ).strip()
        if account and account not in charges_by_account:
            charges_by_account[account] = row

    ftc = acs_ouv = acs_an = fr_ouv = carte = total_charge = 0.0
    for row in charges_by_account.values():
        acs_ouv += _val(row, "CHARGE_DUE_ACS_OUV")
        acs_an += _val(row, "CHARGE_DUE_ACS_AN")
        fr_ouv += _val(row, "CHARGE_DUE_FR_OUV")
        carte += _val(row, "CHARGE_DUE_CARTE")
        ftc += _val(row, "CHARGE_DUE_FTC")
        total_charge += _val(row, "TOTAL_CHARGE")

    # Total = somme des postes affichés (source de vérité pour le widget)
    components_total = round(
        capital + interest + penalty + ftc + (acs_ouv + acs_an) + fr_ouv + carte, 2
    )
    return {
        "capital_due": round(capital, 2),
        "interest_due": round(interest, 2),
        "penalty_due": round(penalty, 2),
        "ftc_due": round(ftc, 2),
        "acs_due": round(acs_ouv + acs_an, 2),
        "acs_ouv_due": round(acs_ouv, 2),
        "acs_an_due": round(acs_an, 2),
        "opening_fee_due": round(fr_ouv, 2),
        "coficarte_fee_due": round(carte, 2),
        "total_exigible": round(total_exigible, 2),
        "total_charge": round(total_charge, 2),
        "total_due_amount": components_total,
    }


def aggregate_encours_global_rows(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Agrège l'encours global client.
    Les charges compte (FTC/ACS/…) sont dédupliquées par DR_PROD_AC
    pour éviter le double comptage multi-prêts.
    """
    if not rows:
        return {
            "encours_total": 0.0,
            "charge_pret_due": 0.0,
            "charge_due": 0.0,
            "encours_global": 0.0,
        }

    encours_total = 0.0
    charge_pret = 0.0
    charges_by_account: dict[str, float] = {}

    for row in rows:
        encours_total += _to_float(row.get("ENCOURS_TOTAL"))
        charge_pret += _to_float(row.get("CHARGE_PRET_DUE"))
        dr_ac = str(row.get("DR_PROD_AC") or "").strip()
        if dr_ac and dr_ac not in charges_by_account:
            charges_by_account[dr_ac] = _to_float(row.get("CHARGE_DUE"))

    charge_due = sum(charges_by_account.values())
    return {
        "encours_total": round(encours_total, 2),
        "charge_pret_due": round(charge_pret, 2),
        "charge_due": round(charge_due, 2),
        "encours_global": round(encours_total + charge_pret + charge_due, 2),
    }
