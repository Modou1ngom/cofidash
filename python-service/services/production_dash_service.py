"""
Données production (nombre / volume) et évolution encours crédit (PTF) depuis les tables DASH_* (Cofina),
avec le même filtre MIGRATION_DATE_MINUS1 que Volume DAT (jour / mois / semaine / année).
"""
import logging
from datetime import date as dt_date
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from database.oracle_pool import get_pool, get_pool_flexcube
from services.cache_service import TTL_DASHBOARD, get_cache, set_cache
from services.volume_dat_service import _ref_month_year, _week_range_dd_mm_yyyy

_PY_ROOT = Path(__file__).resolve().parent.parent
_PRODUCTION_SQL_PATH = _PY_ROOT / "requete mobile" / "production" / "production.sql"
_PRODUCTION_CALL_TIMEOUT_MS = 240_000

logger = logging.getLogger(__name__)


def _fetch_dash_rows(sql: str, binds: dict) -> list[dict]:
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, binds)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            cur.close()

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


def fetch_dash_production_nombre_rows_for_month(
    month: int,
    year: int,
) -> list[dict]:
    """Snapshot production nombre pour un mois calendaire (sans bascule jour/M-1)."""
    binds = {"month_year": f"{int(month):02d}/{int(year)}"}
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
    WHERE {_SQL_INNER_MONTH}
)
ORDER BY CODE_AGENCE, AGENCE, CHARGE_AFFAIRE
"""
    rows = _fetch_dash_rows(sql, binds)
    logger.info(
        "📊 DASH_PRODUCTION_NOMBRE month=%02d/%d lignes=%s",
        month,
        year,
        len(rows),
    )
    return rows


def fetch_dash_production_volume_rows_for_month(
    month: int,
    year: int,
) -> list[dict]:
    """Snapshot production volume pour un mois calendaire (sans bascule jour/M-1)."""
    binds = {"month_year": f"{int(month):02d}/{int(year)}"}
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
    WHERE {_SQL_INNER_MONTH}
)
ORDER BY CODE_AGENCE, AGENCE, CHARGE_AFFAIRE
"""
    rows = _fetch_dash_rows(sql, binds)
    logger.info(
        "📊 DASH_PRODUCTION_VOLUME month=%02d/%d lignes=%s",
        month,
        year,
        len(rows),
    )
    return rows


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
    rows = _fetch_dash_rows(sql, binds)
    logger.info(
        "📊 DASH_PRODUCTION_NOMBRE mode=%s lignes=%s",
        mode,
        len(rows),
    )
    return rows


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
    rows = _fetch_dash_rows(sql, binds)
    logger.info(
        "📊 DASH_PRODUCTION_VOLUME mode=%s lignes=%s",
        mode,
        len(rows),
    )
    return rows


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
    frais_m = float(out.get("FRAIS_DOSSIER_M") or 0)
    frais_m1 = float(out.get("FRAIS_DOSSIER_M_1") or 0)
    out["FRAIS_DOSSIER_M"] = frais_m
    out["FRAIS_DOSSIER_M_1"] = frais_m1
    out["ECART_FRAIS"] = frais_m - frais_m1
    out["VARIATION_FRAIS"] = frais_m - frais_m1
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
    rows = _fetch_dash_rows(sql, binds)
    logger.info(
        "📊 DASH_EVOLUTION_ENCOURS mode=%s lignes=%s",
        mode,
        len(rows),
    )
    return rows


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


def _load_production_query() -> str:
    if not _PRODUCTION_SQL_PATH.is_file():
        raise FileNotFoundError(f"Requête introuvable : {_PRODUCTION_SQL_PATH}")
    return _PRODUCTION_SQL_PATH.read_text(encoding="utf-8").strip().rstrip(";").strip()


def _pick_col(row: dict, *names: str) -> Any:
    index = {str(key).strip().upper(): value for key, value in row.items()}
    for name in names:
        value = index.get(str(name).strip().upper())
        if value is not None:
            return value
    return None


def _as_date(value: Any) -> Optional[dt_date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, dt_date):
        return value
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            return dt_date.fromisoformat(text[:10])
        except ValueError:
            return None
    if len(text) >= 10 and text[2] == "/" and text[5] == "/":
        try:
            return datetime.strptime(text[:10], "%d/%m/%Y").date()
        except ValueError:
            return None
    return None


def _in_range(value: Optional[dt_date], start: dt_date, end: dt_date) -> bool:
    return value is not None and start <= value <= end


