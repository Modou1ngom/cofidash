"""
Sauvegarde du suivi de production : exécute suivi_production.sql sur Flexcube
et matérialise le résultat dans la base SQLite de l'application (database/database.sqlite),
une photo par année.

La requête n'est pas réécrite. Seules les bornes :m_start et :m_end changent,
une année à la fois, sur les trois dernières années.
"""
from __future__ import annotations

import logging
import re
import sqlite3
import threading
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from database.oracle_pool import get_pool_flexcube

logger = logging.getLogger(__name__)

HISTORY_YEARS = 3
_PY_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PY_ROOT.parent
SQL_PATH = _PY_ROOT / "requete mobile" / "production" / "suivi_production.sql"
WORKSPACE_DB_PATH = _PROJECT_ROOT / "database" / "database.sqlite"
_LEGACY_DB_PATH = _PY_ROOT / "data" / "suivi_production_local.db"
_CALL_TIMEOUT_MS = 3_600_000  # 1 h par année

_refresh_lock = threading.Lock()

# Nom Oracle normalisé → colonnes SQLite, dans l'ordre d'apparition
# (p.* puis u.* : TYPE_PRET, CPT_DEPOT_GARANTIE et le dépôt initial sont en double).
_COLUMN_SLOTS: Dict[str, Tuple[str, ...]] = {
    "CODE_AGENCE": ("code_agence",),
    "NOM_AGENCE": ("nom_agence",),
    "NO_PRET": ("no_pret",),
    "MATRICULE_CLIENT": ("matricule_client",),
    "NOM_CLIENT": ("nom_client",),
    "COMPTE": ("compte",),
    "TYPE_PRET": ("type_pret_gl", "type_pret"),
    "DATE_MISE_EN_PLACE": ("date_mise_en_place",),
    "DATE_VAL_MISE_EN_PLACE": ("date_val_mise_en_place",),
    "DATE_DEBLOCAGE": ("date_deblocage",),
    "DATE_MATURITE": ("date_maturite",),
    "DATE_PREMIERE_ECHEANCE": ("date_premiere_echeance",),
    "DATE_DERNIERE_ECHEANCE": ("date_derniere_echeance",),
    "MONTANT_CAPITAL_ACCORDE": ("montant_capital_accorde",),
    "STATUT_PRET": ("statut_pret",),
    "PERIODICITE": ("periodicite",),
    "CPT_DEPOT_GARANTIE": ("cpt_depot_garantie", "udf_cpt_depot_garantie"),
    "MONTANT_DEPOT_GARANTIE_INITIAL": (
        "montant_depot_garantie_initial",
        "udf_montant_depot_garantie_initial",
    ),
    "SOLDE_DEPOT_GARANTIE": ("solde_depot_garantie",),
    "FRAIS_DOSSIER": ("frais_dossier",),
    "FRAIS_ASSURANCE": ("frais_assurance",),
    "TAUX_DE_CREDIT": ("taux_de_credit",),
    "CODE_GESTION_PRET": ("code_gestion_pret",),
    "CHARGE_D_AFFAIRE": ("charge_affaire",),
    "ENCOURS_TOTAL": ("encours_total",),
    "ENCOURS_SAIN": ("encours_sain",),
    "ENCOURS_IMPAYE": ("encours_impaye",),
    "POURCENTAGE_REMBOURSEMENT": ("pourcentage_remboursement",),
    "MAKER_ID": ("maker_id",),
    "ACCOUNT_NUMBER": ("account_number",),
    "CODE_TYPE_PRODUIT": ("code_type_produit",),
    "TYPE_PRODUIT": ("type_produit",),
    "REF_CREDIT_RESTRUCTURE": ("ref_credit_restructure",),
    "FAMILLE_TYPE_CREDIT": ("famille_type_credit",),
    "FAMILLE_CREDIT": ("famille_credit",),
    "CODE_SOUS_FAMILLE_CREDIT": ("code_sous_famille_credit",),
    "SOUS_FAMILLE_CREDIT": ("sous_famille_credit",),
    "CODE_SECTEUR_ACTIVITE": ("code_secteur_activite",),
    "SECTEUR_ACTIVITE": ("secteur_activite",),
    "CODE_SOUS_SECTEUR": ("code_sous_secteur",),
    "SOUS_SECTEUR": ("sous_secteur",),
    "REFERENCE_COMITE": ("reference_comite",),
    "CODE_NATURE_CREDIT": ("code_nature_credit",),
    "NATURE_CREDIT": ("nature_credit",),
    "NAME_NUMERO_DE_CONTRAT": ("name_numero_de_contrat",),
    "ID_PROTOCOLES": ("id_protocoles",),
    "REBOOKE": ("rebooke",),
    "CODE_REF_CREDIT_RESTRUCTURE": ("code_ref_credit_restructure",),
    "NO_CONTRAT_RESTRUCTURE": ("no_contrat_restructure",),
    "CODE_BLOC": ("code_bloc",),
    "BLOC": ("bloc",),
    "CODE_CAMPAGNE": ("code_campagne",),
    "CAMPAGNE": ("campagne",),
    "CODE_RECOUVREUR": ("code_recouvreur",),
    "NAME_RECOUVREUR": ("name_recouvreur",),
    "ID_LIGNE_FINANCEMENT": ("id_ligne_financement",),
    "NUMERO_CREDIT_FLOW": ("numero_credit_flow",),
    "COMPTE_PEP": ("compte_pep",),
    "MONTANT_PEP": ("montant_pep",),
}

