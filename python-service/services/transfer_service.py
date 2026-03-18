"""
Service pour la gestion des données de transferts d'argent
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection

logger = logging.getLogger(__name__)


def get_orange_money_data(month: int, year: int) -> List[Dict]:
    """
    Récupère les données Orange Money (envois et paiements) depuis Oracle
    
    Args:
        month: Mois (1-12)
        year: Année
        
    Returns:
        Liste de dictionnaires avec les données par agence
    """
    logger.info(f"📅 get_orange_money_data appelé avec month={month}, year={year}")
    dates = calculate_month_dates(month, year)
    logger.info(f"📅 Dates calculées pour Orange Money: M={dates['m_debut']} à {dates['m_fin']}, M-1={dates['m1_debut']} à {dates['m1_fin']}")
    conn = get_oracle_connection()
    cursor = conn.cursor()
    
    try:
        # Requête ultra-optimisée combinant envois et paiements en une seule requête
        # Conversion des dates pour comparaison directe (plus rapide que TO_CHAR)
        m1_debut_date = datetime.strptime(dates['m1_debut'], '%d/%m/%Y')
        m_fin_date = datetime.strptime(dates['m_fin'], '%d/%m/%Y')
        m_debut_date = datetime.strptime(dates['m_debut'], '%d/%m/%Y')
        m1_fin_date = datetime.strptime(dates['m1_fin'], '%d/%m/%Y')
        
        logger.info(f"📅 Dates pour requête Orange Money:")
        logger.info(f"   M1 début: {m1_debut_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M fin: {m_fin_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M début: {m_debut_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M1 fin: {m1_fin_date.strftime('%d/%m/%Y')}")
        
        combined_query = f"""
        WITH Journal AS (
            SELECT
                AC_BRANCH, AC_NO, DRCR_IND, LCY_AMOUNT, 
                COALESCE(VALUE_DT, TRN_DT) as TRN_DT
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES 
            WHERE COALESCE(VALUE_DT, TRN_DT) >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY') 
              AND COALESCE(VALUE_DT, TRN_DT) <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
        ),
        RESUL_OM as (
            select 
                   nvl(c.gl_code,s.DR_GL) "PARENT_GL"
                   ,a.ac_branch as CODE_AGENCE
                   ,a.drcr_ind as SENS_ECR
                   ,b.branch_name as LIBELLE_AGENCE
                   ,a.lcy_amount
                   ,a.TRN_DT
            from Journal a
                   LEFT JOIN CFSFCUBS145.gltm_glmaster c ON c.gl_code = a.AC_NO
                   LEFT JOIN CFSFCUBS145.STTM_CUST_ACCOUNT s ON s.CUST_AC_NO = a.AC_NO
                   LEFT JOIN CFSFCUBS145.STTM_BRANCH b ON b.branch_code = a.ac_branch
            where nvl(c.gl_code,s.DR_GL) like '101%'
        ),
        ENVOIE_OM_M as (
            select 
                OM.CODE_AGENCE,
                OM.LIBELLE_AGENCE,
                sum(OM.lcy_amount) as VOLUME_ENVOIE_OM_M
            from  RESUL_OM OM
            where OM.TRN_DT >= TO_DATE('{m_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and OM.TRN_DT <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and OM.SENS_ECR='D'
            group by OM.CODE_AGENCE, OM.LIBELLE_AGENCE
        ),
        ENVOIE_OM_M_1 as (
            select 
                OM1.CODE_AGENCE,
                OM1.LIBELLE_AGENCE,
                sum(OM1.lcy_amount) as VOLUME_ENVOIE_OM_M_1
            from  RESUL_OM OM1
            where OM1.TRN_DT >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and OM1.TRN_DT <= TO_DATE('{m1_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and OM1.SENS_ECR='D'
            group by OM1.CODE_AGENCE, OM1.LIBELLE_AGENCE
        ),
        PAIEMENT_OM_M as (
            select 
                OM.CODE_AGENCE,
                OM.LIBELLE_AGENCE,
                sum(OM.lcy_amount) as VOLUME_PAIEMENT_OM_M
            from  RESUL_OM OM
            where OM.TRN_DT >= TO_DATE('{m_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and OM.TRN_DT <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and OM.SENS_ECR='C'
            group by OM.CODE_AGENCE, OM.LIBELLE_AGENCE
        ),
        PAIEMENT_OM_M_1 as (
            select 
                OM1.CODE_AGENCE,
                OM1.LIBELLE_AGENCE,
                sum(OM1.lcy_amount) as VOLUME_PAIEMENT_OM_M_1
            from  RESUL_OM OM1
            where OM1.TRN_DT >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and OM1.TRN_DT <= TO_DATE('{m1_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and OM1.SENS_ECR='C'
            group by OM1.CODE_AGENCE, OM1.LIBELLE_AGENCE
        )
        select 
            COALESCE(EOM.CODE_AGENCE, EOM1.CODE_AGENCE, POM.CODE_AGENCE, POM1.CODE_AGENCE) as CODE_AGENCE,
            COALESCE(EOM.LIBELLE_AGENCE, EOM1.LIBELLE_AGENCE, POM.LIBELLE_AGENCE, POM1.LIBELLE_AGENCE) as LIBELLE_AGENCE,
            COALESCE(EOM1.VOLUME_ENVOIE_OM_M_1, 0) + COALESCE(POM1.VOLUME_PAIEMENT_OM_M_1, 0) as VOLUME_M_1,
            COALESCE(EOM.VOLUME_ENVOIE_OM_M, 0) + COALESCE(POM.VOLUME_PAIEMENT_OM_M, 0) as VOLUME_M,
            (COALESCE(EOM.VOLUME_ENVOIE_OM_M, 0) + COALESCE(POM.VOLUME_PAIEMENT_OM_M, 0) - 
             COALESCE(EOM1.VOLUME_ENVOIE_OM_M_1, 0) - COALESCE(POM1.VOLUME_PAIEMENT_OM_M_1, 0)) as Variation_volume,
            ROUND(
                (((COALESCE(EOM.VOLUME_ENVOIE_OM_M, 0) + COALESCE(POM.VOLUME_PAIEMENT_OM_M, 0) - 
                   COALESCE(EOM1.VOLUME_ENVOIE_OM_M_1, 0) - COALESCE(POM1.VOLUME_PAIEMENT_OM_M_1, 0)) / 
                  NULLIF(COALESCE(EOM1.VOLUME_ENVOIE_OM_M_1, 0) + COALESCE(POM1.VOLUME_PAIEMENT_OM_M_1, 0), 0)) * 100), 
                2
            ) AS VARIATION_PCT
        from ENVOIE_OM_M EOM
        FULL OUTER JOIN ENVOIE_OM_M_1 EOM1 on EOM1.CODE_AGENCE=EOM.CODE_AGENCE
        FULL OUTER JOIN PAIEMENT_OM_M POM on POM.CODE_AGENCE=COALESCE(EOM.CODE_AGENCE, EOM1.CODE_AGENCE)
        FULL OUTER JOIN PAIEMENT_OM_M_1 POM1 on POM1.CODE_AGENCE=COALESCE(EOM.CODE_AGENCE, EOM1.CODE_AGENCE, POM.CODE_AGENCE)
        """
        
        # Exécuter une seule requête combinée
        cursor.execute(combined_query)
        results = cursor.fetchall()
        
        # Vérifier que la requête a retourné des colonnes
        if not cursor.description:
            logger.warning("⚠️ La requête n'a retourné aucune colonne")
            return []
        
        columns = [desc[0] for desc in cursor.description]
        logger.info(f"📊 Colonnes retournées: {columns}")
        
        # Traiter les résultats
        agencies_data = {}
        for row in results:
            try:
                row_dict = dict(zip(columns, row))
                # Créer un dictionnaire insensible à la casse pour les clés
                row_dict_upper = {k.upper(): v for k, v in row_dict.items()}
                
                code_agence = row_dict_upper.get('CODE_AGENCE')
                libelle_agence = row_dict_upper.get('LIBELLE_AGENCE')
                
                if not code_agence:
                    continue
                    
                if code_agence not in agencies_data:
                    agencies_data[code_agence] = {
                        'agence': libelle_agence or '',
                        'code_agence': code_agence,
                        'volume_m': 0,
                        'volume_m1': 0,
                        'variation_volume': 0,
                        'variation_pct': 0
                    }
                
                agencies_data[code_agence]['volume_m'] = float(row_dict_upper.get('VOLUME_M') or 0)
                agencies_data[code_agence]['volume_m1'] = float(row_dict_upper.get('VOLUME_M_1') or 0)
                agencies_data[code_agence]['variation_volume'] = float(row_dict_upper.get('VARIATION_VOLUME') or 0)
                agencies_data[code_agence]['variation_pct'] = float(row_dict_upper.get('VARIATION_PCT') or 0)
            except Exception as row_error:
                logger.error(f"❌ Erreur lors du traitement d'une ligne: {str(row_error)}")
                logger.error(f"   Colonnes disponibles: {list(row_dict.keys()) if 'row_dict' in locals() else 'N/A'}")
                continue
        
        # Calculer les variations si nécessaire
        result = []
        for code_agence, data in agencies_data.items():
            result.append({
                'agence': data['agence'],
                'code_agence': code_agence,
                'volume_m': round(data['volume_m'], 2),
                'volume_m1': round(data['volume_m1'], 2),
                'variation_volume': round(data['variation_volume'], 2),
                'variation_pct': round(data['variation_pct'], 2)
            })
        
        logger.info(f"✅ Données Orange Money récupérées: {len(result)} agences")
        return result
        
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données Orange Money: {str(e)}", exc_info=True)
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def get_ria_data(month: int, year: int) -> List[Dict]:
    """
    Récupère les données Ria Money Transfer (envois et paiements) depuis Oracle
    
    Args:
        month: Mois (1-12)
        year: Année
        
    Returns:
        Liste de dictionnaires avec les données par agence
    """
    logger.info(f"📅 get_ria_data appelé avec month={month}, year={year}")
    dates = calculate_month_dates(month, year)
    logger.info(f"📅 Dates calculées pour RIA: M={dates['m_debut']} à {dates['m_fin']}, M-1={dates['m1_debut']} à {dates['m1_fin']}")
    conn = get_oracle_connection()
    cursor = conn.cursor()
    
    try:
        # Requête ultra-optimisée combinant envois et paiements RIA en une seule requête
        m1_debut_date = datetime.strptime(dates['m1_debut'], '%d/%m/%Y')
        m_fin_date = datetime.strptime(dates['m_fin'], '%d/%m/%Y')
        m_debut_date = datetime.strptime(dates['m_debut'], '%d/%m/%Y')
        m1_fin_date = datetime.strptime(dates['m1_fin'], '%d/%m/%Y')
        
        logger.info(f"📅 Dates pour requête RIA:")
        logger.info(f"   M1 début: {m1_debut_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M fin: {m_fin_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M début: {m_debut_date.strftime('%d/%m/%Y')}")
        logger.info(f"   M1 fin: {m1_fin_date.strftime('%d/%m/%Y')}")
        
        combined_query = f"""
        WITH Journal AS (
            SELECT
                AC_BRANCH, AC_NO, DRCR_IND, LCY_AMOUNT, 
                COALESCE(VALUE_DT, TRN_DT) as TRN_DT
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES 
            WHERE COALESCE(VALUE_DT, TRN_DT) >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY') 
              AND COALESCE(VALUE_DT, TRN_DT) <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
        ),
        RESUL_RIA as (
            select 
                   nvl(c.gl_code,s.DR_GL) "PARENT_GL"
                   ,a.ac_branch as CODE_AGENCE
                   ,a.drcr_ind as SENS_ECR
                   ,b.branch_name as LIBELLE_AGENCE
                   ,a.lcy_amount
                   ,a.TRN_DT
            from Journal a
                   LEFT JOIN CFSFCUBS145.gltm_glmaster c ON c.gl_code = a.AC_NO
                   LEFT JOIN CFSFCUBS145.STTM_CUST_ACCOUNT s ON s.CUST_AC_NO = a.AC_NO
                   LEFT JOIN CFSFCUBS145.STTM_BRANCH b ON b.branch_code = a.ac_branch
            where nvl(c.gl_code,s.DR_GL) like '101%'
        ),
        ENVOIE_RIA_M as (
            select 
                RA.CODE_AGENCE,
                RA.LIBELLE_AGENCE,
                sum(RA.lcy_amount) as VOLUME_ENVOIE_RIA_M
            from  RESUL_RIA RA
            where RA.TRN_DT >= TO_DATE('{m_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and RA.TRN_DT <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and RA.SENS_ECR='D'
            group by RA.CODE_AGENCE, RA.LIBELLE_AGENCE
        ),
        ENVOIE_RIA_M_1 as (
            select 
                RA1.CODE_AGENCE,
                RA1.LIBELLE_AGENCE,
                sum(RA1.lcy_amount) as VOLUME_ENVOIE_RIA_M_1
            from  RESUL_RIA RA1
            where RA1.TRN_DT >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and RA1.TRN_DT <= TO_DATE('{m1_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and RA1.SENS_ECR='D'
            group by RA1.CODE_AGENCE, RA1.LIBELLE_AGENCE
        ),
        PAIEMENT_RIA_M as (
            select 
                RA.CODE_AGENCE,
                RA.LIBELLE_AGENCE,
                sum(RA.lcy_amount) as VOLUME_PAIEMENT_RIA_M
            from  RESUL_RIA RA
            where RA.TRN_DT >= TO_DATE('{m_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and RA.TRN_DT <= TO_DATE('{m_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and RA.SENS_ECR='C'
            group by RA.CODE_AGENCE, RA.LIBELLE_AGENCE
        ),
        PAIEMENT_RIA_M_1 as (
            select 
                RA1.CODE_AGENCE,
                RA1.LIBELLE_AGENCE,
                sum(RA1.lcy_amount) as VOLUME_PAIEMENT_RIA_M_1
            from  RESUL_RIA RA1
            where RA1.TRN_DT >= TO_DATE('{m1_debut_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
              and RA1.TRN_DT <= TO_DATE('{m1_fin_date.strftime('%d/%m/%Y')}', 'DD/MM/YYYY')
            and RA1.SENS_ECR='C'
            group by RA1.CODE_AGENCE, RA1.LIBELLE_AGENCE
        )
        select 
            COALESCE(ERM.CODE_AGENCE, ERM1.CODE_AGENCE, PRM.CODE_AGENCE, PRM1.CODE_AGENCE) as CODE_AGENCE,
            COALESCE(ERM.LIBELLE_AGENCE, ERM1.LIBELLE_AGENCE, PRM.LIBELLE_AGENCE, PRM1.LIBELLE_AGENCE) as LIBELLE_AGENCE,
            COALESCE(ERM1.VOLUME_ENVOIE_RIA_M_1, 0) + COALESCE(PRM1.VOLUME_PAIEMENT_RIA_M_1, 0) as VOLUME_M_1,
            COALESCE(ERM.VOLUME_ENVOIE_RIA_M, 0) + COALESCE(PRM.VOLUME_PAIEMENT_RIA_M, 0) as VOLUME_M,
            (COALESCE(ERM.VOLUME_ENVOIE_RIA_M, 0) + COALESCE(PRM.VOLUME_PAIEMENT_RIA_M, 0) - 
             COALESCE(ERM1.VOLUME_ENVOIE_RIA_M_1, 0) - COALESCE(PRM1.VOLUME_PAIEMENT_RIA_M_1, 0)) as Variation_volume,
            ROUND(
                (((COALESCE(ERM.VOLUME_ENVOIE_RIA_M, 0) + COALESCE(PRM.VOLUME_PAIEMENT_RIA_M, 0) - 
                   COALESCE(ERM1.VOLUME_ENVOIE_RIA_M_1, 0) - COALESCE(PRM1.VOLUME_PAIEMENT_RIA_M_1, 0)) / 
                  NULLIF(COALESCE(ERM1.VOLUME_ENVOIE_RIA_M_1, 0) + COALESCE(PRM1.VOLUME_PAIEMENT_RIA_M_1, 0), 0)) * 100), 
                2
            ) AS VARIATION_PCT
        from ENVOIE_RIA_M ERM
        FULL OUTER JOIN ENVOIE_RIA_M_1 ERM1 on ERM1.CODE_AGENCE=ERM.CODE_AGENCE
        FULL OUTER JOIN PAIEMENT_RIA_M PRM on PRM.CODE_AGENCE=COALESCE(ERM.CODE_AGENCE, ERM1.CODE_AGENCE)
        FULL OUTER JOIN PAIEMENT_RIA_M_1 PRM1 on PRM1.CODE_AGENCE=COALESCE(ERM.CODE_AGENCE, ERM1.CODE_AGENCE, PRM.CODE_AGENCE)
        """
        
        # Exécuter une seule requête combinée
        cursor.execute(combined_query)
        results = cursor.fetchall()
        
        # Vérifier que la requête a retourné des colonnes
        if not cursor.description:
            logger.warning("⚠️ La requête n'a retourné aucune colonne")
            return []
        
        columns = [desc[0] for desc in cursor.description]
        logger.info(f"📊 Colonnes retournées: {columns}")
        
        # Traiter les résultats
        agencies_data = {}
        for row in results:
            try:
                row_dict = dict(zip(columns, row))
                # Créer un dictionnaire insensible à la casse pour les clés
                row_dict_upper = {k.upper(): v for k, v in row_dict.items()}
                
                code_agence = row_dict_upper.get('CODE_AGENCE')
                libelle_agence = row_dict_upper.get('LIBELLE_AGENCE')
                
                if not code_agence:
                    continue
                    
                if code_agence not in agencies_data:
                    agencies_data[code_agence] = {
                        'agence': libelle_agence or '',
                        'code_agence': code_agence,
                        'volume_m': 0,
                        'volume_m1': 0,
                        'variation_volume': 0,
                        'variation_pct': 0
                    }
                
                agencies_data[code_agence]['volume_m'] = float(row_dict_upper.get('VOLUME_M') or 0)
                agencies_data[code_agence]['volume_m1'] = float(row_dict_upper.get('VOLUME_M_1') or 0)
                agencies_data[code_agence]['variation_volume'] = float(row_dict_upper.get('VARIATION_VOLUME') or 0)
                agencies_data[code_agence]['variation_pct'] = float(row_dict_upper.get('VARIATION_PCT') or 0)
            except Exception as row_error:
                logger.error(f"❌ Erreur lors du traitement d'une ligne: {str(row_error)}")
                logger.error(f"   Colonnes disponibles: {list(row_dict.keys()) if 'row_dict' in locals() else 'N/A'}")
                continue
        
        # Calculer les variations si nécessaire
        result = []
        for code_agence, data in agencies_data.items():
            result.append({
                'agence': data['agence'],
                'code_agence': code_agence,
                'volume_m': round(data['volume_m'], 2),
                'volume_m1': round(data['volume_m1'], 2),
                'variation_volume': round(data['variation_volume'], 2),
                'variation_pct': round(data['variation_pct'], 2)
            })
        
        logger.info(f"✅ Données RIA récupérées: {len(result)} agences")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données RIA: {str(e)}", exc_info=True)
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def calculate_month_dates(month: int, year: int) -> Dict[str, str]:
    """
    Calcule les dates du mois M et M-1
    
    Args:
        month: Mois (1-12)
        year: Année
        
    Returns:
        Dictionnaire avec les dates au format DD/MM/YYYY et YYYY-MM-DD
    """
    # S'assurer que month et year sont des entiers
    month = int(month)
    year = int(year)
    
    logger.info(f"📅 calculate_month_dates appelé avec month={month}, year={year}")
    
    # Premier jour du mois M
    first_day = datetime(year, month, 1)
    # Dernier jour du mois M
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
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
        'm1_debut': prev_first_day.strftime("%d/%m/%Y"),
        'm1_fin': prev_last_day.strftime("%d/%m/%Y"),
        # Format DATE pour Oracle (YYYY-MM-DD)
        'm_debut_date': first_day.strftime("%Y-%m-%d"),
        'm_fin_date': last_day.strftime("%Y-%m-%d"),
        'm1_debut_date': prev_first_day.strftime("%Y-%m-%d"),
        'm1_fin_date': prev_last_day.strftime("%Y-%m-%d"),
    }


def get_transfer_data(period: str = "month", month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None, service: str = "om"):
    """
    Récupère les données de transferts d'argent depuis Oracle
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date au format YYYY-MM-DD pour period="week"
        service: Service de transfert ("om", "wave", "ria", "wu")
    
    Returns:
        Dictionnaire avec les données de transferts organisées par agences et services
    """
    logger.info(f"🔍 get_transfer_data appelé avec period={period}, month={month} (type: {type(month)}), year={year} (type: {type(year)}), date={date}, service={service}")
    
    # Pour l'instant, on ne gère que la période "month"
    if period != "month":
        logger.warning(f"⚠️ Période '{period}' non supportée pour les transferts. Utilisation de 'month' par défaut.")
        period = "month"
    
    # S'assurer que month et year sont des entiers
    if month is not None:
        month = int(month)
    if year is not None:
        year = int(year)
    
    # Utiliser le mois et l'année actuels si non fournis
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    logger.info(f"📅 Paramètres de date finaux (après conversion): month={month} (type: {type(month)}), year={year} (type: {type(year)})")
    
    # Calculer les dates - IMPORTANT: recalculer à chaque appel pour éviter le cache
    dates = calculate_month_dates(month, year)
    
    logger.info(f"📅 Dates calculées: M={dates['m_debut']} à {dates['m_fin']}, M-1={dates['m1_debut']} à {dates['m1_fin']}")
    
    try:
        # Récupérer les données selon le service sélectionné
        if service == "om":
            logger.info("📊 Récupération des données Orange Money depuis Oracle")
            om_data = get_orange_money_data(month, year)
        elif service == "wave":
            logger.info("📊 Récupération des données Wave depuis Oracle")
            # TODO: Implémenter get_wave_data quand les requêtes seront disponibles
            om_data = []
        elif service == "ria":
            logger.info("📊 Récupération des données Ria depuis Oracle")
            om_data = get_ria_data(month, year)
        elif service == "wu":
            logger.info("📊 Récupération des données Western Union depuis Oracle")
            # TODO: Implémenter get_wu_data quand les requêtes seront disponibles
            om_data = []
        else:
            logger.warning(f"⚠️ Service '{service}' non reconnu. Utilisation d'Orange Money par défaut.")
            om_data = get_orange_money_data(month, year)
        
        # Formater les données pour correspondre au format attendu
        agencies = []
        for om_item in om_data:
            try:
                # Calculer le TRO (Taux de Réalisation de l'Objectif)
                # Pour l'instant, objectif = 0 (à définir selon votre logique métier)
                objectif = 0
                tro = 0
                volume_m = om_item.get('volume_m', 0)
                if objectif > 0 and volume_m:
                    tro = (volume_m / objectif) * 100
                
                agencies.append({
                    "agence": om_item.get('agence', ''),
                    "objectif": objectif,
                    "volume_m": volume_m,
                    "volume_m1": om_item.get('volume_m1', 0),
                    "variation_volume": om_item.get('variation_volume', 0),
                    "variation_pct": om_item.get('variation_pct', 0),
                    "tro": round(tro, 2),
                    "contribution": 0,  # Sera calculé après
                    "commission": 0  # À calculer selon votre logique métier
                })
            except Exception as item_error:
                logger.error(f"❌ Erreur lors du traitement d'un item: {str(item_error)}")
                logger.error(f"   Item: {om_item}")
                continue
        
        # Calculer les contributions
        total_volume_m = sum(a['volume_m'] for a in agencies)
        for agency in agencies:
            if total_volume_m > 0:
                agency['contribution'] = round((agency['volume_m'] / total_volume_m) * 100, 2)
        
        result_data = {
            "agencies": agencies,
            "services": []  # Services seront ajoutés séparément si nécessaire
        }
        
        logger.info(f"✅ Données de transferts récupérées: {len(result_data['agencies'])} agences")
        return result_data
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des données de transferts: {str(e)}", exc_info=True)
        raise
