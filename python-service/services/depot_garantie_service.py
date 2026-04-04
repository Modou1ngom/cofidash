"""
Service pour la gestion des données Dépôt de Garantie
"""
import logging
from datetime import date as dt_date
from datetime import timedelta
from typing import Optional

from database.oracle import get_oracle_connection_cofina
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key
from services.volume_dat_service import (
    _dedupe_dash_encours_rows,
    _ref_month_year,
    _snapshot_from_row,
    _week_range_dd_mm_yyyy,
)

logger = logging.getLogger(__name__)

_SQL_DEPOT_GARANTIE_BY_DAY = """
SELECT
    BRANCH_CODE,
    BRANCH_NAME,
    ENCOURS_TOTAL_M,
    M1_ENCOURS_DEPOT_GARANTIE,
    M_ENCOURS_DEPOT_GARANTIE,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_DEPOT_GARANTIE
WHERE MIGRATION_DATE_MINUS1 = (
    SELECT MAX(MIGRATION_DATE_MINUS1)
    FROM DASH_DEPOT_GARANTIE d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'DD/MM/YYYY') = :migration_target
)
ORDER BY BRANCH_CODE, BRANCH_NAME
"""

_SQL_DEPOT_GARANTIE_BY_MONTH = """
SELECT
    BRANCH_CODE,
    BRANCH_NAME,
    ENCOURS_TOTAL_M,
    M1_ENCOURS_DEPOT_GARANTIE,
    M_ENCOURS_DEPOT_GARANTIE,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_DEPOT_GARANTIE
WHERE MIGRATION_DATE_MINUS1 = (
    SELECT MAX(MIGRATION_DATE_MINUS1)
    FROM DASH_DEPOT_GARANTIE d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
ORDER BY BRANCH_CODE, BRANCH_NAME
"""

_SQL_DEPOT_GARANTIE_BY_YEAR = """
SELECT
    BRANCH_CODE,
    BRANCH_NAME,
    ENCOURS_TOTAL_M,
    M1_ENCOURS_DEPOT_GARANTIE,
    M_ENCOURS_DEPOT_GARANTIE,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_DEPOT_GARANTIE
WHERE MIGRATION_DATE_MINUS1 = (
    SELECT MAX(MIGRATION_DATE_MINUS1)
    FROM DASH_DEPOT_GARANTIE d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'YYYY') = :year_only
)
ORDER BY BRANCH_CODE, BRANCH_NAME
"""

_SQL_DEPOT_GARANTIE_BY_WEEK = """
SELECT
    BRANCH_CODE,
    BRANCH_NAME,
    ENCOURS_TOTAL_M,
    M1_ENCOURS_DEPOT_GARANTIE,
    M_ENCOURS_DEPOT_GARANTIE,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_DEPOT_GARANTIE
WHERE MIGRATION_DATE_MINUS1 = (
    SELECT MAX(MIGRATION_DATE_MINUS1)
    FROM DASH_DEPOT_GARANTIE d
    WHERE TRUNC(d.MIGRATION_DATE_MINUS1) BETWEEN TO_DATE(:week_start, 'DD/MM/YYYY')
                                            AND TO_DATE(:week_end, 'DD/MM/YYYY')
)
ORDER BY BRANCH_CODE, BRANCH_NAME
"""


