"""
Service pour la gestion des données Volume DAT
"""
import calendar
import logging
from datetime import date as dt_date
from datetime import datetime, timedelta
from typing import Optional

from database.oracle import get_oracle_connection_cofina
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key

logger = logging.getLogger(__name__)


def _snapshot_from_row(row: dict) -> dict:
    """Sérialise les champs migration Oracle pour le JSON (datetime → ISO)."""

    def _safe(val):
        if val is None:
            return None
        if hasattr(val, "isoformat"):
            try:
                return val.isoformat()
            except Exception:
                return str(val)
        return str(val)

    return {
        "migration_date_minus1": _safe(row.get("MIGRATION_DATE_MINUS1")),
        "migration_date": _safe(row.get("MIGRATION_DATE")),
        "migration_datetime": _safe(row.get("MIGRATION_DATETIME")),
    }


def _dedupe_dash_encours_rows(rows: list) -> list:
    """
    La table peut renvoyer plusieurs lignes pour la même agence (même BRANCH_CODE).
    On garde la première occurrence par code agence, sinon par libellé AGENCE normalisé.
    """
    seen = set()
    out = []
    for row in rows:
        bc = row.get("BRANCH_CODE")
        if bc is None:
            bc = row.get("branch_code")
        if bc is not None and str(bc).strip() != "":
            key = ("bc", str(bc).strip())
        else:
            ag = (row.get("AGENCE") or row.get("agence") or "").strip()
            key = ("ag", " ".join(ag.upper().split()))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    if rows and len(out) < len(rows):
        logger.info(
            "ℹ️ Volume DAT: déduplication %s → %s lignes",
            len(rows),
            len(out),
        )
    return out


