"""
Service pour la gestion des données de collection
"""
import logging
from typing import Optional, Dict
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key, get_all_territories

logger = logging.getLogger(__name__)


def calculate_week_dates_in_month(month: int, year: int) -> Dict[str, str]:
    """
    Calcule les dates des 4 semaines dans un mois donné
    
    Args:
        month: Mois (1-12)
        year: Année
        
    Returns:
        Dictionnaire avec les dates au format DD/MM/YYYY et YYYY-MM-DD
    """
    # Premier jour du mois
    first_day = datetime(year, month, 1)
    # Dernier jour du mois
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Calculer les dates de fin de chaque semaine
    s1_end = min(datetime(year, month, 7), last_day)
    s2_end = min(datetime(year, month, 14), last_day)
    s3_end = min(datetime(year, month, 21), last_day)
    s4_end = last_day
    
    # Calculer les dates de début de chaque semaine
    s1_debut = first_day
    s2_debut = datetime(year, month, 8) if datetime(year, month, 8) <= last_day else s1_end
    s3_debut = datetime(year, month, 15) if datetime(year, month, 15) <= last_day else s2_end
    s4_debut = datetime(year, month, 22) if datetime(year, month, 22) <= last_day else s3_end
    
    # Mois précédent (M-1)
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    prev_last_day = datetime(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
    prev_first_day = datetime(prev_year, prev_month, 1)
    
    return {
        'm_debut': first_day.strftime("%d/%m/%Y"),
        'm_fin': last_day.strftime("%d/%m/%Y"),
        'm1_fin': prev_last_day.strftime("%d/%m/%Y"),
        'm1_debut': prev_first_day.strftime("%d/%m/%Y"),
        's1_fin': s1_end.strftime("%d/%m/%Y"),
        's2_fin': s2_end.strftime("%d/%m/%Y"),
        's3_fin': s3_end.strftime("%d/%m/%Y"),
        's4_fin': s4_end.strftime("%d/%m/%Y"),
        's1_debut': s1_debut.strftime("%d/%m/%Y"),
        's2_debut': s2_debut.strftime("%d/%m/%Y"),
        's3_debut': s3_debut.strftime("%d/%m/%Y"),
        's4_debut': s4_debut.strftime("%d/%m/%Y"),
        # Format DATE pour Oracle (YYYY-MM-DD)
        'm_debut_date': first_day.strftime("%Y-%m-%d"),
        'm_fin_date': last_day.strftime("%Y-%m-%d"),
        'm1_debut_date': prev_first_day.strftime("%Y-%m-%d"),
        'm1_fin_date': prev_last_day.strftime("%Y-%m-%d"),
        's1_debut_date': s1_debut.strftime("%Y-%m-%d"),
        's1_fin_date': s1_end.strftime("%Y-%m-%d"),
        's2_debut_date': s2_debut.strftime("%Y-%m-%d"),
        's2_fin_date': s2_end.strftime("%Y-%m-%d"),
        's3_debut_date': s3_debut.strftime("%Y-%m-%d"),
        's3_fin_date': s3_end.strftime("%Y-%m-%d"),
        's4_debut_date': s4_debut.strftime("%Y-%m-%d"),
        's4_fin_date': s4_end.strftime("%Y-%m-%d"),
    }


def get_collection_data(period: str = "month", zone: Optional[str] = None, 
                       month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None):
    """
    Récupère les données de collection depuis Oracle en utilisant la requête complète pour l'exigible
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période semaine (format YYYY-MM-DD)
    
    Returns:
        Dictionnaire avec les données de collection organisées par zones
    """
    logger.info(f"🔍 get_collection_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}")
    
    # Pour l'instant, on ne gère que la période "month"
    if period != "month":
        logger.warning(f"⚠️ Période '{period}' non supportée pour la collection. Utilisation de 'month' par défaut.")
        period = "month"
    
    # Utiliser le mois et l'année actuels si non fournis
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calculer les dates des semaines
    week_dates = calculate_week_dates_in_month(month, year)
    
    logger.info(f"📅 Dates calculées: M={week_dates['m_debut']} à {week_dates['m_fin']}, M-1 fin={week_dates['m1_fin']}")
    logger.info(f"📅 Semaines: S1 fin={week_dates['s1_fin']}, S2 fin={week_dates['s2_fin']}, S3 fin={week_dates['s3_fin']}, S4 fin={week_dates['s4_fin']}")
    
    # Utiliser le pool de connexions et le cache
    from database.oracle_pool import get_pool
    from services.cache_service import get_cache, set_cache, generate_cache_key
    
    # Générer une clé de cache basée sur les paramètres
    cache_key = f"collection:{generate_cache_key(period, zone, month, year, date)}"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données de collection récupérées depuis le cache")
        return cached_result
    
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        
        # Optimisations Oracle
        cursor.arraysize = 1000  # Optimiser la récupération par lots
        # Activer le mode de récupération optimisé
        cursor.prefetchrows = 1000
        
        try:
            logger.info("🔍 Exécution de la requête complète pour l'exigible...")
            logger.info("⏱️  Timeout configuré: 5 minutes (300 secondes)")
            
            # Construire la requête SQL complète avec les dates dynamiques
            query = f"""
        WITH NUM_ECH_PRINCIPAL AS (
            SELECT 
                e.ACCOUNT_NUMBER,
                e.DUE_DATE,
                ROW_NUMBER() OVER (
                    PARTITION BY e.ACCOUNT_NUMBER
                    ORDER BY e.DUE_DATE
                ) AS NUMERO_ECHEANCE
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID e
            WHERE e.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY e.ACCOUNT_NUMBER, e.DUE_DATE
        ),
        ECHEANCES_PRINCIPAL_M_1 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS PRINCIPAL_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_PRINCIPAL n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'PRINCIPAL'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['m_fin']}', 'DD/MM/YYYY')
        ),
        TA_PRINCIPAL_PAID_M_1 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.PRINCIPAL_PAID) AS PRINCIPAL_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_PRINCIPAL_M_1 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        NUM_ECH_MAIN_INT AS (
            SELECT 
                e.ACCOUNT_NUMBER,
                e.DUE_DATE,
                ROW_NUMBER() OVER (
                    PARTITION BY e.ACCOUNT_NUMBER
                    ORDER BY e.DUE_DATE
                ) AS NUMERO_ECHEANCE
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID e
            WHERE e.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY e.ACCOUNT_NUMBER, e.DUE_DATE
        ),
        ECHEANCES_MAIN_INT_M_1 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS MAIN_INT_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_MAIN_INT n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'MAIN_INT'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['m_fin']}', 'DD/MM/YYYY')
        ),
        TA_MAIN_INT_PAID_M_1 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.MAIN_INT_PAID) AS MAIN_INT_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_MAIN_INT_M_1 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        EXIGIBLE_M_1 AS (
            SELECT  
                IT.ACCOUNT_NUMBER AS NUMERO_PRET,
                pr.CR_PROD_AC,
                IT.NUMERO_ECHEANCE,
                SH.AMOUNT_DUE AS PART_CAP,
                SH.PRINCIPAL_PAID AS PART_CAP_PAY,
                (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0)) AS PART_CAP_IMP,
                IT.AMOUNT_DUE AS PART_INT,
                IT.MAIN_INT_PAID AS PART_INT_PAY,
                (NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) AS PART_INT_IMP,
                ((NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) + (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0))) AS EXIGIBLE_M_1,
                IT.SCHEDULE_DUE_DATE,
                IT.SCH_STATUS AS SCH_STATUS_INT,
                SH.SCH_STATUS AS SCH_STATUS_CAP,
                CASE
                    WHEN IT.SCH_STATUS = 'IMPY' OR SH.SCH_STATUS = 'IMPY' THEN 'IMPY'
                    WHEN IT.SCH_STATUS = 'NORM' OR SH.SCH_STATUS = 'NORM' THEN 'NORM'
                    ELSE NVL(IT.SCH_STATUS, SH.SCH_STATUS)
                END AS STATUT_FINAL,
                CASE
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) = 0
                        THEN 'REMBOURSE'
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) > 0
                        THEN 'IMPAYE'
                    ELSE 'ATTENTE'
                END AS STATUS_ECHEANCE
            FROM TA_MAIN_INT_PAID_M_1 IT
            LEFT JOIN TA_PRINCIPAL_PAID_M_1 SH
                ON SH.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
              AND SH.NUMERO_ECHEANCE = IT.NUMERO_ECHEANCE
            LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_MASTER pr ON pr.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
        ),
        ECHEANCES_PRINCIPAL_S1 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS PRINCIPAL_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_PRINCIPAL n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'PRINCIPAL'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s1_fin']}', 'DD/MM/YYYY')
        ),
        TA_PRINCIPAL_PAID_S1 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.PRINCIPAL_PAID) AS PRINCIPAL_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_PRINCIPAL_S1 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        ECHEANCES_MAIN_INT_S1 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS MAIN_INT_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_MAIN_INT n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'MAIN_INT'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s1_fin']}', 'DD/MM/YYYY')
        ),
        TA_MAIN_INT_PAID_S1 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.MAIN_INT_PAID) AS MAIN_INT_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_MAIN_INT_S1 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        EXIGIBLE_S1 AS (
            SELECT  
                IT.ACCOUNT_NUMBER AS NUMERO_PRET,
                pr.CR_PROD_AC,
                IT.NUMERO_ECHEANCE,
                SH.AMOUNT_DUE AS PART_CAP,
                SH.PRINCIPAL_PAID AS PART_CAP_PAY,
                (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0)) AS PART_CAP_IMP,
                IT.AMOUNT_DUE AS PART_INT,
                IT.MAIN_INT_PAID AS PART_INT_PAY,
                (NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) AS PART_INT_IMP,
                ((NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) + (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0))) AS EXIGIBLE_S1,
                IT.SCHEDULE_DUE_DATE,
                IT.SCH_STATUS AS SCH_STATUS_INT,
                SH.SCH_STATUS AS SCH_STATUS_CAP,
                CASE
                    WHEN IT.SCH_STATUS = 'IMPY' OR SH.SCH_STATUS = 'IMPY' THEN 'IMPY'
                    WHEN IT.SCH_STATUS = 'NORM' OR SH.SCH_STATUS = 'NORM' THEN 'NORM'
                    ELSE NVL(IT.SCH_STATUS, SH.SCH_STATUS)
                END AS STATUT_FINAL,
                CASE
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) = 0
                        THEN 'REMBOURSE'
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) > 0
                        THEN 'IMPAYE'
                    ELSE 'ATTENTE'
                END AS STATUS_ECHEANCE
            FROM TA_MAIN_INT_PAID_S1 IT
            LEFT JOIN TA_PRINCIPAL_PAID_S1 SH
                ON SH.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
              AND SH.NUMERO_ECHEANCE = IT.NUMERO_ECHEANCE
            LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_MASTER pr ON pr.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
        ),
        ECHEANCES_PRINCIPAL_S2 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS PRINCIPAL_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_PRINCIPAL n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'PRINCIPAL'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s2_fin']}', 'DD/MM/YYYY')
        ),
        TA_PRINCIPAL_PAID_S2 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.PRINCIPAL_PAID) AS PRINCIPAL_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_PRINCIPAL_S2 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        ECHEANCES_MAIN_INT_S2 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS MAIN_INT_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_MAIN_INT n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'MAIN_INT'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s2_fin']}', 'DD/MM/YYYY')
        ),
        TA_MAIN_INT_PAID_S2 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.MAIN_INT_PAID) AS MAIN_INT_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_MAIN_INT_S2 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        EXIGIBLE_S2 AS (
            SELECT  
                IT.ACCOUNT_NUMBER AS NUMERO_PRET,
                pr.CR_PROD_AC,
                IT.NUMERO_ECHEANCE,
                SH.AMOUNT_DUE AS PART_CAP,
                SH.PRINCIPAL_PAID AS PART_CAP_PAY,
                (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0)) AS PART_CAP_IMP,
                IT.AMOUNT_DUE AS PART_INT,
                IT.MAIN_INT_PAID AS PART_INT_PAY,
                (NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) AS PART_INT_IMP,
                ((NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) + (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0))) AS EXIGIBLE_S2,
                IT.SCHEDULE_DUE_DATE,
                IT.SCH_STATUS AS SCH_STATUS_INT,
                SH.SCH_STATUS AS SCH_STATUS_CAP,
                CASE
                    WHEN IT.SCH_STATUS = 'IMPY' OR SH.SCH_STATUS = 'IMPY' THEN 'IMPY'
                    WHEN IT.SCH_STATUS = 'NORM' OR SH.SCH_STATUS = 'NORM' THEN 'NORM'
                    ELSE NVL(IT.SCH_STATUS, SH.SCH_STATUS)
                END AS STATUT_FINAL,
                CASE
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) = 0
                        THEN 'REMBOURSE'
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) > 0
                        THEN 'IMPAYE'
                    ELSE 'ATTENTE'
                END AS STATUS_ECHEANCE
            FROM TA_MAIN_INT_PAID_S2 IT
            LEFT JOIN TA_PRINCIPAL_PAID_S2 SH
                ON SH.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
              AND SH.NUMERO_ECHEANCE = IT.NUMERO_ECHEANCE
            LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_MASTER pr ON pr.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
        ),
        ECHEANCES_PRINCIPAL_S3 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS PRINCIPAL_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_PRINCIPAL n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'PRINCIPAL'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s3_fin']}', 'DD/MM/YYYY')
        ),
        TA_PRINCIPAL_PAID_S3 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.PRINCIPAL_PAID) AS PRINCIPAL_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_PRINCIPAL_S3 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        ECHEANCES_MAIN_INT_S3 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS MAIN_INT_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_MAIN_INT n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'MAIN_INT'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s3_fin']}', 'DD/MM/YYYY')
        ),
        TA_MAIN_INT_PAID_S3 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.MAIN_INT_PAID) AS MAIN_INT_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_MAIN_INT_S3 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        EXIGIBLE_S3 AS (
            SELECT  
                IT.ACCOUNT_NUMBER AS NUMERO_PRET,
                pr.CR_PROD_AC,
                IT.NUMERO_ECHEANCE,
                SH.AMOUNT_DUE AS PART_CAP,
                SH.PRINCIPAL_PAID AS PART_CAP_PAY,
                (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0)) AS PART_CAP_IMP,
                IT.AMOUNT_DUE AS PART_INT,
                IT.MAIN_INT_PAID AS PART_INT_PAY,
                (NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) AS PART_INT_IMP,
                ((NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) + (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0))) AS EXIGIBLE_S3,
                IT.SCHEDULE_DUE_DATE,
                IT.SCH_STATUS AS SCH_STATUS_INT,
                SH.SCH_STATUS AS SCH_STATUS_CAP,
                CASE
                    WHEN IT.SCH_STATUS = 'IMPY' OR SH.SCH_STATUS = 'IMPY' THEN 'IMPY'
                    WHEN IT.SCH_STATUS = 'NORM' OR SH.SCH_STATUS = 'NORM' THEN 'NORM'
                    ELSE NVL(IT.SCH_STATUS, SH.SCH_STATUS)
                END AS STATUT_FINAL,
                CASE
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) = 0
                        THEN 'REMBOURSE'
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) > 0
                        THEN 'IMPAYE'
                    ELSE 'ATTENTE'
                END AS STATUS_ECHEANCE
            FROM TA_MAIN_INT_PAID_S3 IT
            LEFT JOIN TA_PRINCIPAL_PAID_S3 SH
                ON SH.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
              AND SH.NUMERO_ECHEANCE = IT.NUMERO_ECHEANCE
            LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_MASTER pr ON pr.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
        ),
        ECHEANCES_PRINCIPAL_S4 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS PRINCIPAL_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_PRINCIPAL n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'PRINCIPAL'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s4_fin']}', 'DD/MM/YYYY')
        ),
        TA_PRINCIPAL_PAID_S4 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.PRINCIPAL_PAID) AS PRINCIPAL_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_PRINCIPAL_S4 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'PRINCIPAL'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        ECHEANCES_MAIN_INT_S4 AS (
            SELECT
                p.ACCOUNT_NUMBER,
                n.NUMERO_ECHEANCE,
                p.DUE_DATE,
                p.PAID_DATE,
                p.AMOUNT_PAID AS MAIN_INT_PAID
            FROM CFSFCUBS145.CLTB_AMOUNT_PAID p
            JOIN NUM_ECH_MAIN_INT n
                ON n.ACCOUNT_NUMBER = p.ACCOUNT_NUMBER
               AND n.DUE_DATE = p.DUE_DATE
            WHERE p.COMPONENT_NAME = 'MAIN_INT'
              AND p.PAID_STATUS = 'N'
              AND p.DUE_DATE <= TO_DATE('{week_dates['m1_fin']}', 'DD/MM/YYYY')
              AND p.PAID_DATE <= TO_DATE('{week_dates['s4_fin']}', 'DD/MM/YYYY')
        ),
        TA_MAIN_INT_PAID_S4 AS (
            SELECT
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                MAX(e.PAID_DATE) AS PAID_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                SUM(e.MAIN_INT_PAID) AS MAIN_INT_PAID,
                s.SCH_STATUS
            FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES s
            LEFT JOIN ECHEANCES_MAIN_INT_S4 e
                ON e.ACCOUNT_NUMBER = s.ACCOUNT_NUMBER
               AND e.DUE_DATE = s.SCHEDULE_DUE_DATE
            WHERE s.COMPONENT_NAME = 'MAIN_INT'
            GROUP BY
                e.ACCOUNT_NUMBER,
                e.NUMERO_ECHEANCE,
                e.DUE_DATE,
                s.SCHEDULE_DUE_DATE,
                s.AMOUNT_DUE,
                s.AMOUNT_SETTLED,
                s.SCH_STATUS
        ),
        EXIGIBLE_S4 AS (
            SELECT  
                IT.ACCOUNT_NUMBER AS NUMERO_PRET,
                pr.CR_PROD_AC,
                IT.NUMERO_ECHEANCE,
                SH.AMOUNT_DUE AS PART_CAP,
                SH.PRINCIPAL_PAID AS PART_CAP_PAY,
                (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0)) AS PART_CAP_IMP,
                IT.AMOUNT_DUE AS PART_INT,
                IT.MAIN_INT_PAID AS PART_INT_PAY,
                (NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) AS PART_INT_IMP,
                ((NVL(IT.AMOUNT_DUE,0) - NVL(IT.MAIN_INT_PAID,0)) + (NVL(SH.AMOUNT_DUE,0) - NVL(SH.PRINCIPAL_PAID,0))) AS EXIGIBLE_S4,
                IT.SCHEDULE_DUE_DATE,
                IT.SCH_STATUS AS SCH_STATUS_INT,
                SH.SCH_STATUS AS SCH_STATUS_CAP,
                CASE
                    WHEN IT.SCH_STATUS = 'IMPY' OR SH.SCH_STATUS = 'IMPY' THEN 'IMPY'
                    WHEN IT.SCH_STATUS = 'NORM' OR SH.SCH_STATUS = 'NORM' THEN 'NORM'
                    ELSE NVL(IT.SCH_STATUS, SH.SCH_STATUS)
                END AS STATUT_FINAL,
                CASE
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) = 0
                        THEN 'REMBOURSE'
                    WHEN (NVL(SH.AMOUNT_DUE,0) - NVL(SH.AMOUNT_SETTLED,0)
                        + NVL(IT.AMOUNT_DUE,0) - NVL(IT.AMOUNT_SETTLED,0)) > 0
                        THEN 'IMPAYE'
                    ELSE 'ATTENTE'
                END AS STATUS_ECHEANCE
            FROM TA_MAIN_INT_PAID_S4 IT
            LEFT JOIN TA_PRINCIPAL_PAID_S4 SH
                ON SH.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
              AND SH.NUMERO_ECHEANCE = IT.NUMERO_ECHEANCE
            LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_MASTER pr ON pr.ACCOUNT_NUMBER = IT.ACCOUNT_NUMBER
        ),
        JOURNAL AS (
            SELECT
                e.AC_ENTRY_SR_NO,
                e.AC_BRANCH,
                b.BRANCH_NAME AS AGENCE,
                e.AC_NO,
                e.MODULE,
                e.DRCR_IND,
                e.TRN_CODE,
                e.LCY_AMOUNT,
                CASE 
                    WHEN e.MODULE = 'DE' THEN e.VALUE_DT 
                    ELSE e.TRN_DT 
                END AS TRN_DT
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES e
            LEFT JOIN CFSFCUBS145.STTM_BRANCH b ON b.BRANCH_CODE = e.AC_BRANCH
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
        DEPOT_CPT_COURANT AS (
            SELECT
                a.AC_NO,
                y.BRANCH_CODE,
                MAX(a.AGENCE) AS AGENCE,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['m1_debut_date']}' AND DATE '{week_dates['m1_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS M_1,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['m_debut_date']}' AND DATE '{week_dates['m_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS M,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['s1_debut_date']}' AND DATE '{week_dates['s1_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS S1,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['s2_debut_date']}' AND DATE '{week_dates['s2_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS S2,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['s3_debut_date']}' AND DATE '{week_dates['s3_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS S3,
                SUM(CASE 
                    WHEN a.DRCR_IND = 'C'
                     AND a.TRN_DT BETWEEN DATE '{week_dates['s4_debut_date']}' AND DATE '{week_dates['s4_fin_date']}'
                    THEN a.LCY_AMOUNT ELSE 0 END) AS S4
            FROM JOURNAL a
            JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
            WHERE y.ACCOUNT_CODE = '251'
              AND a.MODULE <> 'CL'
            GROUP BY a.AC_NO, y.BRANCH_CODE
        ),
        SOLDE_CPT_COURANT AS (
            SELECT 
                a.AC_NO,
                y.BRANCH_CODE,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['m_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['m_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_M,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['m1_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['m1_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_M_1,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['s1_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['s1_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_1,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['s2_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['s2_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_2,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['s3_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['s3_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_3,
                SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= DATE '{week_dates['s4_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END)
              - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= DATE '{week_dates['s4_fin_date']}' THEN a.LCY_AMOUNT ELSE 0 END) AS SLD_4
            FROM JOURNAL a
            JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
            WHERE y.ACCOUNT_CODE = '251'
            GROUP BY a.AC_NO, y.BRANCH_CODE
        ),
        MT_ECH_M AS (
            SELECT
                c.CR_PROD_AC AS NO_CPT,
                SUM(NVL(z.AMOUNT_DUE,0)) AS MT_ECH_M,
                SUM(NVL(z.AMOUNT_SETTLED,0)) AS MT_RECOUVR_ECH_M,
                SUM(NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) AS EXIGIBLE_ECH_M
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
            JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
                 ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
            WHERE c.ACCOUNT_STATUS NOT IN ('L','V')
              AND z.COMPONENT_NAME IN ('PRINCIPAL','MAIN_INT')
              AND z.SCHEDULE_DUE_DATE BETWEEN DATE '{week_dates['m_debut_date']}' AND DATE '{week_dates['m_fin_date']}'
            GROUP BY c.CR_PROD_AC
        ),
        MT_ECH_S1 AS (
            SELECT
                c.CR_PROD_AC AS NO_CPT,
                SUM(NVL(z.AMOUNT_DUE,0)) AS MT_ECH_S1
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
            JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
                 ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
            WHERE c.ACCOUNT_STATUS NOT IN ('L','V')
              AND z.COMPONENT_NAME IN ('PRINCIPAL','MAIN_INT')
              AND z.SCHEDULE_DUE_DATE BETWEEN DATE '{week_dates['s1_debut_date']}' AND DATE '{week_dates['s1_fin_date']}'
            GROUP BY c.CR_PROD_AC
        ),
        MT_ECH_S2 AS (
            SELECT
                c.CR_PROD_AC AS NO_CPT,
                SUM(NVL(z.AMOUNT_DUE,0)) AS MT_ECH_S2
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
            JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
                 ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
            WHERE c.ACCOUNT_STATUS NOT IN ('L','V')
              AND z.COMPONENT_NAME IN ('PRINCIPAL','MAIN_INT')
              AND z.SCHEDULE_DUE_DATE BETWEEN DATE '{week_dates['s2_debut_date']}' AND DATE '{week_dates['s2_fin_date']}'
            GROUP BY c.CR_PROD_AC
        ),
        MT_ECH_S3 AS (
            SELECT
                c.CR_PROD_AC AS NO_CPT,
                SUM(NVL(z.AMOUNT_DUE,0)) AS MT_ECH_S3
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
            JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
                 ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
            WHERE c.ACCOUNT_STATUS NOT IN ('L','V')
              AND z.COMPONENT_NAME IN ('PRINCIPAL','MAIN_INT')
              AND z.SCHEDULE_DUE_DATE BETWEEN DATE '{week_dates['s3_debut_date']}' AND DATE '{week_dates['s3_fin_date']}'
            GROUP BY c.CR_PROD_AC
        ),
        MT_ECH_S4 AS (
            SELECT
                c.CR_PROD_AC AS NO_CPT,
                SUM(NVL(z.AMOUNT_DUE,0)) AS MT_ECH_S4
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
            JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
                 ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
            WHERE c.ACCOUNT_STATUS NOT IN ('L','V')
              AND z.COMPONENT_NAME IN ('PRINCIPAL','MAIN_INT')
              AND z.SCHEDULE_DUE_DATE BETWEEN DATE '{week_dates['s4_debut_date']}' AND DATE '{week_dates['s4_fin_date']}'
            GROUP BY c.CR_PROD_AC
        ),
        CODE_GESTIONNAIRE AS (
            SELECT 
                p.CR_PROD_AC,
                p.FIELD_CHAR_2 AS CODE_GESTION_PRET,
                (SELECT MAX(u.LOV_DESC) 
                 FROM CFSFCUBS145.UDTM_LOV u 
                 WHERE u.FIELD_NAME='GESTION_PRET' AND u.LOV=p.FIELD_CHAR_2) AS CHARGE_AFFAIRE
            FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER p
        ),
        CODE_GES AS (
            SELECT *
            FROM (
                SELECT m.*,
                       ROW_NUMBER() OVER (PARTITION BY m.CR_PROD_AC ORDER BY m.CR_PROD_AC DESC) AS RN
                FROM CODE_GESTIONNAIRE m
            ) t
            WHERE RN = 1
        ),
        EXIGIBLE_AGG_M_1 AS (
            SELECT
                CR_PROD_AC,
                SUM(EXIGIBLE_M_1) AS EXIGIBLE_M_1
            FROM EXIGIBLE_M_1
            GROUP BY CR_PROD_AC
        ),
        EXIGIBLE_AGG_S1 AS (
            SELECT
                CR_PROD_AC,
                SUM(EXIGIBLE_S1) AS EXIGIBLE_S1
            FROM EXIGIBLE_S1
            GROUP BY CR_PROD_AC
        ),
        EXIGIBLE_AGG_S2 AS (
            SELECT
                CR_PROD_AC,
                SUM(EXIGIBLE_S2) AS EXIGIBLE_S2
            FROM EXIGIBLE_S2
            GROUP BY CR_PROD_AC
        ),
        EXIGIBLE_AGG_S3 AS (
            SELECT
                CR_PROD_AC,
                SUM(EXIGIBLE_S3) AS EXIGIBLE_S3
            FROM EXIGIBLE_S3
            GROUP BY CR_PROD_AC
        ),
        EXIGIBLE_AGG_S4 AS (
            SELECT
                CR_PROD_AC,
                SUM(EXIGIBLE_S4) AS EXIGIBLE_S4
            FROM EXIGIBLE_S4
            GROUP BY CR_PROD_AC
        )
        SELECT
            CO.AC_NO,
            CO.AGENCE,
            CO.BRANCH_CODE,
            CG.CODE_GESTION_PRET,
            CG.CHARGE_AFFAIRE,
            NVL(EX1.EXIGIBLE_M_1, 0) AS EXIGIBLE_M_1,
            NVL(EXS1.EXIGIBLE_S1, 0) AS EXIGIBLE_S1,
            NVL(EXS2.EXIGIBLE_S2, 0) AS EXIGIBLE_S2,
            NVL(EXS3.EXIGIBLE_S3, 0) AS EXIGIBLE_S3,
            NVL(EXS4.EXIGIBLE_S4, 0) AS EXIGIBLE_S4,
            NVL(SLD.SLD_M, 0) AS SLD_M,
            NVL(SLD.SLD_M_1, 0) AS SLD_M_1,
            NVL(SLD.SLD_1, 0) AS SLD_1,
            NVL(SLD.SLD_2, 0) AS SLD_2,
            NVL(SLD.SLD_3, 0) AS SLD_3,
            NVL(SLD.SLD_4, 0) AS SLD_4,
            CO.M_1,
            CO.M,
            CO.S1,
            CO.S2,
            CO.S3,
            CO.S4,
            NVL(ECH_M.MT_ECH_M, 0) AS MT_ECH_M,
            NVL(ECH_S1.MT_ECH_S1, 0) AS MT_ECH_S1,
            NVL(ECH_S2.MT_ECH_S2, 0) AS MT_ECH_S2,
            NVL(ECH_S3.MT_ECH_S3, 0) AS MT_ECH_S3,
            NVL(ECH_S4.MT_ECH_S4, 0) AS MT_ECH_S4
        FROM DEPOT_CPT_COURANT CO
        LEFT JOIN SOLDE_CPT_COURANT SLD 
               ON SLD.AC_NO = CO.AC_NO
              AND SLD.BRANCH_CODE = CO.BRANCH_CODE
        LEFT JOIN EXIGIBLE_AGG_M_1 EX1 
               ON EX1.CR_PROD_AC = CO.AC_NO
        LEFT JOIN EXIGIBLE_AGG_S1 EXS1 
               ON EXS1.CR_PROD_AC = CO.AC_NO
        LEFT JOIN EXIGIBLE_AGG_S2 EXS2 
               ON EXS2.CR_PROD_AC = CO.AC_NO
        LEFT JOIN EXIGIBLE_AGG_S3 EXS3 
               ON EXS3.CR_PROD_AC = CO.AC_NO
        LEFT JOIN EXIGIBLE_AGG_S4 EXS4 
               ON EXS4.CR_PROD_AC = CO.AC_NO
        LEFT JOIN MT_ECH_M ECH_M 
               ON ECH_M.NO_CPT = CO.AC_NO
        LEFT JOIN MT_ECH_S1 ECH_S1 
               ON ECH_S1.NO_CPT = CO.AC_NO
        LEFT JOIN MT_ECH_S2 ECH_S2 
               ON ECH_S2.NO_CPT = CO.AC_NO
        LEFT JOIN MT_ECH_S3 ECH_S3 
               ON ECH_S3.NO_CPT = CO.AC_NO
        LEFT JOIN MT_ECH_S4 ECH_S4 
               ON ECH_S4.NO_CPT = CO.AC_NO
        LEFT JOIN CODE_GES CG 
               ON CG.CR_PROD_AC = CO.AC_NO
        ORDER BY CO.AC_NO
        """
        
            import time
            start_time = time.time()
            logger.info("⏱️  Début de l'exécution de la requête SQL...")
            
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            execution_time = time.time() - start_time
            logger.info(f"✅ {len(results)} lignes récupérées en {execution_time:.2f} secondes")
            
            # Traiter les résultats et structurer les données
            data = []
            for row in results:
                row_dict = dict(zip(columns, row))
                data.append(row_dict)
        
            # Log pour déboguer MT_ECH_M
            if len(data) > 0:
                sample_row = data[0]
                logger.info(f"🔍 Exemple de données récupérées: AC_NO={sample_row.get('AC_NO')}, MT_ECH_M={sample_row.get('MT_ECH_M')}, EXIGIBLE_M_1={sample_row.get('EXIGIBLE_M_1')}")
                mt_ech_count = sum(1 for r in data if r.get('MT_ECH_M', 0) and float(r.get('MT_ECH_M', 0) or 0) > 0)
                logger.info(f"📊 Nombre de lignes avec MT_ECH_M > 0: {mt_ech_count} sur {len(data)}")
            
            # Grouper par agence et territoire
            agencies_by_territory = {
                'territoire_dakar_ville': [],
                'territoire_dakar_banlieue': [],
                'territoire_province_centre_sud': [],
                'territoire_province_nord': []
            }
            
            grand_compte = None
            agencies_data = {}
            charge_affaire_data = {}  # Structure pour regrouper par chargé d'affaire: {agency_key: {charge_affaire_key: {...}}}
            
            for row in data:
                agency_name = row.get('AGENCE') or 'INCONNU'
                branch_code = row.get('BRANCH_CODE') or ''
                ac_no = row.get('AC_NO') or ''
                code_gestion = row.get('CODE_GESTION_PRET') or ''
                charge_affaire = row.get('CHARGE_AFFAIRE') or '-'
                
                # Identifier le territoire - Priorité au code agence, puis au nom
                territory_name = None
                if branch_code:
                    territory_name = get_territory_from_branch_code(branch_code)
                
                # Si pas trouvé par code agence, essayer par nom
                if not territory_name:
                    territory_name = get_territory_from_agency(agency_name)
                
                territory_key = get_territory_key(territory_name) if territory_name else None
                
                # Vérifier si c'est le grand compte
                if agency_name.upper() in ['GRAND COMPTE', 'AGENCE GRAND COMPTE', 'GRAND COMPTES']:
                    if grand_compte is None:
                        grand_compte = {
                            'name': agency_name,
                            'BRANCH_CODE': '526',
                            'branch_code': '526',
                            'exigibleM1': 0,
                            'EXIGIBLE_M1': 0,
                            'exigibleS1': 0,
                            'EXIGIBLE_S1': 0,
                            'exigibleS2': 0,
                            'EXIGIBLE_S2': 0,
                            'exigibleS3': 0,
                            'EXIGIBLE_S3': 0,
                            'exigibleS4': 0,
                            'EXIGIBLE_S4': 0,
                            'SLD_M': 0,
                            'SLD_M_1': 0,
                            'SLD_S1': 0,
                            'sldS1': 0,
                            'SLD_S2': 0,
                            'sldS2': 0,
                            'SLD_S3': 0,
                            'sldS3': 0,
                            'SLD_S4': 0,
                            'sldS4': 0,
                            'MT_ECHEANCE': 0,
                            'mtEcheance': 0,
                            'M': 0,
                            'M_1': 0,
                            'S1': 0,
                            'S2': 0,
                            'S3': 0,
                            'S4': 0,
                            'MT_ECH_S1': 0,
                            'MT_ECH_S2': 0,
                            'MT_ECH_S3': 0,
                            'MT_ECH_S4': 0,
                            'COLLECTE_M': 0,
                            'COLLECTE_S1': 0,
                            'COLLECTE_S2': 0,
                            'COLLECTE_S3': 0,
                            'COLLECTE_S4': 0,
                            'CODE_GESTION': row.get('CODE_GESTION_PRET') or '-',
                            'CHARGE_AFFAIRE': row.get('CHARGE_AFFAIRE') or '-'
                        }
                    
                    # Agréger les données du grand compte
                    grand_compte['exigibleM1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                    grand_compte['EXIGIBLE_M1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                    grand_compte['exigibleS1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                    grand_compte['EXIGIBLE_S1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                    grand_compte['exigibleS2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                    grand_compte['EXIGIBLE_S2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                    grand_compte['exigibleS3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                    grand_compte['EXIGIBLE_S3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                    grand_compte['exigibleS4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                    grand_compte['EXIGIBLE_S4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                    grand_compte['SLD_M'] += float(row.get('SLD_M', 0) or 0)
                    grand_compte['SLD_M_1'] += float(row.get('SLD_M_1', 0) or 0)
                    grand_compte['SLD_S1'] += float(row.get('SLD_1', 0) or 0)
                    grand_compte['sldS1'] = grand_compte['SLD_S1']
                    grand_compte['SLD_S2'] += float(row.get('SLD_2', 0) or 0)
                    grand_compte['sldS2'] = grand_compte['SLD_S2']
                    grand_compte['SLD_S3'] += float(row.get('SLD_3', 0) or 0)
                    grand_compte['sldS3'] = grand_compte['SLD_S3']
                    grand_compte['SLD_S4'] += float(row.get('SLD_4', 0) or 0)
                    grand_compte['sldS4'] = grand_compte['SLD_S4']
                    grand_compte['MT_ECHEANCE'] += float(row.get('MT_ECH_M', 0) or 0)
                    grand_compte['mtEcheance'] += float(row.get('MT_ECH_M', 0) or 0)
                    grand_compte['M'] += float(row.get('M', 0) or 0)
                    grand_compte['M_1'] += float(row.get('M_1', 0) or 0)
                    grand_compte['S1'] += float(row.get('S1', 0) or 0)
                    grand_compte['S2'] += float(row.get('S2', 0) or 0)
                    grand_compte['S3'] += float(row.get('S3', 0) or 0)
                    grand_compte['S4'] += float(row.get('S4', 0) or 0)
                    grand_compte['MT_ECH_S1'] += float(row.get('MT_ECH_S1', 0) or 0)
                    grand_compte['MT_ECH_S2'] += float(row.get('MT_ECH_S2', 0) or 0)
                    grand_compte['MT_ECH_S3'] += float(row.get('MT_ECH_S3', 0) or 0)
                    grand_compte['MT_ECH_S4'] += float(row.get('MT_ECH_S4', 0) or 0)
                    
                    # Calculer les collectes selon les formules
                    # Collecte M = Etat depot M - (Exigible M-1 + Echeance S1)
                    exigible_m1 = grand_compte.get('EXIGIBLE_M1', 0) or grand_compte.get('exigibleM1', 0) or 0
                    mt_ech_s1 = grand_compte.get('MT_ECH_S1', 0) or 0
                    depot_m = grand_compte.get('M', 0) or 0
                    grand_compte['COLLECTE_M'] = depot_m - (exigible_m1 + mt_ech_s1)
                    
                    # Collecte S1 = Etat depot S1 - (Exigible M-1 + Montant Echeance S1)
                    depot_s1 = grand_compte.get('S1', 0) or 0
                    grand_compte['COLLECTE_S1'] = depot_s1 - (exigible_m1 + mt_ech_s1)
                    
                    # Collecte S2 = Etat depot S2 - (Exigible S-1 + Montant Echeance S2)
                    exigible_s1 = grand_compte.get('EXIGIBLE_S1', 0) or grand_compte.get('exigibleS1', 0) or 0
                    mt_ech_s2 = grand_compte.get('MT_ECH_S2', 0) or 0
                    depot_s2 = grand_compte.get('S2', 0) or 0
                    grand_compte['COLLECTE_S2'] = depot_s2 - (exigible_s1 + mt_ech_s2)
                    
                    # Collecte S3 = Etat depot S3 - (Exigible S-2 + Montant Echeance S3)
                    exigible_s2 = grand_compte.get('EXIGIBLE_S2', 0) or grand_compte.get('exigibleS2', 0) or 0
                    mt_ech_s3 = grand_compte.get('MT_ECH_S3', 0) or 0
                    depot_s3 = grand_compte.get('S3', 0) or 0
                    grand_compte['COLLECTE_S3'] = depot_s3 - (exigible_s2 + mt_ech_s3)
                    
                    # Collecte S4 = Etat depot S4 - (Exigible S-3 + Montant Echeance S4)
                    exigible_s3 = grand_compte.get('EXIGIBLE_S3', 0) or grand_compte.get('exigibleS3', 0) or 0
                    mt_ech_s4 = grand_compte.get('MT_ECH_S4', 0) or 0
                    depot_s4 = grand_compte.get('S4', 0) or 0
                    grand_compte['COLLECTE_S4'] = depot_s4 - (exigible_s3 + mt_ech_s4)
                    continue
                
                # Créer une clé unique pour l'agence basée sur BRANCH_CODE uniquement
                # pour regrouper tous les codes gestionnaires avec le même code agence
                agency_key = branch_code if branch_code else f"NO_CODE_{agency_name}"
                
                if agency_key not in agencies_data:
                    # Récupérer le code gestionnaire (prendre le premier non vide trouvé)
                    # Ne pas accepter les tirets ou valeurs vides
                    code_gestion_raw = row.get('CODE_GESTION_PRET') or ''
                    code_gestion = code_gestion_raw.strip() if code_gestion_raw and code_gestion_raw.strip() != '-' else ''
                    charge_affaire = row.get('CHARGE_AFFAIRE') or ''
                    
                    agencies_data[agency_key] = {
                    'name': agency_name,
                    'AGENCE': agency_name,
                    'BRANCH_CODE': branch_code,
                    'branch_code': branch_code,  # Version camelCase aussi
                    'AC_NO': ac_no,  # Garder pour référence mais ne pas utiliser comme clé unique
                    'ac_no': ac_no,  # Version camelCase aussi
                    'codeGestion': code_gestion,
                    'CODE_GESTION': code_gestion,
                    'codeGestionList': [],  # Initialiser la liste des codes gestionnaires
                    'CODE_GESTION_LIST': [],
                    'chargeAffaire': charge_affaire,
                    'CHARGE_AFFAIRE': charge_affaire,
                    'chargeAffaireList': [],  # Initialiser la liste des chargés d'affaire
                    'CHARGE_AFFAIRE_LIST': [],
                    'exigibleM1': 0,
                    'EXIGIBLE_M1': 0,
                    'exigibleS1': 0,
                    'EXIGIBLE_S1': 0,
                    'exigibleS2': 0,
                    'EXIGIBLE_S2': 0,
                    'exigibleS3': 0,
                    'EXIGIBLE_S3': 0,
                    'exigibleS4': 0,
                    'EXIGIBLE_S4': 0,
                    'SLD_M': 0,
                    'SLD_M_1': 0,
                    'SLD_S1': 0,
                    'sldS1': 0,
                    'SLD_S2': 0,
                    'sldS2': 0,
                    'SLD_S3': 0,
                    'sldS3': 0,
                    'SLD_S4': 0,
                    'sldS4': 0,
                    'MT_ECHEANCE': 0,
                    'mtEcheance': 0,
                    'M': 0,
                    'M_1': 0,
                    'S1': 0,
                    'S2': 0,
                    'S3': 0,
                    'S4': 0,
                    'MT_ECH_S1': 0,
                    'MT_ECH_S2': 0,
                    'MT_ECH_S3': 0,
                    'MT_ECH_S4': 0,
                    'COLLECTE_M': 0,
                    'COLLECTE_S1': 0,
                    'COLLECTE_S2': 0,
                        'COLLECTE_S3': 0,
                        'COLLECTE_S4': 0
                    }
                
                # Agréger les données
                agencies_data[agency_key]['exigibleM1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                agencies_data[agency_key]['EXIGIBLE_M1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                agencies_data[agency_key]['exigibleS1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                agencies_data[agency_key]['EXIGIBLE_S1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                agencies_data[agency_key]['exigibleS2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                agencies_data[agency_key]['EXIGIBLE_S2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                agencies_data[agency_key]['exigibleS3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                agencies_data[agency_key]['EXIGIBLE_S3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                agencies_data[agency_key]['exigibleS4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                agencies_data[agency_key]['EXIGIBLE_S4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                agencies_data[agency_key]['SLD_M'] += float(row.get('SLD_M', 0) or 0)
                agencies_data[agency_key]['SLD_M_1'] += float(row.get('SLD_M_1', 0) or 0)
                agencies_data[agency_key]['SLD_S1'] += float(row.get('SLD_1', 0) or 0)
                agencies_data[agency_key]['sldS1'] = agencies_data[agency_key]['SLD_S1']
                agencies_data[agency_key]['SLD_S2'] += float(row.get('SLD_2', 0) or 0)
                agencies_data[agency_key]['sldS2'] = agencies_data[agency_key]['SLD_S2']
                agencies_data[agency_key]['SLD_S3'] += float(row.get('SLD_3', 0) or 0)
                agencies_data[agency_key]['sldS3'] = agencies_data[agency_key]['SLD_S3']
                agencies_data[agency_key]['SLD_S4'] += float(row.get('SLD_4', 0) or 0)
                agencies_data[agency_key]['sldS4'] = agencies_data[agency_key]['SLD_S4']
                agencies_data[agency_key]['MT_ECHEANCE'] += float(row.get('MT_ECH_M', 0) or 0)
                agencies_data[agency_key]['mtEcheance'] += float(row.get('MT_ECH_M', 0) or 0)
                agencies_data[agency_key]['M'] += float(row.get('M', 0) or 0)
                agencies_data[agency_key]['M_1'] += float(row.get('M_1', 0) or 0)
                agencies_data[agency_key]['S1'] += float(row.get('S1', 0) or 0)
                agencies_data[agency_key]['S2'] += float(row.get('S2', 0) or 0)
                agencies_data[agency_key]['S3'] += float(row.get('S3', 0) or 0)
                agencies_data[agency_key]['S4'] += float(row.get('S4', 0) or 0)
                agencies_data[agency_key]['MT_ECH_S1'] += float(row.get('MT_ECH_S1', 0) or 0)
                agencies_data[agency_key]['MT_ECH_S2'] += float(row.get('MT_ECH_S2', 0) or 0)
                agencies_data[agency_key]['MT_ECH_S3'] += float(row.get('MT_ECH_S3', 0) or 0)
                agencies_data[agency_key]['MT_ECH_S4'] += float(row.get('MT_ECH_S4', 0) or 0)
                
                # Collecter tous les codes gestionnaires uniques pour cette agence (même BRANCH_CODE)
                code_gestion_from_row = row.get('CODE_GESTION_PRET') or ''
                if code_gestion_from_row and code_gestion_from_row.strip() != '' and code_gestion_from_row.strip() != '-':
                    code_gestion_clean = code_gestion_from_row.strip()
                    # S'assurer que la liste existe
                    if 'codeGestionList' not in agencies_data[agency_key]:
                        agencies_data[agency_key]['codeGestionList'] = []
                        agencies_data[agency_key]['CODE_GESTION_LIST'] = []
                    # Ajouter le code gestionnaire s'il n'est pas déjà dans la liste
                    if code_gestion_clean not in agencies_data[agency_key]['codeGestionList']:
                        agencies_data[agency_key]['codeGestionList'].append(code_gestion_clean)
                        agencies_data[agency_key]['CODE_GESTION_LIST'].append(code_gestion_clean)
                    
                    # Mettre à jour le code gestionnaire principal (prendre le premier non vide)
                    if not agencies_data[agency_key].get('codeGestion') or agencies_data[agency_key].get('codeGestion') == '' or agencies_data[agency_key].get('codeGestion') == '-':
                        agencies_data[agency_key]['codeGestion'] = code_gestion_clean
                        agencies_data[agency_key]['CODE_GESTION'] = code_gestion_clean
                
                # Collecter tous les chargés d'affaire uniques pour cette agence (même BRANCH_CODE)
                charge_affaire_from_row = row.get('CHARGE_AFFAIRE') or ''
                if charge_affaire_from_row and charge_affaire_from_row.strip() != '' and charge_affaire_from_row.strip() != '-':
                    charge_affaire_clean = charge_affaire_from_row.strip()
                    # S'assurer que la liste existe
                    if 'chargeAffaireList' not in agencies_data[agency_key]:
                        agencies_data[agency_key]['chargeAffaireList'] = []
                        agencies_data[agency_key]['CHARGE_AFFAIRE_LIST'] = []
                    # Ajouter le chargé d'affaire s'il n'est pas déjà dans la liste
                    if charge_affaire_clean not in agencies_data[agency_key]['chargeAffaireList']:
                        agencies_data[agency_key]['chargeAffaireList'].append(charge_affaire_clean)
                        agencies_data[agency_key]['CHARGE_AFFAIRE_LIST'].append(charge_affaire_clean)
                    
                    # Mettre à jour le chargé d'affaire principal (prendre le premier non vide)
                    if not agencies_data[agency_key].get('chargeAffaire') or agencies_data[agency_key].get('chargeAffaire') == '':
                        agencies_data[agency_key]['chargeAffaire'] = charge_affaire_clean
                        agencies_data[agency_key]['CHARGE_AFFAIRE'] = charge_affaire_clean
                
                # Regrouper les données par chargé d'affaire pour cette agence
                charge_affaire_key = f"{code_gestion}_{charge_affaire}" if code_gestion or charge_affaire != '-' else f"NO_CHARGE_{ac_no}"
                
                if agency_key not in charge_affaire_data:
                    charge_affaire_data[agency_key] = {}
                
                if charge_affaire_key not in charge_affaire_data[agency_key]:
                    charge_affaire_data[agency_key][charge_affaire_key] = {
                    'BRANCH_CODE': branch_code,
                    'branch_code': branch_code,
                    'name': agency_name,
                    'AGENCE': agency_name,
                    'codeGestion': code_gestion,
                    'CODE_GESTION': code_gestion,
                    'chargeAffaire': charge_affaire,
                    'CHARGE_AFFAIRE': charge_affaire,
                    'exigibleM1': 0,
                    'EXIGIBLE_M1': 0,
                    'exigibleS1': 0,
                    'EXIGIBLE_S1': 0,
                    'exigibleS2': 0,
                    'EXIGIBLE_S2': 0,
                    'exigibleS3': 0,
                    'EXIGIBLE_S3': 0,
                    'exigibleS4': 0,
                    'EXIGIBLE_S4': 0,
                    'SLD_M': 0,
                    'SLD_M_1': 0,
                    'SLD_S1': 0,
                    'sldS1': 0,
                    'SLD_S2': 0,
                    'sldS2': 0,
                    'SLD_S3': 0,
                    'sldS3': 0,
                    'SLD_S4': 0,
                    'sldS4': 0,
                    'MT_ECHEANCE': 0,
                    'mtEcheance': 0,
                    'M': 0,
                    'M_1': 0,
                    'S1': 0,
                    'S2': 0,
                    'S3': 0,
                    'S4': 0,
                    'MT_ECH_S1': 0,
                    'MT_ECH_S2': 0,
                    'MT_ECH_S3': 0,
                    'MT_ECH_S4': 0,
                    'COLLECTE_M': 0,
                    'COLLECTE_S1': 0,
                    'COLLECTE_S2': 0,
                        'COLLECTE_S3': 0,
                        'COLLECTE_S4': 0
                    }
                
                # Agréger les données par chargé d'affaire
                charge_affaire_data[agency_key][charge_affaire_key]['exigibleM1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['EXIGIBLE_M1'] += float(row.get('EXIGIBLE_M_1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['exigibleS1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['EXIGIBLE_S1'] += float(row.get('EXIGIBLE_S1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['exigibleS2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['EXIGIBLE_S2'] += float(row.get('EXIGIBLE_S2', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['exigibleS3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['EXIGIBLE_S3'] += float(row.get('EXIGIBLE_S3', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['exigibleS4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['EXIGIBLE_S4'] += float(row.get('EXIGIBLE_S4', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_M'] += float(row.get('SLD_M', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_M_1'] += float(row.get('SLD_M_1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_S1'] += float(row.get('SLD_1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['sldS1'] = charge_affaire_data[agency_key][charge_affaire_key]['SLD_S1']
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_S2'] += float(row.get('SLD_2', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['sldS2'] = charge_affaire_data[agency_key][charge_affaire_key]['SLD_S2']
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_S3'] += float(row.get('SLD_3', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['sldS3'] = charge_affaire_data[agency_key][charge_affaire_key]['SLD_S3']
                charge_affaire_data[agency_key][charge_affaire_key]['SLD_S4'] += float(row.get('SLD_4', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['sldS4'] = charge_affaire_data[agency_key][charge_affaire_key]['SLD_S4']
                charge_affaire_data[agency_key][charge_affaire_key]['MT_ECHEANCE'] += float(row.get('MT_ECH_M', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['mtEcheance'] += float(row.get('MT_ECH_M', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['M'] += float(row.get('M', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['M_1'] += float(row.get('M_1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['S1'] += float(row.get('S1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['S2'] += float(row.get('S2', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['S3'] += float(row.get('S3', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['S4'] += float(row.get('S4', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['MT_ECH_S1'] += float(row.get('MT_ECH_S1', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['MT_ECH_S2'] += float(row.get('MT_ECH_S2', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['MT_ECH_S3'] += float(row.get('MT_ECH_S3', 0) or 0)
                charge_affaire_data[agency_key][charge_affaire_key]['MT_ECH_S4'] += float(row.get('MT_ECH_S4', 0) or 0)
                
                # Calculer les collectes selon les formules (après agrégation de toutes les lignes)
                # Les calculs seront faits après la boucle pour utiliser les valeurs agrégées
                
                # Note: Les agences seront ajoutées aux territoires dans la section de distribution ci-dessous
                # pour éviter les doublons et s'assurer que seules les agences correctement mappées sont incluses
            
            # Distribuer les agences dans les territoires
            logger.info(f"📊 Distribution de {len(agencies_data)} agences dans les territoires...")
            
            # Nettoyer d'abord les listes d'agences pour éviter les doublons
            for territory_key in agencies_by_territory.keys():
                agencies_by_territory[territory_key] = []
            
            agencies_mapped = 0
            agencies_unmapped = 0
            agencies_filtered = 0
            unmapped_agencies = []
            for agency_key, agency in agencies_data.items():
                # Ignorer le grand compte (il sera ajouté séparément)
                # Vérifier par nom et par BRANCH_CODE 526
                agency_name_upper = agency.get('name', '').upper()
                branch_code = agency.get('BRANCH_CODE') or agency.get('branch_code') or ''
                if (agency_name_upper in ['GRAND COMPTE', 'AGENCE GRAND COMPTE', 'GRAND COMPTES'] or 
                    branch_code == '526'):
                    logger.debug(f"⚠️ Grand compte exclu de la distribution: {branch_code} - {agency.get('name')}")
                    continue
                
                # Filtrer les agences sans code gestionnaire
                code_gestion = agency.get('codeGestion') or agency.get('CODE_GESTION') or ''
                # Vérifier aussi que ce n'est pas juste un tiret ou un caractère vide
                if not code_gestion or code_gestion.strip() == '' or code_gestion.strip() == '-':
                    agencies_filtered += 1
                    logger.debug(f"⚠️ Agence filtrée (pas de code gestionnaire): {agency.get('BRANCH_CODE')} - {agency.get('name')} - code: '{code_gestion}'")
                    continue
                
                # Identifier le territoire - Priorité au code agence, puis au nom
                branch_code = agency.get('BRANCH_CODE') or agency.get('branch_code') or ''
                territory_name = None
                if branch_code:
                    territory_name = get_territory_from_branch_code(branch_code)
                
                # Si pas trouvé par code agence, essayer par nom
                if not territory_name:
                    territory_name = get_territory_from_agency(agency.get('name') or agency.get('AGENCE') or '')
                
                territory_key = get_territory_key(territory_name) if territory_name else None
                if territory_key and territory_key in agencies_by_territory:
                    # Regrouper par BRANCH_CODE uniquement - une seule entrée par code agence
                    # Vérifier si une agence avec le même BRANCH_CODE existe déjà
                    agency_exists = any(
                        existing_agency.get('BRANCH_CODE') == agency.get('BRANCH_CODE')
                        for existing_agency in agencies_by_territory[territory_key]
                    )
                    if not agency_exists:
                        agencies_by_territory[territory_key].append(agency)
                        agencies_mapped += 1
                    else:
                        logger.debug(f"⚠️ Agence déjà présente dans {territory_key}: {agency.get('BRANCH_CODE')} - {agency.get('name')}")
                else:
                    agencies_unmapped += 1
                    if len(unmapped_agencies) < 10:
                        unmapped_agencies.append(agency.get('name', agency_key))
        
            logger.info(f"✅ {agencies_mapped} agences mappées, {agencies_unmapped} non mappées, {agencies_filtered} filtrées (sans code gestionnaire)")
            if unmapped_agencies:
                logger.warning(f"⚠️ Agences non mappées (ne seront pas affichées): {unmapped_agencies[:10]}")
            
            # Filtrer une dernière fois toutes les agences sans code gestionnaire valide dans chaque territoire
            total_filtered_final = 0
            for territory_key in agencies_by_territory.keys():
                original_count = len(agencies_by_territory[territory_key])
                agencies_by_territory[territory_key] = [
                    agency for agency in agencies_by_territory[territory_key]
                    if (agency.get('codeGestion') or agency.get('CODE_GESTION') or '').strip() not in ['', '-', None]
                ]
                filtered_count = original_count - len(agencies_by_territory[territory_key])
                total_filtered_final += filtered_count
                if filtered_count > 0:
                    logger.info(f"🔍 Territoire {territory_key}: {filtered_count} agences supplémentaires filtrées (sans code gestionnaire)")
            
            if total_filtered_final > 0:
                logger.info(f"🔍 Filtre final: {total_filtered_final} agences supplémentaires exclues (sans code gestionnaire valide)")
            
            # Calculer les collectes pour chaque chargé d'affaire après agrégation
            for agency_key, charges in charge_affaire_data.items():
                for charge_key, charge_data in charges.items():
                    # Collecte M = Etat depot M - (Exigible M-1 + Echeance S1)
                    exigible_m1 = charge_data.get('EXIGIBLE_M1', 0) or charge_data.get('exigibleM1', 0) or 0
                    mt_ech_s1 = charge_data.get('MT_ECH_S1', 0) or 0
                    depot_m = charge_data.get('M', 0) or 0
                    collecte_m = max(0, depot_m - (exigible_m1 + mt_ech_s1))
                    charge_data['COLLECTE_M'] = collecte_m
                    charge_data['collecteM'] = collecte_m
                    
                    # Collecte S1 = Etat depot S1 - (Exigible M-1 + Montant Echeance S1)
                    depot_s1 = charge_data.get('S1', 0) or 0
                    collecte_s1 = max(0, depot_s1 - (exigible_m1 + mt_ech_s1))
                    charge_data['COLLECTE_S1'] = collecte_s1
                    charge_data['collecteS1'] = collecte_s1
                    
                    # Collecte S2 = Etat depot S2 - (Exigible S-1 + Montant Echeance S2)
                    exigible_s1 = charge_data.get('EXIGIBLE_S1', 0) or charge_data.get('exigibleS1', 0) or 0
                    mt_ech_s2 = charge_data.get('MT_ECH_S2', 0) or 0
                    depot_s2 = charge_data.get('S2', 0) or 0
                    collecte_s2 = max(0, depot_s2 - (exigible_s1 + mt_ech_s2))
                    charge_data['COLLECTE_S2'] = collecte_s2
                    charge_data['collecteS2'] = collecte_s2
                    
                    # Collecte S3 = Etat depot S3 - (Exigible S-2 + Montant Echeance S3)
                    exigible_s2 = charge_data.get('EXIGIBLE_S2', 0) or charge_data.get('exigibleS2', 0) or 0
                    mt_ech_s3 = charge_data.get('MT_ECH_S3', 0) or 0
                    depot_s3 = charge_data.get('S3', 0) or 0
                    collecte_s3 = max(0, depot_s3 - (exigible_s2 + mt_ech_s3))
                    charge_data['COLLECTE_S3'] = collecte_s3
                    charge_data['collecteS3'] = collecte_s3
                    
                    # Collecte S4 = Etat depot S4 - (Exigible S-3 + Montant Echeance S4)
                    exigible_s3 = charge_data.get('EXIGIBLE_S3', 0) or charge_data.get('exigibleS3', 0) or 0
                    mt_ech_s4 = charge_data.get('MT_ECH_S4', 0) or 0
                    depot_s4 = charge_data.get('S4', 0) or 0
                    collecte_s4 = max(0, depot_s4 - (exigible_s3 + mt_ech_s4))
                    charge_data['COLLECTE_S4'] = collecte_s4
                    charge_data['collecteS4'] = collecte_s4
            
            # Calculer les collectes pour chaque agence après agrégation
            for agency_key, agency in agencies_data.items():
                # Collecte M = Etat depot M - (Exigible M-1 + Echeance S1)
                exigible_m1 = agency.get('EXIGIBLE_M1', 0) or agency.get('exigibleM1', 0) or 0
                mt_ech_s1 = agency.get('MT_ECH_S1', 0) or 0
                depot_m = agency.get('M', 0) or 0
                collecte_m = max(0, depot_m - (exigible_m1 + mt_ech_s1))  # Remplacer les valeurs négatives par 0
                agency['COLLECTE_M'] = collecte_m
                agency['collecteM'] = collecte_m
                
                # Collecte S1 = Etat depot S1 - (Exigible M-1 + Montant Echeance S1)
                depot_s1 = agency.get('S1', 0) or 0
                collecte_s1 = max(0, depot_s1 - (exigible_m1 + mt_ech_s1))  # Remplacer les valeurs négatives par 0
                agency['COLLECTE_S1'] = collecte_s1
                agency['collecteS1'] = collecte_s1
                
                # Collecte S2 = Etat depot S2 - (Exigible S-1 + Montant Echeance S2)
                exigible_s1 = agency.get('EXIGIBLE_S1', 0) or agency.get('exigibleS1', 0) or 0
                mt_ech_s2 = agency.get('MT_ECH_S2', 0) or 0
                depot_s2 = agency.get('S2', 0) or 0
                collecte_s2 = max(0, depot_s2 - (exigible_s1 + mt_ech_s2))  # Remplacer les valeurs négatives par 0
                agency['COLLECTE_S2'] = collecte_s2
                agency['collecteS2'] = collecte_s2
                
                # Collecte S3 = Etat depot S3 - (Exigible S-2 + Montant Echeance S3)
                exigible_s2 = agency.get('EXIGIBLE_S2', 0) or agency.get('exigibleS2', 0) or 0
                mt_ech_s3 = agency.get('MT_ECH_S3', 0) or 0
                depot_s3 = agency.get('S3', 0) or 0
                collecte_s3 = max(0, depot_s3 - (exigible_s2 + mt_ech_s3))  # Remplacer les valeurs négatives par 0
                agency['COLLECTE_S3'] = collecte_s3
                agency['collecteS3'] = collecte_s3
                
                # Collecte S4 = Etat depot S4 - (Exigible S-3 + Montant Echeance S4)
                exigible_s3 = agency.get('EXIGIBLE_S3', 0) or agency.get('exigibleS3', 0) or 0
                mt_ech_s4 = agency.get('MT_ECH_S4', 0) or 0
                depot_s4 = agency.get('S4', 0) or 0
                collecte_s4 = max(0, depot_s4 - (exigible_s3 + mt_ech_s4))  # Remplacer les valeurs négatives par 0
                agency['COLLECTE_S4'] = collecte_s4
                agency['collecteS4'] = collecte_s4
            
            # Calculer les collectes pour le grand compte
            if grand_compte:
                # Collecte M = Etat depot M - (Exigible M-1 + Echeance S1)
                exigible_m1 = grand_compte.get('EXIGIBLE_M1', 0) or grand_compte.get('exigibleM1', 0) or 0
                mt_ech_s1 = grand_compte.get('MT_ECH_S1', 0) or 0
                depot_m = grand_compte.get('M', 0) or 0
                collecte_m = max(0, depot_m - (exigible_m1 + mt_ech_s1))  # Remplacer les valeurs négatives par 0
                grand_compte['COLLECTE_M'] = collecte_m
                grand_compte['collecteM'] = collecte_m
                
                # Collecte S1 = Etat depot S1 - (Exigible M-1 + Montant Echeance S1)
                depot_s1 = grand_compte.get('S1', 0) or 0
                collecte_s1 = max(0, depot_s1 - (exigible_m1 + mt_ech_s1))  # Remplacer les valeurs négatives par 0
                grand_compte['COLLECTE_S1'] = collecte_s1
                grand_compte['collecteS1'] = collecte_s1
                
                # Collecte S2 = Etat depot S2 - (Exigible S-1 + Montant Echeance S2)
                exigible_s1 = grand_compte.get('EXIGIBLE_S1', 0) or grand_compte.get('exigibleS1', 0) or 0
                mt_ech_s2 = grand_compte.get('MT_ECH_S2', 0) or 0
                depot_s2 = grand_compte.get('S2', 0) or 0
                collecte_s2 = max(0, depot_s2 - (exigible_s1 + mt_ech_s2))  # Remplacer les valeurs négatives par 0
                grand_compte['COLLECTE_S2'] = collecte_s2
                grand_compte['collecteS2'] = collecte_s2
                
                # Collecte S3 = Etat depot S3 - (Exigible S-2 + Montant Echeance S3)
                exigible_s2 = grand_compte.get('EXIGIBLE_S2', 0) or grand_compte.get('exigibleS2', 0) or 0
                mt_ech_s3 = grand_compte.get('MT_ECH_S3', 0) or 0
                depot_s3 = grand_compte.get('S3', 0) or 0
                collecte_s3 = max(0, depot_s3 - (exigible_s2 + mt_ech_s3))  # Remplacer les valeurs négatives par 0
                grand_compte['COLLECTE_S3'] = collecte_s3
                grand_compte['collecteS3'] = collecte_s3
                
                # Collecte S4 = Etat depot S4 - (Exigible S-3 + Montant Echeance S4)
                exigible_s3 = grand_compte.get('EXIGIBLE_S3', 0) or grand_compte.get('exigibleS3', 0) or 0
                mt_ech_s4 = grand_compte.get('MT_ECH_S4', 0) or 0
                depot_s4 = grand_compte.get('S4', 0) or 0
                collecte_s4 = max(0, depot_s4 - (exigible_s3 + mt_ech_s4))  # Remplacer les valeurs négatives par 0
                grand_compte['COLLECTE_S4'] = collecte_s4
                grand_compte['collecteS4'] = collecte_s4
            
            # Calculer les totaux globaux
            total_exigible = sum(ag.get('exigibleM1', 0) for ag in agencies_data.values())
            
            # Calculer les totaux pour chaque territoire
            def calculate_territory_totals(agencies_list):
                """Calcule les totaux pour un territoire à partir de sa liste d'agences"""
                totals = {
                'exigibleM1': 0,
                'EXIGIBLE_M1': 0,
                'exigibleS1': 0,
                'EXIGIBLE_S1': 0,
                'exigibleS2': 0,
                'EXIGIBLE_S2': 0,
                'exigibleS3': 0,
                'EXIGIBLE_S3': 0,
                'exigibleS4': 0,
                'EXIGIBLE_S4': 0,
                'sldM': 0,
                'SLD_M': 0,
                'sldM1': 0,
                'SLD_M_1': 0,
                'sldS1': 0,
                'SLD_S1': 0,
                'sldS2': 0,
                'SLD_S2': 0,
                'sldS3': 0,
                'SLD_S3': 0,
                'sldS4': 0,
                'SLD_S4': 0,
                'mtEcheance': 0,
                'MT_ECHEANCE': 0,
                'collecteM': 0,
                'COLLECTE_M': 0,
                'collecteS1': 0,
                'COLLECTE_S1': 0,
                'collecteS2': 0,
                'COLLECTE_S2': 0,
                'collecteS3': 0,
                'COLLECTE_S3': 0,
                'collecteS4': 0,
                'COLLECTE_S4': 0,
                'm': 0,
                'M': 0,
                'mS1': 0,
                'M_S1': 0,
                'sldM': 0,
                    'SLD_M': 0
                }
                for agency in agencies_list:
                    totals['exigibleM1'] += agency.get('exigibleM1', 0) or agency.get('EXIGIBLE_M1', 0) or 0
                    totals['EXIGIBLE_M1'] += agency.get('EXIGIBLE_M1', 0) or agency.get('exigibleM1', 0) or 0
                    totals['exigibleS1'] += agency.get('exigibleS1', 0) or agency.get('EXIGIBLE_S1', 0) or 0
                    totals['EXIGIBLE_S1'] += agency.get('EXIGIBLE_S1', 0) or agency.get('exigibleS1', 0) or 0
                    totals['exigibleS2'] += agency.get('exigibleS2', 0) or agency.get('EXIGIBLE_S2', 0) or 0
                    totals['EXIGIBLE_S2'] += agency.get('EXIGIBLE_S2', 0) or agency.get('exigibleS2', 0) or 0
                    totals['exigibleS3'] += agency.get('exigibleS3', 0) or agency.get('EXIGIBLE_S3', 0) or 0
                    totals['EXIGIBLE_S3'] += agency.get('EXIGIBLE_S3', 0) or agency.get('exigibleS3', 0) or 0
                    totals['exigibleS4'] += agency.get('exigibleS4', 0) or agency.get('EXIGIBLE_S4', 0) or 0
                    totals['EXIGIBLE_S4'] += agency.get('EXIGIBLE_S4', 0) or agency.get('exigibleS4', 0) or 0
                    totals['sldM'] += agency.get('sldM', 0) or agency.get('SLD_M', 0) or 0
                    totals['SLD_M'] += agency.get('SLD_M', 0) or agency.get('sldM', 0) or 0
                    totals['sldM1'] += agency.get('sldM1', 0) or agency.get('SLD_M_1', 0) or 0
                    totals['SLD_M_1'] += agency.get('SLD_M_1', 0) or agency.get('sldM1', 0) or 0
                    totals['sldS1'] += agency.get('sldS1', 0) or agency.get('SLD_S1', 0) or 0
                    totals['SLD_S1'] += agency.get('SLD_S1', 0) or agency.get('sldS1', 0) or 0
                    totals['sldS2'] += agency.get('sldS2', 0) or agency.get('SLD_S2', 0) or 0
                    totals['SLD_S2'] += agency.get('SLD_S2', 0) or agency.get('sldS2', 0) or 0
                    totals['sldS3'] += agency.get('sldS3', 0) or agency.get('SLD_S3', 0) or 0
                    totals['SLD_S3'] += agency.get('SLD_S3', 0) or agency.get('sldS3', 0) or 0
                    totals['sldS4'] += agency.get('sldS4', 0) or agency.get('SLD_S4', 0) or 0
                    totals['SLD_S4'] += agency.get('SLD_S4', 0) or agency.get('sldS4', 0) or 0
                    totals['mtEcheance'] += agency.get('mtEcheance', 0) or agency.get('MT_ECHEANCE', 0) or 0
                    totals['MT_ECHEANCE'] += agency.get('MT_ECHEANCE', 0) or agency.get('mtEcheance', 0) or 0
                    totals['collecteM'] += agency.get('collecteM', 0) or agency.get('COLLECTE_M', 0) or 0
                    totals['COLLECTE_M'] += agency.get('COLLECTE_M', 0) or agency.get('collecteM', 0) or 0
                    totals['collecteS1'] += agency.get('collecteS1', 0) or agency.get('COLLECTE_S1', 0) or 0
                    totals['COLLECTE_S1'] += agency.get('COLLECTE_S1', 0) or agency.get('collecteS1', 0) or 0
                    totals['collecteS2'] += agency.get('collecteS2', 0) or agency.get('COLLECTE_S2', 0) or 0
                    totals['COLLECTE_S2'] += agency.get('COLLECTE_S2', 0) or agency.get('collecteS2', 0) or 0
                    totals['collecteS3'] += agency.get('collecteS3', 0) or agency.get('COLLECTE_S3', 0) or 0
                    totals['COLLECTE_S3'] += agency.get('COLLECTE_S3', 0) or agency.get('collecteS3', 0) or 0
                    totals['collecteS4'] += agency.get('collecteS4', 0) or agency.get('COLLECTE_S4', 0) or 0
                    totals['COLLECTE_S4'] += agency.get('COLLECTE_S4', 0) or agency.get('collecteS4', 0) or 0
                return totals
            
            # Construire la réponse avec les clés attendues par le frontend
            response_data = {
                "globalResult": {
                    "exigibleJ1": total_exigible,
                    "montantARecouvrer": total_exigible
                },
                "hierarchicalData": {
                    "TERRITOIRE": {
                        "dakar_centre_ville": {
                            "name": "DAKAR CENTRE VILLE",
                            "agencies": agencies_by_territory['territoire_dakar_ville'],
                            "totals": calculate_territory_totals(agencies_by_territory['territoire_dakar_ville'])
                        },
                        "dakar_banlieue": {
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
                }
            }
            
            # Ajouter le grand compte si disponible
            if grand_compte:
                response_data["grandCompte"] = grand_compte
            
            # Ajouter les données par chargé d'affaire pour chaque agence
            charge_affaire_by_agency = {}
            for agency_key, charges in charge_affaire_data.items():
                # Convertir le dictionnaire en liste pour faciliter l'accès dans le frontend
                charge_affaire_by_agency[agency_key] = list(charges.values())
            
            response_data["chargeAffaireDetails"] = charge_affaire_by_agency
            logger.info(f"📊 chargeAffaireDetails: {len(charge_affaire_by_agency)} agences avec détails par chargé d'affaire")
            if len(charge_affaire_by_agency) > 0:
                sample_key = list(charge_affaire_by_agency.keys())[0]
                logger.info(f"📊 Exemple clé agence: {sample_key}, nombre de chargés d'affaire: {len(charge_affaire_by_agency[sample_key])}")
            
            # Log pour vérifier les collectes
            if len(agencies_data) > 0:
                sample_agency = list(agencies_data.values())[0]
                logger.info(f"🔍 Exemple d'agence avec collectes: {sample_agency.get('name')}")
                logger.info(f"   COLLECTE_M={sample_agency.get('COLLECTE_M')}, collecteM={sample_agency.get('collecteM')}")
                logger.info(f"   COLLECTE_S1={sample_agency.get('COLLECTE_S1')}, collecteS1={sample_agency.get('collecteS1')}")
                logger.info(f"   M={sample_agency.get('M')}, EXIGIBLE_M1={sample_agency.get('EXIGIBLE_M1')}, MT_ECH_S1={sample_agency.get('MT_ECH_S1')}")
                
                # Vérifier les totaux d'un territoire
                if agencies_by_territory['territoire_dakar_ville']:
                    territory_totals = calculate_territory_totals(agencies_by_territory['territoire_dakar_ville'])
                    logger.info(f"🔍 Totaux territoire DAKAR CENTRE VILLE:")
                    logger.info(f"   collecteM={territory_totals.get('collecteM')}, COLLECTE_M={territory_totals.get('COLLECTE_M')}")
                    logger.info(f"   collecteS1={territory_totals.get('collecteS1')}, COLLECTE_S1={territory_totals.get('COLLECTE_S1')}")
            
            if grand_compte:
                logger.info(f"🔍 Grand compte collectes: COLLECTE_M={grand_compte.get('COLLECTE_M')}, collecteM={grand_compte.get('collecteM')}")
            
            # Mettre en cache le résultat (TTL de 5 minutes pour les données de collection)
            set_cache(cache_key, response_data, ttl=300)
            
            logger.info(f"✅ Données de collection récupérées: {len(agencies_data)} agences")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données de collection: {str(e)}", exc_info=True)
            raise
