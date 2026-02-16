"""
Service pour la gestion des données de ventes de cartes prépayées (CofiCarte)
"""
import logging
from typing import Optional
from database.oracle_pool import get_pool
from services.utils import (
    calculate_period_dates, 
    get_territory_from_agency, 
    get_territory_key, 
    get_all_territories,
    SERVICE_POINT_MAPPING,
    get_territory_from_branch_code
)
from services.cache_service import get_cache, set_cache, generate_cache_key

logger = logging.getLogger(__name__)


def get_prepaid_card_sales_data(period: str = "month", zone: Optional[str] = None, 
                                month: Optional[int] = None, year: Optional[int] = None, 
                                date: Optional[str] = None):
    """
    Récupère les données de ventes de cartes prépayées depuis Oracle
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période "week"
    
    Returns:
        Dictionnaire avec les données de ventes de cartes prépayées
    """
    logger.info(f"🔍 get_prepaid_card_sales_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}")
    
    # Valider et convertir les paramètres
    if month is not None:
        try:
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError(f"Mois invalide: {month}")
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erreur de validation du mois: {e}")
            month = None
    
    if year is not None:
        try:
            year = int(year)
            if year < 2000 or year > 2100:
                raise ValueError(f"Année invalide: {year}")
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erreur de validation de l'année: {e}")
            year = None
    
    # Générer une clé de cache basée sur les paramètres
    cache_key = f"prepaid_card_sales:{generate_cache_key(period, zone, month, year, date)}"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données de ventes de cartes prépayées récupérées depuis le cache")
        return cached_result
    
    # Calculer les dates
    try:
        dates = calculate_period_dates(period, month, year, date)
        date_m_debut_str = dates['date_m_debut_str']
        date_m_fin_str = dates['date_m_fin_str']
        date_m1_debut_str = dates['date_m1_debut_str']
        date_m1_fin_str = dates['date_m1_fin_str']
        
        # Valider le format des dates
        if not all([date_m_debut_str, date_m_fin_str, date_m1_debut_str, date_m1_fin_str]):
            raise ValueError("Une ou plusieurs dates sont None")
        
        # Vérifier le format DD/MM/YYYY
        from datetime import datetime
        for date_str, date_name in [
            (date_m_debut_str, 'date_m_debut_str'),
            (date_m_fin_str, 'date_m_fin_str'),
            (date_m1_debut_str, 'date_m1_debut_str'),
            (date_m1_fin_str, 'date_m1_fin_str')
        ]:
            try:
                datetime.strptime(date_str, '%d/%m/%Y')
            except ValueError as e:
                raise ValueError(f"Format de date invalide pour {date_name}: {date_str} - {e}")
        
        logger.info(f"📅 Dates utilisées pour la requête Oracle: M={date_m_debut_str} à {date_m_fin_str}, M-1={date_m1_debut_str} à {date_m1_fin_str}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du calcul des dates: {e}", exc_info=True)
        raise ValueError(f"Erreur lors du calcul des dates: {e}")
    
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        
        # Optimisations Oracle
        cursor.arraysize = 1000
        cursor.prefetchrows = 1000
        
        try:
            logger.info("🔍 Exécution de la requête Vente CofiCarte...")
            
            # Construire la requête SQL avec les dates dynamiques
            query = f"""
WITH Journal AS (
    SELECT
        TRN_REF_NO, AC_ENTRY_SR_NO, EVENT_SR_NO, EVENT, AC_BRANCH, AC_NO, AC_CCY, CATEGORY, DRCR_IND, TRN_CODE, FCY_AMOUNT, EXCH_RATE, LCY_AMOUNT, VALUE_DT AS TRN_DT, VALUE_DT, TXN_INIT_DATE, AMOUNT_TAG, RELATED_ACCOUNT, RELATED_CUSTOMER, RELATED_REFERENCE, MIS_HEAD, MIS_FLAG, INSTRUMENT_CODE, BANK_CODE, BALANCE_UPD, AUTH_STAT, MODULE, CUST_GL, DLY_HIST, FINANCIAL_CYCLE, PERIOD_CODE, BATCH_NO, USER_ID, CURR_NO, PRINT_STAT, AUTH_ID, GLMIS_VAL_UPD_FLAG, EXTERNAL_REF_NO, DONT_SHOWIN_STMT, IC_BAL_INCLUSION, AML_EXCEPTION, IB, GLMIS_UPDATE_FLAG, PRODUCT_ACCRUAL, ORIG_PNL_GL, STMT_DT, ENTRY_SEQ_NO, VIRTUAL_AC_NO, CLAIM_AMOUNT, GRP_REF_NO, SAVE_TIMESTAMP, AUTH_TIMESTAMP, PRODUCT_PROCESSOR, RELATED_AC_ENTRY_SR_NO, DONT_SHOWIN_STMT_FEE, ORG_SOURCE, ORG_SOURCE_REF, SOURCE_CODE
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES 
    WHERE MODULE = 'DE'
    UNION
    SELECT
        TRN_REF_NO, AC_ENTRY_SR_NO, EVENT_SR_NO, EVENT, AC_BRANCH, AC_NO, AC_CCY, CATEGORY, DRCR_IND, TRN_CODE, FCY_AMOUNT, EXCH_RATE, LCY_AMOUNT, TRN_DT, VALUE_DT, TXN_INIT_DATE, AMOUNT_TAG, RELATED_ACCOUNT, RELATED_CUSTOMER, RELATED_REFERENCE, MIS_HEAD, MIS_FLAG, INSTRUMENT_CODE, BANK_CODE, BALANCE_UPD, AUTH_STAT, MODULE, CUST_GL, DLY_HIST, FINANCIAL_CYCLE, PERIOD_CODE, BATCH_NO, USER_ID, CURR_NO, PRINT_STAT, AUTH_ID, GLMIS_VAL_UPD_FLAG, EXTERNAL_REF_NO, DONT_SHOWIN_STMT, IC_BAL_INCLUSION, AML_EXCEPTION, IB, GLMIS_UPDATE_FLAG, PRODUCT_ACCRUAL, ORIG_PNL_GL, STMT_DT, ENTRY_SEQ_NO, VIRTUAL_AC_NO, CLAIM_AMOUNT, GRP_REF_NO, SAVE_TIMESTAMP, AUTH_TIMESTAMP, PRODUCT_PROCESSOR, RELATED_AC_ENTRY_SR_NO, DONT_SHOWIN_STMT_FEE, ORG_SOURCE, ORG_SOURCE_REF, SOURCE_CODE
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES 
    WHERE MODULE <> 'DE'
),

VENTE_COFICARTE as (
select 
       nvl(c.gl_code,s.DR_GL) "PARENT_GL"
       ,nvl(c.GL_DESC,s.ac_desc) "DESCRIPTION"
       ,a.ac_branch as CODE_AGENCE
       ,b.branch_name as LIBELLE_AGENCE
       ,decode(a.drcr_ind, 'D', a.lcy_amount, 0) Debit_Envoi
       ,decode(a.drcr_ind, 'C', a.lcy_amount, 0) Credit_Paiement
       ,a.trn_dt as TRN_DT
       ,to_char(a.trn_dt,'dd/mm/yyyy')"DATE_SAISIE"
       ,to_char(a.value_dt,'dd/mm/yyyy')"DATE_VALEUR"
       ,a.USER_ID "UTIL SAISI"
       ,a.AC_NO "ACCOUNT_NO"
       ,a.AUTH_ID "UTIL VALID"
       ,a.drcr_ind as SENS_ECR
       ,a.BATCH_NO
       ,a.trn_ref_no
       ,a.trn_code
       ,nvl((select u.ADDL_TEXT from CFSFCUBS145.detb_upload_detail u WHERE u.BATCH_NO=A.BATCH_NO AND U.ACCOUNT=A.AC_NO and U.VALUE_DATE=A.VALUE_DT and u.AMOUNT=A.lcy_amount AND A.CURR_NO=U.CURR_NO),t.TRN_DESC)"LIBELLE_OPER"
       ,nvl(od.ADDL_TEXT, nvl(xx.ADDL_TEXT, d.DESCRIPTION)) "DESCRIPTION BATCH"
       ,a.related_customer "MATRICULE_CLIENT"
       ,s.ALT_AC_NO "ACCOUNT NAFA"
from Journal a
       LEFT JOIN CFSFCUBS145.gltm_glmaster c ON c.gl_code = a.AC_NO
       LEFT JOIN CFSFCUBS145.STTM_CUST_ACCOUNT s ON s.CUST_AC_NO = a.AC_NO
       left JOIN CFSFCUBS145.STTM_TRN_CODE t ON t.TRN_CODE = a.TRN_CODE
       left JOIN CFSFCUBS145.STTM_BRANCH b ON b.branch_code = a.ac_branch
       left join cfsfcubs145.DETBS_JRNL_TXN_DETAIL xx on a.TRN_REF_NO = xx.REFERENCE_NO and a.EVENT_SR_NO=xx.SERIAL_NO
       left join cfsfcubs145.detb_batch_master d on a.batch_no = d.batch_no and a.ac_branch = d.BRANCH_CODE
       left join cfsfcubs145.detb_upload_detail od on od.batch_no = a.batch_no and a.ac_branch = od.ACCOUNT_BRANCH and a.CURR_NO = od.CURR_NO
WHERE
       (nvl(c.gl_code,s.DR_GL) like '3792%' OR a.AC_NO like '3792%')
),

RESUL_VENTE_M  as (
select 
    MAX(RVC1.DESCRIPTION) as DESCRIPTION,
    RVC1.CODE_AGENCE,
    RVC1.LIBELLE_AGENCE,
    count(*)  as NOMBRE_COFICARTE_VENDU_M
from  VENTE_COFICARTE  RVC1
where RVC1.PARENT_GL  like  '3792%'
and RVC1.TRN_DT is not null
and RVC1.TRN_DT >= TO_DATE('{date_m_debut_str}','DD/MM/YYYY')
and RVC1.TRN_DT <= TO_DATE('{date_m_fin_str}','DD/MM/YYYY')
and RVC1.SENS_ECR='C'
group by RVC1.CODE_AGENCE,
    RVC1.LIBELLE_AGENCE 
),

RESUL_VENTE_M_1   as (
select 
    MAX(RVC1.DESCRIPTION) as DESCRIPTION,
    RVC1.CODE_AGENCE,
    RVC1.LIBELLE_AGENCE,
    count(*)  as NOMBRE_COFICARTE_VENDU_M_1
from  VENTE_COFICARTE  RVC1
where RVC1.PARENT_GL  like  '3792%'
and RVC1.TRN_DT is not null
and RVC1.TRN_DT >= TO_DATE('{date_m1_debut_str}','DD/MM/YYYY')
and RVC1.TRN_DT <= TO_DATE('{date_m1_fin_str}','DD/MM/YYYY')
and RVC1.SENS_ECR='C'
group by RVC1.CODE_AGENCE,
    RVC1.LIBELLE_AGENCE
),

OBJECTIF_COFICARTE AS (
    SELECT  
        BRANCH_CODE,
        BRANCH_NAME,
        0 AS OBJECTIF_COFICARTE
    FROM CFSFCUBS145.STTM_BRANCH
),

ALL_AGENCIES AS (
    SELECT CODE_AGENCE, LIBELLE_AGENCE FROM RESUL_VENTE_M
    UNION
    SELECT CODE_AGENCE, LIBELLE_AGENCE FROM RESUL_VENTE_M_1
)

select
    AA.CODE_AGENCE,
    AA.LIBELLE_AGENCE,
    COALESCE(OB.OBJECTIF_COFICARTE, 0) AS OBJECTIF_COFICARTE,
    COALESCE(RVM1.NOMBRE_COFICARTE_VENDU_M_1, 0) AS NOMBRE_COFICARTE_VENDU_M_1,
    COALESCE(RVM.NOMBRE_COFICARTE_VENDU_M, 0) AS NOMBRE_COFICARTE_VENDU_M,
    (COALESCE(RVM.NOMBRE_COFICARTE_VENDU_M, 0) - COALESCE(RVM1.NOMBRE_COFICARTE_VENDU_M_1, 0)) AS Variation_Nombre,
    ROUND(
        (((COALESCE(RVM.NOMBRE_COFICARTE_VENDU_M, 0) - COALESCE(RVM1.NOMBRE_COFICARTE_VENDU_M_1, 0))) / NULLIF(COALESCE(RVM1.NOMBRE_COFICARTE_VENDU_M_1, 0), 0)) * 100, 
        2
    ) AS "VARIATION%",
    ROUND(
        (COALESCE(RVM.NOMBRE_COFICARTE_VENDU_M, 0) / NULLIF(COALESCE(OB.OBJECTIF_COFICARTE, 0), 0)) * 100, 
        2
    ) AS TAUX_REALISATION
from ALL_AGENCIES AA
LEFT JOIN RESUL_VENTE_M RVM ON RVM.CODE_AGENCE = AA.CODE_AGENCE
LEFT JOIN RESUL_VENTE_M_1 RVM1 ON RVM1.CODE_AGENCE = AA.CODE_AGENCE
LEFT JOIN OBJECTIF_COFICARTE OB ON OB.BRANCH_CODE = AA.CODE_AGENCE
ORDER BY AA.CODE_AGENCE
"""
            
            cursor.execute(query)
            
            # Récupérer les résultats
            columns = [desc[0] for desc in cursor.description]
            raw_data = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convertir les Decimal en float pour JSON
                for key, value in row_dict.items():
                    if value is None:
                        if key in ['NOMBRE_COFICARTE_VENDU_M', 'NOMBRE_COFICARTE_VENDU_M_1', 'VARIATION%', 'Variation_Nombre']:
                            row_dict[key] = 0
                        else:
                            row_dict[key] = None
                    elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                        try:
                            row_dict[key] = float(value)
                        except (ValueError, TypeError):
                            row_dict[key] = 0
                raw_data.append(row_dict)
            
            logger.info(f"📊 {len(raw_data)} lignes récupérées depuis Oracle")
            
            # Transformer les données en structure hiérarchique
            agencies_by_territory = {
                'territoire_dakar_ville': [],
                'territoire_dakar_banlieue': [],
                'territoire_province_centre_sud': [],
                'territoire_province_nord': []
            }
            service_points_data = []
            
            # Calculer le total global pour la contribution
            total_global_m = sum(int(row.get('NOMBRE_COFICARTE_VENDU_M') or 0) for row in raw_data)
            
            # Traiter chaque ligne de données
            for row in raw_data:
                agency_name = row.get('LIBELLE_AGENCE') or row.get('DESCRIPTION') or 'Inconnu'
                branch_code = row.get('CODE_AGENCE') or None
                objectif = int(row.get('OBJECTIF_COFICARTE') or 0)
                nombre_m = int(row.get('NOMBRE_COFICARTE_VENDU_M') or 0)
                nombre_m1 = int(row.get('NOMBRE_COFICARTE_VENDU_M_1') or 0)
                variation_nombre = int(row.get('Variation_Nombre') or 0)
                variation_pourcent = float(row.get('VARIATION%') or 0)
                taux_realisation = float(row.get('TAUX_REALISATION') or 0)
                
                # Calculer la contribution agence
                contribution = 0.0
                if total_global_m > 0:
                    contribution = round((nombre_m / total_global_m) * 100, 2)
                
                # Créer l'objet agence avec tous les alias nécessaires pour le frontend
                agency_obj = {
                    'AGENCE': agency_name,
                    'CODE_AGENCE': branch_code,
                    'OBJECTIF_COFICARTE': objectif,
                    'objectif': objectif,  # Alias pour compatibilité
                    'NOMBRE_COFICARTE_VENDU_M': nombre_m,
                    'NOMBRE_COFICARTE_VENDU_M_1': nombre_m1,
                    'm': nombre_m,  # Alias pour compatibilité
                    'm1': nombre_m1,  # Alias pour compatibilité
                    'Variation_Nombre': variation_nombre,
                    'variationNombre': variation_nombre,  # Alias pour compatibilité
                    'VARIATION%': variation_pourcent,
                    'variationPourcent': variation_pourcent,  # Alias pour compatibilité
                    'TAUX_REALISATION': taux_realisation,
                    'atteinte': taux_realisation,  # Alias pour compatibilité
                    'CONTRIBUTION': contribution,
                    'contribution': contribution,  # Alias pour compatibilité
                    'DESCRIPTION': row.get('DESCRIPTION') or ''
                }
                
                # Déterminer le territoire
                territory = None
                if branch_code:
                    territory = get_territory_from_branch_code(str(branch_code))
                
                if not territory:
                    territory = get_territory_from_agency(agency_name)
                
                # Vérifier si c'est un point de service
                is_service_point = False
                if agency_name:
                    agency_name_upper = str(agency_name).upper().strip()
                    agency_name_normalized = ' '.join(agency_name_upper.split())
                    
                    for service_point_name in SERVICE_POINT_MAPPING.keys():
                        service_point_upper = str(service_point_name).upper().strip() if service_point_name else ''
                        service_point_normalized = ' '.join(service_point_upper.split())
                        
                        if (service_point_normalized == agency_name_normalized or
                            service_point_normalized in agency_name_normalized or
                            agency_name_normalized in service_point_normalized):
                            service_points_data.append(agency_obj)
                            is_service_point = True
                            logger.debug(f"✅ Point de service identifié: {agency_name}")
                            break
                
                if not is_service_point:
                    if territory:
                        territory_key = get_territory_key(territory)
                        if territory_key in agencies_by_territory:
                            agencies_by_territory[territory_key].append(agency_obj)
                        else:
                            # Par défaut, mettre dans DAKAR VILLE
                            agencies_by_territory['territoire_dakar_ville'].append(agency_obj)
                            logger.warning(f"⚠️ Territoire non reconnu pour {agency_name}, assigné à DAKAR VILLE")
                    else:
                        # Si aucun territoire trouvé, mettre dans DAKAR VILLE par défaut
                        agencies_by_territory['territoire_dakar_ville'].append(agency_obj)
                        logger.warning(f"⚠️ Aucun territoire trouvé pour {agency_name}, assigné à DAKAR VILLE")
            
            # Obtenir la structure complète des territoires
            try:
                all_territories = get_all_territories()
            except Exception as e:
                logger.error(f"❌ Erreur lors de la récupération de all_territories: {e}", exc_info=True)
                all_territories = {
                    'territoire_dakar_ville': {'name': 'TERRITOIRE DAKAR VILLE'},
                    'territoire_dakar_banlieue': {'name': 'TERRITOIRE DAKAR BANLIEUE'},
                    'territoire_province_centre_sud': {'name': 'TERRITOIRE PROVINCE CENTRE-SUD'},
                    'territoire_province_nord': {'name': 'TERRITOIRE PROVINCE NORD'}
                }
            
            # Calculer les totaux par territoire
            def calculate_territory_totals(agencies_list):
                totals = {
                    'objectif': 0,
                    'm1': 0,
                    'm': 0,
                    'variation': 0,
                    'variation_pourcent': 0,
                    'atteinte': 0,
                    'contribution': 0
                }
                for agency in agencies_list:
                    totals['objectif'] += int(agency.get('OBJECTIF_COFICARTE', 0) or 0)
                    totals['m1'] += int(agency.get('NOMBRE_COFICARTE_VENDU_M_1', 0) or 0)
                    totals['m'] += int(agency.get('NOMBRE_COFICARTE_VENDU_M', 0) or 0)
                    totals['variation'] += int(agency.get('Variation_Nombre', 0) or 0)
                if totals['m1'] > 0:
                    totals['variation_pourcent'] = round((totals['variation'] / totals['m1']) * 100, 2)
                if totals['objectif'] > 0:
                    totals['atteinte'] = round((totals['m'] / totals['objectif']) * 100, 2)
                if total_global_m > 0:
                    totals['contribution'] = round((totals['m'] / total_global_m) * 100, 2)
                return totals
            
            # Construire la structure hiérarchique
            hierarchical_data = {
                'TERRITOIRE': {},
                'POINT SERVICES': {}
            }
            
            # Ajouter les territoires avec leurs totaux
            for territory_key in ['territoire_dakar_ville', 'territoire_dakar_banlieue', 
                                 'territoire_province_centre_sud', 'territoire_province_nord']:
                agencies = agencies_by_territory.get(territory_key, [])
                totals = calculate_territory_totals(agencies)
                
                hierarchical_data['TERRITOIRE'][territory_key] = {
                    'name': all_territories.get(territory_key, {}).get('name', territory_key.upper()),
                    'data': agencies,
                    'total': totals
                }
            
            # Ajouter les points de service
            service_points_totals = calculate_territory_totals(service_points_data)
            hierarchical_data['POINT SERVICES'] = {
                'service_points': {
                    'name': 'POINT SERVICES',
                    'data': service_points_data,
                    'total': service_points_totals
                }
            }
            
            # Construire la réponse finale
            response_data = {
                'hierarchicalData': hierarchical_data
            }
            
            logger.info(f"📊 Structure hiérarchique créée: {len(agencies_by_territory['territoire_dakar_ville'])} agences DAKAR VILLE, "
                       f"{len(agencies_by_territory['territoire_dakar_banlieue'])} DAKAR BANLIEUE, "
                       f"{len(agencies_by_territory['territoire_province_centre_sud'])} PROVINCE CENTRE-SUD, "
                       f"{len(agencies_by_territory['territoire_province_nord'])} PROVINCE NORD, "
                       f"{len(service_points_data)} points de service")
            
            # Mettre en cache le résultat
            set_cache(cache_key, response_data, ttl=300)  # Cache de 5 minutes
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution de la requête Vente CofiCarte: {str(e)}", exc_info=True)
            raise
        finally:
            cursor.close()