ROW_COLUMNS: Tuple[str, ...] = tuple(
    column for slots in _COLUMN_SLOTS.values() for column in slots
)

_SQLITE_DDL = f"""
CREATE TABLE IF NOT EXISTS suivi_production (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annee INTEGER NOT NULL,
    {", ".join(f"{column} TEXT" for column in ROW_COLUMNS)}
);

CREATE INDEX IF NOT EXISTS idx_suivi_production_annee
    ON suivi_production(annee);

CREATE INDEX IF NOT EXISTS idx_suivi_production_date
    ON suivi_production(annee, date_deblocage);

CREATE INDEX IF NOT EXISTS idx_suivi_production_pret
    ON suivi_production(no_pret);

CREATE INDEX IF NOT EXISTS idx_suivi_production_agence
    ON suivi_production(annee, code_agence);

CREATE TABLE IF NOT EXISTS suivi_production_meta (
    annee INTEGER PRIMARY KEY,
    date_debut TEXT,
    date_fin TEXT,
    refreshed_at TEXT,
    row_count INTEGER,
    status TEXT,
    error_message TEXT,
    elapsed_seconds REAL
);
"""


def history_years(today: Optional[date] = None) -> List[int]:
    """Les trois dernières années civiles, de la plus ancienne à l'année en cours."""
    today = today or date.today()
    start = today.year - (HISTORY_YEARS - 1)
    return list(range(start, today.year + 1))


def year_window(year: int, today: Optional[date] = None) -> Tuple[date, date]:
    today = today or date.today()
    year = int(year)
    if year < today.year - (HISTORY_YEARS - 1) or year > today.year:
        raise ValueError(
            f"Année hors fenêtre ({history_years(today)[0]}–{today.year}) : {year}"
        )
    start = date(year, 1, 1)
    end = date(year, 12, 31) if year < today.year else today
    return start, end


def _oracle_key(name: str) -> str:
    text = str(name or "").upper().replace("'", "")
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")


def _load_sql() -> str:
    if not SQL_PATH.is_file():
        raise FileNotFoundError(f"Requête introuvable : {SQL_PATH}")
    return SQL_PATH.read_text(encoding="utf-8").strip().rstrip(";").strip()


def _serialize_cell(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float):
        return format(value, "f")
    return str(value)


def _normalize_row(columns: Sequence[str], raw: tuple, year: int) -> Tuple:
    seen: Dict[str, int] = {}
    values = {column: None for column in ROW_COLUMNS}
    for name, cell in zip(columns, raw):
        key = _oracle_key(name)
        slots = _COLUMN_SLOTS.get(key)
        if not slots:
            continue
        index = seen.get(key, 0)
        seen[key] = index + 1
        if index >= len(slots):
            continue
        values[slots[index]] = _serialize_cell(cell)
    return (year, *(values[column] for column in ROW_COLUMNS))


