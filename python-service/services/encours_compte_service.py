"""
Service pour la gestion des données Volume DAT
"""
import logging
from typing import Optional, Dict
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key, get_all_territories

logger = logging.getLogger(__name__)


def get_volume_dat_data(period: str = "month", zone: Optional[str] = None, 
                        month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None):
    """
    Récupère les données Volume DAT depuis Oracle
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période semaine (format YYYY-MM-DD)
    
    Returns:
        Dictionnaire avec les données Volume DAT organisées par zones
    """
    logger.info(f"🔍 get_volume_dat_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}")
    
    # Utiliser le mois et l'année actuels si non fournis
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calculer les dates M et M-1
    if period == "month":
        # Date de fin du mois M
        m_end = datetime(year, month, calendar.monthrange(year, month)[1])
        # Date de fin du mois M-1
        if month == 1:
            m1_end = datetime(year - 1, 12, calendar.monthrange(year - 1, 12)[1])
        else:
            m1_end = datetime(year, month - 1, calendar.monthrange(year, month - 1)[1])
    elif period == "year":
        # Date de fin de l'année M
        m_end = datetime(year, 12, 31)
        # Date de fin de l'année M-1
        m1_end = datetime(year - 1, 12, 31)
    elif period == "week":
        # Pour la semaine, utiliser la date fournie ou aujourd'hui
        if date:
            try:
                reference_date = datetime.strptime(date, "%Y-%m-%d")
            except (ValueError, TypeError):
                reference_date = datetime.now()
        else:
            reference_date = datetime.now()
        
        # Trouver le dimanche de la semaine (fin de semaine)
        from datetime import timedelta
        days_since_monday = reference_date.weekday()
        sunday = reference_date + timedelta(days=(6 - days_since_monday))
        m_end = sunday
        
        # Semaine précédente
        m1_end = sunday - timedelta(days=7)
    else:
        # Par défaut, utiliser le mois actuel
        now = datetime.now()
        m_end = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
        if now.month == 1:
            m1_end = datetime(now.year - 1, 12, calendar.monthrange(now.year - 1, 12)[1])
        else:
            m1_end = datetime(now.year, now.month - 1, calendar.monthrange(now.year, now.month - 1)[1])
    
    # Formater les dates pour Oracle (DD/MM/YYYY)
    m_end_str = m_end.strftime("%d/%m/%Y")
    m1_end_str = m1_end.strftime("%d/%m/%Y")
    
    logger.info(f"📅 Dates calculées: M fin={m_end_str}, M-1 fin={m1_end_str}")
    
    # Utiliser le pool de connexions et le cache
    from database.oracle_pool import get_pool
    from services.cache_service import get_cache, set_cache, generate_cache_key
    
    # Générer une clé de cache basée sur les paramètres
    cache_key = f"volume_dat:{generate_cache_key(period, zone, month, year, date)}:territoire_v2"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données Volume DAT récupérées depuis le cache")
        return cached_result
    
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        
        # Optimisations Oracle
        cursor.arraysize = 1000
        cursor.prefetchrows = 1000
        
        try:
            logger.info("🔍 Exécution de la requête Volume DAT...")
            
            # Construire la requête SQL avec les dates dynamiques
            query = f"""
WITH JOURNAL AS (
    SELECT
        AC_ENTRY_SR_NO,
        AC_NO,
        DRCR_IND,
        LCY_AMOUNT,
        CASE 
            WHEN MODULE = 'DE' THEN VALUE_DT 
            ELSE TRN_DT 
        END AS TRN_DT
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES
),
 
COMPTE AS (
    SELECT 
        cpt.BRANCH_CODE,
        cpt.CUST_AC_NO,
        cpt.AC_DESC,
        cs.ACCOUNT_CLASS,
        cs.DESCRIPTION,
        cs.ACCOUNT_CODE
    FROM CFSFCUBS145.STTM_CUST_ACCOUNT cpt
    JOIN CFSFCUBS145.STTM_ACCOUNT_CLASS cs 
        ON cpt.ACCOUNT_CLASS = cs.ACCOUNT_CLASS
),
 
BRANCH AS (
    SELECT  
        BRANCH_CODE,
        BRANCH_NAME
    FROM CFSFCUBS145.STTM_BRANCH
),
 
 
-- DAT
DAT AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '252'
    GROUP BY y.BRANCH_CODE
)

SELECT 
    O.BRANCH_CODE,
    BR.BRANCH_NAME as AGENCE,
    O.M_1 as DAT_M_1,
    O.M as DAT_M,
    (O.M - O.M_1) as VARIATION_VOLUME_DA,
    NVL(ROUND(
        (((O.M - O.M_1)) / NULLIF(O.M_1, 0)) * 100, 
        2
    ), 0) AS "VARIATION_DAT%"
FROM DAT O
LEFT JOIN BRANCH BR ON BR.BRANCH_CODE = O.BRANCH_CODE
ORDER BY BR.BRANCH_NAME
"""
            
            logger.info(f"⏱️  Exécution de la requête Volume DAT (timeout: 5 minutes)")
            cursor.execute(query)
            
            # Récupérer les résultats
            columns = [desc[0] for desc in cursor.description]
            data = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                data.append(row_dict)
            
            logger.info(f"📊 {len(data)} lignes récupérées depuis Oracle")
            
            if len(data) == 0:
                logger.warning("⚠️ Aucune donnée Volume DAT trouvée")
                return {
                    "hierarchicalData": {
                        "TERRITOIRE": {},
                        "POINT SERVICES": {}
                    }
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
                
                # Créer l'objet agence
                # Gérer la colonne VARIATION_DAT% qui peut être retournée avec ou sans %
                variation_dat_value = row.get('VARIATION_DAT%') or row.get('VARIATION_DAT') or row.get('"VARIATION_DAT%"') or 0
                agency = {
                    'BRANCH_CODE': branch_code,
                    'AGENCE': agency_name,
                    'name': agency_name,
                    'DAT_M_1': float(row.get('DAT_M_1') or 0),
                    'DAT_M': float(row.get('DAT_M') or 0),
                    'VARIATION_VOLUME_DA': float(row.get('VARIATION_VOLUME_DA') or 0),
                    'VARIATION_DAT': float(variation_dat_value),
                    'VARIATION_DAT%': float(variation_dat_value)  # Alias pour compatibilité
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
            
            # Calculer les totaux pour chaque territoire
            def calculate_territory_totals(agencies_list):
                """Calcule les totaux pour un territoire"""
                totals = {
                    'datM1': 0,
                    'datM': 0,
                    'variationVolumeDa': 0,
                    'variationDat': 0
                }
                for agency in agencies_list:
                    totals['datM1'] += float(agency.get('DAT_M_1', 0) or 0)
                    totals['datM'] += float(agency.get('DAT_M', 0) or 0)
                    totals['variationVolumeDa'] += float(agency.get('VARIATION_VOLUME_DA', 0) or 0)
                    totals['variationDat'] += float(agency.get('VARIATION_DAT', 0) or 0)
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
                            'variationDat': grand_compte.get('VARIATION_DAT', 0)
                        }
                    }
            
            # Mettre en cache le résultat (TTL de 5 minutes)
            set_cache(cache_key, response_data, ttl=300)
            
            logger.info(f"✅ Données Volume DAT récupérées: {len(data)} agences")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données Volume DAT: {str(e)}", exc_info=True)
            raise
