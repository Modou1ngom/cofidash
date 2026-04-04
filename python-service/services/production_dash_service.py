"""
Données production (nombre / volume) et évolution encours crédit (PTF) depuis les tables DASH_* (Cofina),
avec le même filtre MIGRATION_DATE_MINUS1 que Volume DAT (jour / mois / semaine / année).
"""
import logging
from datetime import date as dt_date
from datetime import timedelta
from typing import Any, Optional

from database.oracle import get_oracle_connection_cofina
from services.volume_dat_service import _ref_month_year, _week_range_dd_mm_yyyy

logger = logging.getLogger(__name__)

_SQL_INNER_DAY = "TO_CHAR(d.MIGRATION_DATE_MINUS1, 'DD/MM/YYYY') = :migration_target"
_SQL_INNER_MONTH = "TO_CHAR(d.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year"
_SQL_INNER_WEEK = """TRUNC(d.MIGRATION_DATE_MINUS1) BETWEEN TO_DATE(:week_start, 'DD/MM/YYYY')
                                            AND TO_DATE(:week_end, 'DD/MM/YYYY')"""
_SQL_INNER_YEAR = "TO_CHAR(d.MIGRATION_DATE_MINUS1, 'YYYY') = :year_only"


def _migration_mode_and_binds(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> tuple[str, dict[str, Any]]:
    """Retourne (mode, binds) avec mode dans day|month|week|year."""
    p = (period or "month").strip().lower()
    today = dt_date.today()
    ref_m, ref_y = _ref_month_year(p, month, year, date_str)
    viewing_current_month = ref_y == today.year and ref_m == today.month
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
    if viewing_current_month:
        return "day", {"migration_target": (today - timedelta(days=1)).strftime("%d/%m/%Y")}
    return "month", {"month_year": f"{ref_m:02d}/{ref_y}"}


def _inner_sql_fragment(mode: str) -> str:
    if mode == "week":
        return _SQL_INNER_WEEK
    if mode == "year":
        return _SQL_INNER_YEAR
    if mode == "day":
        return _SQL_INNER_DAY
    return _SQL_INNER_MONTH


def fetch_dash_production_nombre_rows(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> list[dict]:
    mode, binds = _migration_mode_and_binds(period, month, year, date_str)
    inner = _inner_sql_fragment(mode)
    sql = f"""
SELECT
    CODE_AGENCE,
    AGENCE,
    CHARGE_AFFAIRE,
    FIELD_CHAR_2,
    NB_CRED_DECAISSES_M,
    NB_CRED_DECAISSES_M_1,
    VARIATION_POURCENT,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_PRODUCTION_NOMBRE
WHERE MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM DASH_PRODUCTION_NOMBRE d
    WHERE {inner}
)
ORDER BY CODE_AGENCE, AGENCE, CHARGE_AFFAIRE
"""
    conn = get_oracle_connection_cofina()
    try:
        cur = conn.cursor()
        cur.execute(sql, binds)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        logger.info(
            "📊 DASH_PRODUCTION_NOMBRE mode=%s lignes=%s",
            mode,
            len(rows),
        )
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass


def build_production_nombre_charge_details_by_agency(raw_rows: list[dict]) -> dict[str, list[dict]]:
    """Détail par CAF pour le clic sur une agence (même principe que la production volume)."""
    out: dict[str, list[dict]] = {}
    for r in raw_rows:
        code = str(r.get("CODE_AGENCE") if r.get("CODE_AGENCE") is not None else "").strip()
        if not code:
            continue
        m = float(
            r.get("NB_CRED_DECAISSES_M")
            or r.get("NB_DE_CREDITS_DECAISSES_M")
            or r.get("NOMBRE_DE_CREDITS_DECAISSES_M")
            or 0
        )
        m1 = float(
            r.get("NB_CRED_DECAISSES_M_1")
            or r.get("NB_DE_CREDITS_DECAISSES_M_1")
            or r.get("NOMBRE_DE_CREDITS_DECAISSES_M_1")
            or 0
        )
        obj = float(r.get("OBJECTIF_PRODUCTION") or 0)
        var_n = float(r.get("VARIATION_NOMBRE") or (m - m1))
        var_pct = r.get("VARIATION_POURCENT")
        try:
            var_pct_f = float(var_pct) if var_pct is not None else (
                round(((m - m1) / m1) * 100, 2) if m1 else 0.0
            )
        except (TypeError, ValueError):
            var_pct_f = 0.0
        caf = str(r.get("CHARGE_AFFAIRE") or "").strip() or "-"
        cg = str(r.get("FIELD_CHAR_2") or r.get("CODE_GESTION_PRET") or "").strip() or "-"
        detail = {
            "chargeAffaire": caf,
            "CHARGE_AFFAIRE": caf,
            "codeGestion": cg,
            "CODE_GESTION": cg,
            "objectif": obj,
            "nombreDossiersM": m,
            "NOMBRE_DOSSIERS_M": m,
            "nombreDossiersM1": m1,
            "NOMBRE_DOSSIERS_M_1": m1,
            "variationNombre": var_n,
            "VARIATION_NOMBRE": var_n,
            "variationPct": var_pct_f,
            "VARIATION_PCT": var_pct_f,
        }
        out.setdefault(code, []).append(detail)
    return out


def aggregate_nombre_dash_rows_by_agency(rows: list[dict]) -> list[dict]:
    """Une ligne par CODE_AGENCE (somme des effectifs si le DASH est au grain CAF)."""

    def nm_m1(r: dict) -> tuple[float, float]:
        x = (
            r.get("NB_CRED_DECAISSES_M")
            or r.get("NB_DE_CREDITS_DECAISSES_M")
            or r.get("NOMBRE_DE_CREDITS_DECAISSES_M")
            or 0
        )
        y = (
            r.get("NB_CRED_DECAISSES_M_1")
            or r.get("NB_DE_CREDITS_DECAISSES_M_1")
            or r.get("NOMBRE_DE_CREDITS_DECAISSES_M_1")
            or 0
        )
        try:
            return float(x or 0), float(y or 0)
        except (TypeError, ValueError):
            return 0.0, 0.0

    by_code: dict[str, dict] = {}
    for r in rows:
        code = str(r.get("CODE_AGENCE") if r.get("CODE_AGENCE") is not None else "").strip()
        if not code:
            code = "__nocode__"
        nm, nm1 = nm_m1(r)
        obj = float(r.get("OBJECTIF_PRODUCTION") or 0)
        ag = (r.get("AGENCE") or "").strip()
        if code not in by_code:
            base = dict(r)
            base["NB_CRED_DECAISSES_M"] = nm
            base["NB_CRED_DECAISSES_M_1"] = nm1
            base["OBJECTIF_PRODUCTION"] = obj
            by_code[code] = base
        else:
            cur = by_code[code]
            a_nm, a_nm1 = nm_m1(cur)
            cur["NB_CRED_DECAISSES_M"] = a_nm + nm
            cur["NB_CRED_DECAISSES_M_1"] = a_nm1 + nm1
            cur["OBJECTIF_PRODUCTION"] = float(cur.get("OBJECTIF_PRODUCTION") or 0) + obj
            prev_ag = (cur.get("AGENCE") or "").strip()
            if ag and (not prev_ag or len(ag) > len(prev_ag)):
                cur["AGENCE"] = ag
    out = []
    for d in by_code.values():
        nm, nm1 = nm_m1(d)
        obj = float(d.get("OBJECTIF_PRODUCTION") or 0)
        d["NB_CRED_DECAISSES_M"] = nm
        d["NB_CRED_DECAISSES_M_1"] = nm1
        d["VARIATION_NOMBRE"] = nm - nm1
        if nm1:
            d["VARIATION_POURCENT"] = round(((nm - nm1) / nm1) * 100, 2)
        else:
            d["VARIATION_POURCENT"] = 0.0
        if obj:
            d["TAUX_REALISATION"] = round((nm / obj) * 100, 2)
        else:
            d["TAUX_REALISATION"] = 0.0
        for k in ("CHARGE_AFFAIRE", "FIELD_CHAR_2"):
            d.pop(k, None)
        out.append(d)
    return out


def fetch_dash_production_volume_rows(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> list[dict]:
    mode, binds = _migration_mode_and_binds(period, month, year, date_str)
    inner = _inner_sql_fragment(mode)
    sql = f"""
SELECT
    CODE_AGENCE,
    AGENCE,
    CHARGE_AFFAIRE,
    CODE_GESTION_PRET,
    VOLUME_DEBLOQUE_M,
    VOLUME_DEBLOQUE_M_1,
    VARIATION_VOLUME,
    VARIATION_PCT,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_PRODUCTION_VOLUME
WHERE MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM DASH_PRODUCTION_VOLUME d
    WHERE {inner}
)
ORDER BY CODE_AGENCE, AGENCE, CHARGE_AFFAIRE
"""
    conn = get_oracle_connection_cofina()
    try:
        cur = conn.cursor()
        cur.execute(sql, binds)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        logger.info(
            "📊 DASH_PRODUCTION_VOLUME mode=%s lignes=%s",
            mode,
            len(rows),
        )
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass


def normalize_nombre_row_from_dash(row: dict) -> dict:
    """Aligne les noms de colonnes sur le reste de production_service."""
    out = dict(row)

    def pick(*keys):
        for k in keys:
            for cand in (k, k.upper(), k.lower()):
                if cand in out and out[cand] is not None:
                    return out[cand]
        return None

    m = pick(
        "NB_CRED_DECAISSES_M",
        "NB_DE_CREDITS_DECAISSES_M",
        "NOMBRE_DE_CREDITS_DECAISSES_M",
    )
    m1 = pick(
        "NB_CRED_DECAISSES_M_1",
        "NB_DE_CREDITS_DECAISSES_M_1",
        "NOMBRE_DE_CREDITS_DECAISSES_M_1",
    )
    try:
        out["NOMBRE_DE_CREDITS_DECAISSES_M"] = float(m or 0)
        out["NOMBRE_DE_CREDITS_DECAISSES_M_1"] = float(m1 or 0)
    except (TypeError, ValueError):
        out["NOMBRE_DE_CREDITS_DECAISSES_M"] = 0.0
        out["NOMBRE_DE_CREDITS_DECAISSES_M_1"] = 0.0
    if not out.get("AGENCE"):
        out["AGENCE"] = pick("AGENCE", "BRANCH_NAME") or ""
    ca = pick("CODE_AGENCE", "BRANCH_CODE")
    if ca is not None:
        out["CODE_AGENCE"] = ca
    return out


def aggregate_volume_dash_rows_by_agency(rows: list[dict]) -> list[dict]:
    """Une ligne par CODE_AGENCE (somme des volumes si grain CAF dans DASH)."""
    by_code: dict[str, dict] = {}
    for r in rows:
        code = str(r.get("CODE_AGENCE") if r.get("CODE_AGENCE") is not None else "").strip()
        if not code:
            code = "__nocode__"
        vm = float(r.get("VOLUME_DEBLOQUE_M") or 0)
        vm1 = float(r.get("VOLUME_DEBLOQUE_M_1") or 0)
        if code not in by_code:
            base = dict(r)
            base["VOLUME_DEBLOQUE_M"] = vm
            base["VOLUME_DEBLOQUE_M_1"] = vm1
            by_code[code] = base
        else:
            by_code[code]["VOLUME_DEBLOQUE_M"] = float(by_code[code].get("VOLUME_DEBLOQUE_M") or 0) + vm
            by_code[code]["VOLUME_DEBLOQUE_M_1"] = float(by_code[code].get("VOLUME_DEBLOQUE_M_1") or 0) + vm1
    out = []
    for d in by_code.values():
        vm = float(d.get("VOLUME_DEBLOQUE_M") or 0)
        vm1 = float(d.get("VOLUME_DEBLOQUE_M_1") or 0)
        d["VARIATION_VOLUME"] = vm - vm1
        if vm1:
            d["VARIATION_PCT"] = round(((vm - vm1) / vm1) * 100, 2)
        else:
            d["VARIATION_PCT"] = 0.0
        d.pop("CHARGE_AFFAIRE", None)
        d.pop("CODE_GESTION_PRET", None)
        out.append(d)
    return out


def build_production_volume_charge_details_by_agency(raw_rows: list[dict]) -> dict[str, list[dict]]:
    """Lignes CAF volume pour le panneau déplié (clé = CODE_AGENCE en str)."""
    out: dict[str, list[dict]] = {}
    for r in raw_rows:
        code = str(r.get("CODE_AGENCE") if r.get("CODE_AGENCE") is not None else "").strip()
        if not code:
            continue
        vm = float(r.get("VOLUME_DEBLOQUE_M") or 0)
        vm1 = float(r.get("VOLUME_DEBLOQUE_M_1") or 0)
        var_v = float(r.get("VARIATION_VOLUME") or (vm - vm1))
        vpct = r.get("VARIATION_PCT")
        try:
            vpct_f = float(vpct) if vpct is not None else (
                round(((vm - vm1) / vm1) * 100, 2) if vm1 else 0.0
            )
        except (TypeError, ValueError):
            vpct_f = 0.0
        caf = str(r.get("CHARGE_AFFAIRE") or "").strip() or "-"
        cg = str(r.get("CODE_GESTION_PRET") or "").strip() or "-"
        detail = {
            "chargeAffaire": caf,
            "CHARGE_AFFAIRE": caf,
            "codeGestion": cg,
            "CODE_GESTION": cg,
            "volumeDebloqueM": vm,
            "VOLUME_DEBLOQUE_M": vm,
            "volumeDebloqueM1": vm1,
            "VOLUME_DEBLOQUE_M_1": vm1,
            "variationVolume": var_v,
            "VARIATION_VOLUME": var_v,
            "variationPct": vpct_f,
            "VARIATION_PCT": vpct_f,
        }
        out.setdefault(code, []).append(detail)
    return out


def normalize_volume_row_from_dash(row: dict) -> dict:
    out = dict(row)
    vm = out.get("VOLUME_DEBLOQUE_M")
    vm1 = out.get("VOLUME_DEBLOQUE_M_1")
    try:
        out["VOLUME_CREDIT_DECAISSE_M"] = float(vm or 0)
        out["VOLUME_CREDIT_DECAISSE_M_1"] = float(vm1 or 0)
    except (TypeError, ValueError):
        out["VOLUME_CREDIT_DECAISSE_M"] = 0.0
        out["VOLUME_CREDIT_DECAISSE_M_1"] = 0.0
    vpct = out.get("VARIATION_PCT")
    if vpct is None:
        vpct = out.get("VARIATION_POURCENT")
    try:
        out["VARIATION_POURCENT"] = float(vpct or 0)
    except (TypeError, ValueError):
        out["VARIATION_POURCENT"] = 0.0
    try:
        out["VARIATION_VOLUME"] = float(out.get("VARIATION_VOLUME") or 0)
    except (TypeError, ValueError):
        out["VARIATION_VOLUME"] = 0.0
    for fk in ("OBJECTIF_PRODUCTION", "TAUX_REALISATION"):
        if fk not in out or out[fk] is None:
            out[fk] = 0
    out["FRAIS_DOSSIER_M"] = 0
    out["FRAIS_DOSSIER_M_1"] = 0
    out["ECART_FRAIS"] = 0
    out["VARIATION_FRAIS"] = 0
    return out


def fetch_dash_evolution_encours_rows(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> list[dict]:
    """PTF et produit d'intérêt depuis DASH_EVOLUTION_ENCOURS."""
    mode, binds = _migration_mode_and_binds(period, month, year, date_str)
    inner = _inner_sql_fragment(mode)
    sql = f"""
SELECT
    CODE_AGENCE,
    AGENCE,
    PTF_M1,
    PTF_M,
    VARIATION_PTF,
    TAUX_CROISSANCE_PTF,
    PRODUIT_INT_M1,
    PRODUIT_INT_M,
    VARIATION_PRODUIT_INT,
    TAUX_CROISSANCE_PRODUIT_INT,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_EVOLUTION_ENCOURS
WHERE MIGRATION_DATE_MINUS1 = (
    SELECT MAX(MIGRATION_DATE_MINUS1)
    FROM DASH_EVOLUTION_ENCOURS d
    WHERE {inner}
)
ORDER BY CODE_AGENCE, AGENCE
"""
    conn = get_oracle_connection_cofina()
    try:
        cur = conn.cursor()
        cur.execute(sql, binds)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        logger.info(
            "📊 DASH_EVOLUTION_ENCOURS mode=%s lignes=%s",
            mode,
            len(rows),
        )
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass


def normalize_encours_row_from_dash(row: dict) -> dict:
    out = dict(row)
    for k in (
        "PTF_M1",
        "PTF_M",
        "VARIATION_PTF",
        "TAUX_CROISSANCE_PTF",
        "PRODUIT_INT_M1",
        "PRODUIT_INT_M",
        "VARIATION_PRODUIT_INT",
        "TAUX_CROISSANCE_PRODUIT_INT",
    ):
        v = out.get(k)
        if v is None:
            out[k] = 0.0
        else:
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = 0.0
    if not out.get("AGENCE"):
        out["AGENCE"] = ""
    return out


def resolve_production_period(
    period: Optional[str],
    month: Optional[int],
    year: Optional[int],
    date_m_debut: Optional[str],
    date_m_fin: Optional[str],
) -> str:
    """Déduit period (week|month|year) pour le dash si non fourni explicitement."""
    if period and str(period).strip():
        return str(period).strip().lower()
    if month and year:
        return "month"
    if year and not month:
        return "year"
    if date_m_debut and date_m_fin:
        return "month"
    return "month"