def fetch_flexcube_production_detail(
    range_start: dt_date,
    range_end: dt_date,
) -> list[dict]:
    """Exécute production.sql sur Flexcube. Dates inclusives, format YYYY-MM-DD."""
    m_start = range_start.isoformat()
    m_end = range_end.isoformat()
    cache_key = f"prod-flexcube:{m_start}:{m_end}"
    cached = get_cache(cache_key)
    if cached is not None:
        logger.info("⚡ production Flexcube cache hit %s → %s (%s)", m_start, m_end, len(cached))
        return cached

    pool = get_pool_flexcube()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if hasattr(cursor, "callTimeout"):
                cursor.callTimeout = _PRODUCTION_CALL_TIMEOUT_MS
            cursor.execute(
                _load_production_query(),
                {"m_start": m_start, "m_end": m_end},
            )
            columns = [str(col[0]) for col in cursor.description]
            rows = [dict(zip(columns, raw)) for raw in cursor.fetchall()]
        finally:
            cursor.close()

    logger.info("📊 production Flexcube %s → %s : %s lignes", m_start, m_end, len(rows))
    set_cache(cache_key, rows, TTL_DASHBOARD)
    return rows


def _bucket_production_rows(
    rows: list[dict],
    m_debut: dt_date,
    m_fin: dt_date,
    m1_debut: dt_date,
    m1_fin: dt_date,
) -> dict[tuple[str, str], dict]:
    buckets: dict[tuple[str, str], dict] = {}
    for row in rows:
        trn_dt = _as_date(_pick_col(row, "DATE_DEBLOCAGE"))
        in_m = _in_range(trn_dt, m_debut, m_fin)
        in_m1 = _in_range(trn_dt, m1_debut, m1_fin)
        if not in_m and not in_m1:
            continue
        code = str(_pick_col(row, "CODE AGENCE") or "").strip()
        if not code:
            continue
        caf_code = str(_pick_col(row, "CODE_GESTION_PRET") or "").strip() or "-"
        key = (code, caf_code)
        bucket = buckets.get(key)
        if bucket is None:
            charge = str(_pick_col(row, "CHARGE_D'AFFAIRE", "CHARGE_AFFAIRE") or "").strip() or "-"
            bucket = {
                "CODE_AGENCE": code,
                "AGENCE": str(_pick_col(row, "NOM AGENCE") or "").strip(),
                "CHARGE_AFFAIRE": charge,
                "FIELD_CHAR_2": caf_code,
                "CODE_GESTION_PRET": caf_code,
                "NB_CRED_DECAISSES_M": 0.0,
                "NB_CRED_DECAISSES_M_1": 0.0,
                "VOLUME_DEBLOQUE_M": 0.0,
                "VOLUME_DEBLOQUE_M_1": 0.0,
                "FRAIS_DOSSIER_M": 0.0,
                "FRAIS_DOSSIER_M_1": 0.0,
                "OBJECTIF_PRODUCTION": 0.0,
            }
            buckets[key] = bucket
        amount = float(_pick_col(row, "MONTANT CAPITAL ACCORDE") or 0)
        frais = float(_pick_col(row, "FRAIS_DOSSIER") or 0)
        if in_m:
            bucket["NB_CRED_DECAISSES_M"] += 1
            bucket["VOLUME_DEBLOQUE_M"] += amount
            bucket["FRAIS_DOSSIER_M"] += frais
        if in_m1:
            bucket["NB_CRED_DECAISSES_M_1"] += 1
            bucket["VOLUME_DEBLOQUE_M_1"] += amount
            bucket["FRAIS_DOSSIER_M_1"] += frais
    return buckets


def fetch_flexcube_production_nombre_rows(
    m_debut: dt_date,
    m_fin: dt_date,
    m1_debut: dt_date,
    m1_fin: dt_date,
) -> list[dict]:
    rows = fetch_flexcube_production_detail(m1_debut, m_fin)
    return list(_bucket_production_rows(rows, m_debut, m_fin, m1_debut, m1_fin).values())


def fetch_flexcube_production_volume_rows(
    m_debut: dt_date,
    m_fin: dt_date,
    m1_debut: dt_date,
    m1_fin: dt_date,
) -> list[dict]:
    rows = fetch_flexcube_production_detail(m1_debut, m_fin)
    return list(_bucket_production_rows(rows, m_debut, m_fin, m1_debut, m1_fin).values())


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