def get_depot_garantie_data(period: str = "month", zone: Optional[str] = None,
                            month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None):
    """
    Récupère les encours dépôt de garantie (DASH_DEPOT_GARANTIE).

    - Semaine : dernier chargement dans la semaine lundi–dimanche de la date (ou d’aujourd’hui).
    - Mois en cours : lot de la veille (J−1).
    - Année : MAX(MIGRATION_DATE_MINUS1) dans cette année civile.
    - Autre mois : MAX dans ce mois calendaire.

    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période semaine (format YYYY-MM-DD)

    Returns:
        Dictionnaire avec les données Dépôt de Garantie organisées par zones
    """
    logger.info(
        f"🔍 get_depot_garantie_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}"
    )

    from services.cache_service import get_cache, set_cache

    period = (period or "month").strip().lower()

    today = dt_date.today()
    ref_m, ref_y = _ref_month_year(period, month, year, date)
    viewing_current_month = ref_y == today.year and ref_m == today.month

    week_range = _week_range_dd_mm_yyyy(period, date)

    year_only_str = None
    if period == "year":
        y = int(year) if year is not None else today.year
        year_only_str = f"{y:04d}"

    if week_range:
        week_start, week_end = week_range
        cache_key = f"depot_garantie:migration:week:{week_start}_{week_end}:v6"
    elif year_only_str is not None:
        cache_key = f"depot_garantie:migration:year:{year_only_str}:v6"
    elif viewing_current_month:
        migration_target = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        cache_key = f"depot_garantie:migration:day:{migration_target}:v6"
    else:
        migration_target = None
        month_year = f"{ref_m:02d}/{ref_y}"
        cache_key = f"depot_garantie:migration:month:{month_year}:v6"

    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données Dépôt de Garantie récupérées depuis le cache")
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
                    "🔍 Dépôt de Garantie — semaine %s → %s (MAX dans l’intervalle)",
                    ws,
                    we,
                )
                cursor.execute(_SQL_DEPOT_GARANTIE_BY_WEEK, {"week_start": ws, "week_end": we})
            elif year_only_str is not None:
                logger.info(
                    "🔍 Dépôt de Garantie — MAX dans l’année %s",
                    year_only_str,
                )
                cursor.execute(_SQL_DEPOT_GARANTIE_BY_YEAR, {"year_only": year_only_str})
            elif viewing_current_month:
                logger.info(
                    "🔍 Dépôt de Garantie — filtre jour %s",
                    migration_target,
                )
                cursor.execute(_SQL_DEPOT_GARANTIE_BY_DAY, {"migration_target": migration_target})
            else:
                logger.info(
                    "🔍 Dépôt de Garantie — MAX dans le mois %s",
                    month_year,
                )
                cursor.execute(_SQL_DEPOT_GARANTIE_BY_MONTH, {"month_year": month_year})

            columns = [desc[0] for desc in cursor.description]
            data = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                data.append(row_dict)
            data = _dedupe_dash_encours_rows(data)

            logger.info(f"📊 {len(data)} lignes récupérées depuis Oracle Cofina (après déduplication le cas échéant)")

            if len(data) == 0:
                logger.warning("⚠️ Aucune donnée Dépôt de Garantie trouvée")
                return {
                    "hierarchicalData": {
                        "TERRITOIRE": {},
                        "POINT SERVICES": {},
                    },
                    "snapshot": None,
                }

            agencies_by_territory = {
                'territoire_dakar_ville': [],
                'territoire_dakar_banlieue': [],
                'territoire_province_centre_sud': [],
                'territoire_province_nord': []
            }

            grand_compte = None

            for row in data:
                branch_code = row.get('BRANCH_CODE') or row.get('branch_code')
                agency_name = (
                    row.get('BRANCH_NAME')
                    or row.get('branch_name')
                    or row.get('AGENCE')
                    or row.get('agence')
                    or ''
                )

                agency = {
                    'BRANCH_CODE': branch_code,
                    'BRANCH_NAME': agency_name,
                    'name': agency_name,
                    'M1_ENCOURS_DEPOT_GARANTIE': float(row.get('M1_ENCOURS_DEPOT_GARANTIE') or 0),
                    'M_ENCOURS_DEPOT_GARANTIE': float(row.get('M_ENCOURS_DEPOT_GARANTIE') or 0),
                    'ENCOURS_TOTAL_M': float(row.get('ENCOURS_TOTAL_M') or 0)
                }

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

            def calculate_territory_totals(agencies_list):
                totals = {
                    'm1EncoursDepotGarantie': 0,
                    'mEncoursDepotGarantie': 0,
                    'encoursTotalM': 0
                }
                for agency in agencies_list:
                    totals['m1EncoursDepotGarantie'] += float(agency.get('M1_ENCOURS_DEPOT_GARANTIE', 0) or 0)
                    totals['mEncoursDepotGarantie'] += float(agency.get('M_ENCOURS_DEPOT_GARANTIE', 0) or 0)
                    totals['encoursTotalM'] += float(agency.get('ENCOURS_TOTAL_M', 0) or 0)
                return totals

            response_data = {
                "hierarchicalData": {
                    "TERRITOIRE": {},
                    "POINT SERVICES": {}
                }
            }

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

                if grand_compte:
                    response_data["hierarchicalData"]["TERRITOIRE"]["grand_compte"] = {
                        "name": "GRAND COMPTE",
                        "agencies": [grand_compte],
                        "totals": {
                            'm1EncoursDepotGarantie': grand_compte.get('M1_ENCOURS_DEPOT_GARANTIE', 0),
                            'mEncoursDepotGarantie': grand_compte.get('M_ENCOURS_DEPOT_GARANTIE', 0),
                            'encoursTotalM': grand_compte.get('ENCOURS_TOTAL_M', 0)
                        }
                    }

            response_data["snapshot"] = _snapshot_from_row(data[0])

            set_cache(cache_key, response_data, ttl=300)

            logger.info(f"✅ Données Dépôt de Garantie récupérées: {len(data)} agences")
            return response_data

        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données Dépôt de Garantie: {str(e)}", exc_info=True)
            raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