def _ref_month_year(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> tuple[int, int]:
    """Mois / année correspondant au filtre UI (défaut : mois courant)."""
    today = dt_date.today()
    p = (period or "month").strip().lower()
    if p == "week" and date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            return d.month, d.year
        except (ValueError, TypeError):
            return today.month, today.year
    if p == "year" and year:
        return 1, int(year)
    if month and year:
        return int(month), int(year)
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            return d.month, d.year
        except (ValueError, TypeError):
            return today.month, today.year
    return today.month, today.year


def _monday_sunday_week(containing: dt_date) -> tuple[dt_date, dt_date]:
    """Semaine calendaire lundi → dimanche (containing peut être n’importe quel jour de la semaine)."""
    monday = containing - timedelta(days=containing.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _week_range_dd_mm_yyyy(period: str, date_str: Optional[str]) -> Optional[tuple[str, str]]:
    """
    Si period == 'week', retourne (début, fin) au format DD/MM/YYYY pour la semaine
    de la date choisie (ou de la date du jour si aucune date).
    Sinon None.
    """
    p = (period or "month").strip().lower()
    if p != "week":
        return None
    today_d = dt_date.today()
    if date_str:
        try:
            ref = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            ref = today_d
    else:
        ref = today_d
    monday, sunday = _monday_sunday_week(ref)
    return monday.strftime("%d/%m/%Y"), sunday.strftime("%d/%m/%Y")


def _migration_date_minus1_target(
    period: str,
    month: Optional[int],
    year: Optional[int],
    date_str: Optional[str],
) -> dt_date:
    """
    Ancre calendaire pour la doc / tests : veille si mois affiché = mois en cours,
    sinon dernier jour du mois sélectionné. La requête Oracle pour les mois passés
    utilise plutôt MAX(MIGRATION_DATE_MINUS1) dans le mois (voir requêtes SQL).
    """
    today = dt_date.today()
    ref_month, ref_year = _ref_month_year(period, month, year, date_str)

    if ref_year == today.year and ref_month == today.month:
        return today - timedelta(days=1)

    last_d = calendar.monthrange(ref_year, ref_month)[1]
    return dt_date(ref_year, ref_month, last_d)


# Mois en cours : une seule date (veille / J−1).
_SQL_VOLUME_DAT_BY_DAY = """
SELECT
    BRANCH_CODE,
    AGENCE,
    DAT_M_1,
    DAT_M,
    VARIATION_VOLUME_DA,
    DETTES_RATTACHEES_DAT_M,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENCOURS_DAT
WHERE TO_CHAR(MIGRATION_DATE_MINUS1, 'DD/MM/YYYY') = :migration_target
ORDER BY AGENCE
"""

# Autre mois : dernier chargement réellement présent dans le mois (ex. 27/03 et non 31/03).
_SQL_VOLUME_DAT_BY_MONTH = """
SELECT
    BRANCH_CODE,
    AGENCE,
    DAT_M_1,
    DAT_M,
    VARIATION_VOLUME_DA,
    DETTES_RATTACHEES_DAT_M,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENCOURS_DAT
WHERE MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM DASH_ENCOURS_DAT d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
ORDER BY AGENCE
"""

# Année : dernier chargement présent dans cette année civile (le front n’envoie pas month pour period=year).
_SQL_VOLUME_DAT_BY_YEAR = """
SELECT
    BRANCH_CODE,
    AGENCE,
    DAT_M_1,
    DAT_M,
    VARIATION_VOLUME_DA,
    DETTES_RATTACHEES_DAT_M,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENCOURS_DAT
WHERE MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM DASH_ENCOURS_DAT d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'YYYY') = :year_only
)
ORDER BY AGENCE
"""

# Semaine : dernier chargement dont la date tombe dans [lundi, dimanche] de la semaine choisie.
_SQL_VOLUME_DAT_BY_WEEK = """
SELECT
    BRANCH_CODE,
    AGENCE,
    DAT_M_1,
    DAT_M,
    VARIATION_VOLUME_DA,
    DETTES_RATTACHEES_DAT_M,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENCOURS_DAT
WHERE MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM DASH_ENCOURS_DAT d
    WHERE TRUNC(d.MIGRATION_DATE_MINUS1) BETWEEN TO_DATE(:week_start, 'DD/MM/YYYY')
                                            AND TO_DATE(:week_end, 'DD/MM/YYYY')
)
ORDER BY AGENCE
"""


def get_volume_dat_data(period: str = "month", zone: Optional[str] = None, 
                        month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None):
    """
    Récupère les données Volume DAT depuis Oracle (Cofina).

    Filtre sur le lot :

    - **Semaine** : dernier ``MIGRATION_DATE_MINUS1`` dans la semaine lundi–dimanche.
    - **Année** (``period='year'``) : dernier chargement présent dans l’année choisie (YYYY).
    - **Mois en cours** (``period='month'``) : veille (J−1).
    - **Autre mois** : dernier chargement présent dans ce mois calendaire.

    Returns:
        Dictionnaire avec les données Volume DAT organisées par zones
    """
    logger.info(f"🔍 get_volume_dat_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}")
    
    from services.cache_service import get_cache, set_cache

    period = (period or "month").strip().lower()

    today = dt_date.today()
    ref_m, ref_y = _ref_month_year(period, month, year, date)
    viewing_current_month = ref_y == today.year and ref_m == today.month

    week_range = _week_range_dd_mm_yyyy(period, date)

    year_only_str: Optional[str] = None
    if period == "year":
        y = int(year) if year is not None else today.year
        year_only_str = f"{y:04d}"

    if week_range:
        week_start, week_end = week_range
        cache_key = f"volume_dat:migration:week:{week_start}_{week_end}:v8"
        migration_target = None
        month_year = None
    elif year_only_str is not None:
        migration_target = None
        month_year = None
        cache_key = f"volume_dat:migration:year:{year_only_str}:v8"
    elif viewing_current_month:
        migration_target = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        cache_key = f"volume_dat:migration:day:{migration_target}:v8"
        month_year = None
    else:
        migration_target = None
        month_year = f"{ref_m:02d}/{ref_y}"
        cache_key = f"volume_dat:migration:month:{month_year}:v8"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données Volume DAT récupérées depuis le cache")
        return cached_result
    
    conn = get_oracle_connection_cofina()
    try:
        cursor = conn.cursor()
        
        cursor.arraysize = 1000
        cursor.prefetchrows = 1000
        
        try:
            if week_range:
                ws, we = week_range
                logger.info(
                    "🔍 Volume DAT — semaine %s → %s (MAX dans l’intervalle)",
                    ws,
                    we,
                )
                cursor.execute(
                    _SQL_VOLUME_DAT_BY_WEEK,
                    {"week_start": ws, "week_end": we},
                )
            elif year_only_str is not None:
                logger.info(
                    "🔍 Volume DAT — MAX dans l’année YYYY = %s",
                    year_only_str,
                )
                cursor.execute(_SQL_VOLUME_DAT_BY_YEAR, {"year_only": year_only_str})
            elif viewing_current_month:
                logger.info(
                    "🔍 Volume DAT — jour (veille) MIGRATION_DATE_MINUS1 = %s",
                    migration_target,
                )
                cursor.execute(_SQL_VOLUME_DAT_BY_DAY, {"migration_target": migration_target})
            else:
                logger.info(
                    "🔍 Volume DAT — MAX dans le mois MM/YYYY = %s",
                    month_year,
                )
                cursor.execute(_SQL_VOLUME_DAT_BY_MONTH, {"month_year": month_year})
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = _dedupe_dash_encours_rows(data)
            
            logger.info(f"📊 {len(data)} lignes à traiter (après déduplication le cas échéant)")
            
            # Log des premières lignes pour déboguer
            if len(data) > 0:
                sample_row = data[0]
                logger.info(f"🔍 Exemple de données récupérées: BRANCH_CODE={sample_row.get('BRANCH_CODE')}, AGENCE={sample_row.get('AGENCE')}, DETTES_RATTACHEES_DAT_M={sample_row.get('DETTES_RATTACHEES_DAT_M')}")
            
            if len(data) == 0:
                logger.warning("⚠️ Aucune donnée Volume DAT trouvée")
                return {
                    "hierarchicalData": {
                        "TERRITOIRE": {},
                        "POINT SERVICES": {},
                    },
                    "snapshot": None,
                }
            
            # Organiser les données par territoire et point de service
            agencies_by_territory = {
                'territoire_dakar_ville': [],
                'territoire_dakar_banlieue': [],
                'territoire_province_centre_sud': [],
                'territoire_province_nord': []
            }
            
            grand_compte = None
            
            for row in data:
                branch_code = row.get('BRANCH_CODE') or row.get('branch_code')
                agency_name = row.get('AGENCE') or row.get('agence') or ''
                
                dat_m1 = float(row.get('DAT_M_1') or 0)
                dat_m = float(row.get('DAT_M') or 0)
                variation_dat_value = (
                    row.get('VARIATION_DAT%')
                    or row.get('VARIATION_DAT')
                    or row.get('"VARIATION_DAT%"')
                )
                if variation_dat_value is None or variation_dat_value == '':
                    variation_dat_value = round(
                        ((dat_m - dat_m1) / dat_m1 * 100), 2
                    ) if dat_m1 else 0.0
                else:
                    variation_dat_value = float(variation_dat_value)
                agency = {
                    'BRANCH_CODE': branch_code,
                    'AGENCE': agency_name,
                    'name': agency_name,
                    'DAT_M_1': dat_m1,
                    'DAT_M': dat_m,
                    'VARIATION_VOLUME_DA': float(row.get('VARIATION_VOLUME_DA') or 0),
                    'VARIATION_DAT': variation_dat_value,
                    'VARIATION_DAT%': variation_dat_value,
                    'DETTES_RATTACHEES_DAT_M': float(row.get('DETTES_RATTACHEES_DAT_M') or 0),
                    'DETTES_RATTACHEES_DAT': float(row.get('DETTES_RATTACHEES_DAT_M') or 0),
                    'MIGRATION_DATE': row.get('MIGRATION_DATE'),
                    'MIGRATION_DATETIME': row.get('MIGRATION_DATETIME'),
                    'MIGRATION_DATE_MINUS1': row.get('MIGRATION_DATE_MINUS1'),
                }
                
                # Code agence (DASH) puis nom d’agence — évite tout ranger à Dakar si le mapping code est absent
                territory = get_territory_from_branch_code(branch_code)
                if territory is None:
                    territory = get_territory_from_agency(agency_name)

                if agency_name and 'GRAND COMPTE' in agency_name.upper():
                    grand_compte = agency
                    continue

                if territory is None or territory == 'POINT SERVICES':
                    territory_key = 'territoire_dakar_ville'
                else:
                    territory_key = get_territory_key(territory)

                if territory_key in agencies_by_territory:
                    agencies_by_territory[territory_key].append(agency)
            
            # Calculer les totaux pour chaque territoire
            def calculate_territory_totals(agencies_list):
                """Calcule les totaux pour un territoire"""
                totals = {
                    'datM1': 0,
                    'datM': 0,
                    'variationVolumeDa': 0,
                    'variationDat': 0,
                    'dettesRattacheesDat': 0
                }
                for agency in agencies_list:
                    totals['datM1'] += float(agency.get('DAT_M_1', 0) or 0)
                    totals['datM'] += float(agency.get('DAT_M', 0) or 0)
                    totals['variationVolumeDa'] += float(agency.get('VARIATION_VOLUME_DA', 0) or 0)
                    totals['variationDat'] += float(agency.get('VARIATION_DAT', 0) or 0)
                    totals['dettesRattacheesDat'] += float(agency.get('DETTES_RATTACHEES_DAT_M', 0) or agency.get('DETTES_RATTACHEES_DAT', 0) or 0)
                return totals
            
            # Construire la structure hiérarchique
            response_data = {
                "hierarchicalData": {
                    "TERRITOIRE": {},
                    "POINT SERVICES": {}
                }
            }
            
            # Ajouter les territoires
            if any(agencies_by_territory.values()):
                response_data["hierarchicalData"]["TERRITOIRE"] = {
                    "territoire_dakar_ville": {
                        "name": "DAKAR CENTRE VILLE",
                        "agencies": agencies_by_territory['territoire_dakar_ville'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_dakar_ville'])
                    },
                    "territoire_dakar_banlieue": {
                        "name": "DAKAR BANLIEUE",
                        "agencies": agencies_by_territory['territoire_dakar_banlieue'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_dakar_banlieue'])
                    },
                    "province_centre_sud": {
                        "name": "PROVINCE CENTRE SUD",
                        "agencies": agencies_by_territory['territoire_province_centre_sud'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_province_centre_sud'])
                    },
                    "province_nord": {
                        "name": "PROVINCE NORD",
                        "agencies": agencies_by_territory['territoire_province_nord'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_province_nord'])
                    }
                }
                
                # Ajouter le grand compte dans TERRITOIRE si présent
                if grand_compte:
                    response_data["hierarchicalData"]["TERRITOIRE"]["grand_compte"] = {
                        "name": "GRAND COMPTE",
                        "agencies": [grand_compte],
                        "totals": {
                            'datM1': grand_compte.get('DAT_M_1', 0),
                            'datM': grand_compte.get('DAT_M', 0),
                            'variationVolumeDa': grand_compte.get('VARIATION_VOLUME_DA', 0),
                            'variationDat': grand_compte.get('VARIATION_DAT', 0),
                            'dettesRattacheesDat': grand_compte.get('DETTES_RATTACHEES_DAT_M', 0) or grand_compte.get('DETTES_RATTACHEES_DAT', 0) or 0
                        }
                    }

            response_data["snapshot"] = _snapshot_from_row(data[0])
            
            # Mettre en cache le résultat (TTL de 5 minutes)
            set_cache(cache_key, response_data, ttl=300)
            
            logger.info(f"✅ Données Volume DAT récupérées: {len(data)} agences")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données Volume DAT: {str(e)}", exc_info=True)
            raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