def _env_database_path() -> Optional[Path]:
    """Chemin SQLite déclaré dans le .env Laravel, s'il diffère du fichier du projet."""
    env_file = _PROJECT_ROOT / ".env"
    if not env_file.is_file():
        return None
    connection = ""
    database = ""
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("DB_CONNECTION="):
            connection = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("DB_DATABASE="):
            database = stripped.split("=", 1)[1].strip().strip('"').strip("'")
    if connection != "sqlite" or not database:
        return None
    path = Path(database)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    return path


def database_paths() -> List[Path]:
    """
    Bases où la table doit apparaître : le fichier du projet ouvert dans l'éditeur,
    puis celui configuré dans .env s'il s'agit d'un autre fichier.
    """
    found: List[Path] = []
    seen = set()
    for candidate in (WORKSPACE_DB_PATH, _env_database_path()):
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        if not candidate.is_file() and candidate != WORKSPACE_DB_PATH:
            continue
        seen.add(resolved)
        found.append(candidate)
    return found or [WORKSPACE_DB_PATH]


def _connect(path: Optional[Path] = None) -> sqlite3.Connection:
    target = path or database_paths()[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _import_legacy(conn: sqlite3.Connection) -> None:
    if not _LEGACY_DB_PATH.is_file():
        return
    existing = conn.execute("SELECT COUNT(*) FROM suivi_production").fetchone()[0]
    if existing:
        return
    legacy_count = 0
    probe = sqlite3.connect(str(_LEGACY_DB_PATH))
    try:
        probe.execute("SELECT 1 FROM suivi_production LIMIT 1")
        legacy_count = probe.execute("SELECT COUNT(*) FROM suivi_production").fetchone()[0]
        legacy_meta = probe.execute("SELECT COUNT(*) FROM suivi_production_meta").fetchone()[0]
    except sqlite3.Error:
        return
    finally:
        probe.close()
    if not legacy_count and not legacy_meta:
        return
    conn.execute("ATTACH DATABASE ? AS legacy", (str(_LEGACY_DB_PATH),))
    columns = "annee, " + ", ".join(ROW_COLUMNS)
    conn.execute(
        f"INSERT INTO suivi_production ({columns}) "
        f"SELECT {columns} FROM legacy.suivi_production"
    )
    conn.execute(
        """
        INSERT INTO suivi_production_meta (
            annee, date_debut, date_fin, refreshed_at, row_count,
            status, error_message, elapsed_seconds
        )
        SELECT annee, date_debut, date_fin, refreshed_at, row_count,
               status, error_message, elapsed_seconds
        FROM legacy.suivi_production_meta
        """
    )
    conn.commit()
    conn.execute("DETACH DATABASE legacy")
    logger.info(
        "Suivi production : %s lignes reprises depuis %s",
        legacy_count,
        _LEGACY_DB_PATH,
    )


def init_suivi_production_local_db() -> None:
    for path in database_paths():
        with _connect(path) as conn:
            conn.executescript(_SQLITE_DDL)
            _import_legacy(conn)
            conn.commit()


def _set_meta(
    conn: sqlite3.Connection,
    *,
    year: int,
    status: str,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    row_count: int = 0,
    error_message: Optional[str] = None,
    elapsed_seconds: Optional[float] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO suivi_production_meta (
            annee, date_debut, date_fin, refreshed_at, row_count,
            status, error_message, elapsed_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(annee) DO UPDATE SET
            date_debut = COALESCE(excluded.date_debut, suivi_production_meta.date_debut),
            date_fin = COALESCE(excluded.date_fin, suivi_production_meta.date_fin),
            refreshed_at = excluded.refreshed_at,
            row_count = excluded.row_count,
            status = excluded.status,
            error_message = excluded.error_message,
            elapsed_seconds = excluded.elapsed_seconds
        """,
        (
            int(year),
            date_debut,
            date_fin,
            datetime.now().isoformat(timespec="seconds"),
            row_count,
            status,
            error_message,
            elapsed_seconds,
        ),
    )


def get_suivi_snapshot_meta(year: Optional[int] = None) -> Any:
    init_suivi_production_local_db()
    with _connect() as conn:
        if year is None:
            rows = conn.execute(
                """
                SELECT annee, date_debut, date_fin, refreshed_at, row_count,
                       status, error_message, elapsed_seconds
                FROM suivi_production_meta
                ORDER BY annee
                """
            ).fetchall()
            return [dict(row) for row in rows]
        row = conn.execute(
            """
            SELECT annee, date_debut, date_fin, refreshed_at, row_count,
                   status, error_message, elapsed_seconds
            FROM suivi_production_meta
            WHERE annee = ?
            """,
            (int(year),),
        ).fetchone()
        return dict(row) if row else None


def has_suivi_snapshot(year: int) -> bool:
    meta = get_suivi_snapshot_meta(int(year))
    return bool(meta and meta.get("status") == "success")


def backup_covers(range_start: date, range_end: date) -> bool:
    """Vrai si chaque année de la période a une sauvegarde exploitable."""
    metas = {
        int(item["annee"]): item
        for item in (get_suivi_snapshot_meta() or [])
    }
    for year in range(range_start.year, range_end.year + 1):
        meta = metas.get(year)
        if not meta or meta.get("status") not in ("success", "running"):
            return False
    return True


def load_suivi_backup_rows(range_start: date, range_end: date) -> Optional[List[dict]]:
    """
    Lignes de la sauvegarde, avec les noms de colonnes de la requête.
    None si une année de la période n'est pas encore sauvegardée.
    """
    if not backup_covers(range_start, range_end):
        return None
    init_suivi_production_local_db()
    with _connect() as conn:
        found = conn.execute(
            """
            SELECT
                date_deblocage,
                code_agence,
                nom_agence,
                no_pret,
                secteur_activite,
                famille_credit,
                code_ref_credit_restructure,
                id_protocoles,
                rebooke,
                montant_capital_accorde,
                code_gestion_pret,
                charge_affaire
            FROM suivi_production
            WHERE substr(COALESCE(date_deblocage, ''), 1, 10) >= ?
              AND substr(COALESCE(date_deblocage, ''), 1, 10) <= ?
            """,
            (range_start.isoformat(), range_end.isoformat()),
        ).fetchall()
    return [
        {
            "DATE_DEBLOCAGE": row["date_deblocage"],
            "CODE AGENCE": row["code_agence"],
            "NOM AGENCE": row["nom_agence"],
            "NO_PRET": row["no_pret"],
            "SECTEUR_ACTIVITE": row["secteur_activite"],
            "FAMILLE_CREDIT": row["famille_credit"],
            "CODE_REF_CREDIT_RESTRUCTURE": row["code_ref_credit_restructure"],
            "ID_PROTOCOLES": row["id_protocoles"],
            "REBOOKE": row["rebooke"],
            "MONTANT CAPITAL ACCORDE": row["montant_capital_accorde"],
            "CODE_GESTION_PRET": row["code_gestion_pret"],
            "CHARGE_D'AFFAIRE": row["charge_affaire"],
        }
        for row in found
    ]


def years_pending(today: Optional[date] = None) -> List[int]:
    """Années sans photo réussie datée d'aujourd'hui."""
    today = today or date.today()
    pending: List[int] = []
    for year in history_years(today):
        meta = get_suivi_snapshot_meta(year)
        refreshed = str((meta or {}).get("refreshed_at") or "")[:10]
        if not meta or meta.get("status") != "success" or refreshed != today.isoformat():
            pending.append(year)
    return pending


def _refresh_year(year: int) -> Dict[str, Any]:
    today = date.today()
    start, end = year_window(year, today)
    init_suivi_production_local_db()
    started = time.monotonic()
    for path in database_paths():
        with _connect(path) as local:
            _set_meta(
                local,
                year=year,
                status="running",
                date_debut=start.isoformat(),
                date_fin=end.isoformat(),
            )
            local.commit()

    logger.info(
        "Suivi production : sauvegarde %s (%s → %s)",
        year,
        start.isoformat(),
        end.isoformat(),
    )
    pool = get_pool_flexcube()
    try:
        with pool.get_connection_context() as ora_conn:
            if hasattr(ora_conn, "callTimeout"):
                ora_conn.callTimeout = _CALL_TIMEOUT_MS
            cursor = ora_conn.cursor()
            try:
                if hasattr(cursor, "callTimeout"):
                    cursor.callTimeout = _CALL_TIMEOUT_MS
                cursor.arraysize = 1000
                cursor.execute(
                    _load_sql(),
                    {"m_start": start.isoformat(), "m_end": end.isoformat()},
                )
                columns = [str(col[0]) for col in cursor.description]
                fetched: List[Tuple] = []
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    fetched.extend(_normalize_row(columns, row, year) for row in batch)
            finally:
                cursor.close()

        placeholders = ", ".join(["?"] * (1 + len(ROW_COLUMNS)))
        insert_sql = (
            f"INSERT INTO suivi_production (annee, {', '.join(ROW_COLUMNS)}) "
            f"VALUES ({placeholders})"
        )
        elapsed = round(time.monotonic() - started, 1)
        stored = [str(path) for path in database_paths()]
        for path in database_paths():
            with _connect(path) as local:
                local.execute("BEGIN")
                local.execute("DELETE FROM suivi_production WHERE annee = ?", (year,))
                local.executemany(insert_sql, fetched)
                _set_meta(
                    local,
                    year=year,
                    status="success",
                    date_debut=start.isoformat(),
                    date_fin=end.isoformat(),
                    row_count=len(fetched),
                    elapsed_seconds=elapsed,
                )
                local.commit()
        logger.info(
            "Suivi production %s : %s lignes en %.1fs → %s",
            year,
            len(fetched),
            elapsed,
            ", ".join(stored),
        )
        return {
            "status": "success",
            "annee": year,
            "date_debut": start.isoformat(),
            "date_fin": end.isoformat(),
            "row_count": len(fetched),
            "elapsed_seconds": elapsed,
            "path": stored,
        }
    except Exception as exc:
        elapsed = round(time.monotonic() - started, 1)
        logger.error("Sauvegarde suivi production %s échouée: %s", year, exc, exc_info=True)
        try:
            for path in database_paths():
                with _connect(path) as local:
                    _set_meta(
                        local,
                        year=year,
                        status="error",
                        date_debut=start.isoformat(),
                        date_fin=end.isoformat(),
                        error_message=str(exc),
                        elapsed_seconds=elapsed,
                    )
                    local.commit()
        except Exception:
            logger.exception("Impossible d'enregistrer l'échec suivi production %s", year)
        raise


def refresh_suivi_production_year(year: int) -> Dict[str, Any]:
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "already_running", "annee": int(year)}
    try:
        return _refresh_year(int(year))
    finally:
        _refresh_lock.release()


def refresh_suivi_production_history(years: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """Rejoue la requête pour chaque année demandée (par défaut les trois dernières)."""
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "already_running"}
    chosen = [int(year) for year in (years if years is not None else history_years())]
    results: List[Dict[str, Any]] = []
    try:
        for year in chosen:
            try:
                results.append(_refresh_year(year))
            except Exception as exc:
                results.append({
                    "status": "error",
                    "annee": year,
                    "error": str(exc),
                })
        failed = [item for item in results if item.get("status") != "success"]
        if failed and len(failed) == len(results):
            status = "error"
        elif failed:
            status = "partial"
        else:
            status = "success"
        return {
            "status": status,
            "years": results,
            "path": [str(path) for path in database_paths()],
        }
    finally:
        _refresh_lock.release()


def refresh_suivi_production_pending() -> Dict[str, Any]:
    pending = years_pending()
    if not pending:
        return {"status": "success", "years": [], "reason": "already_fresh"}
    return refresh_suivi_production_history(pending)
