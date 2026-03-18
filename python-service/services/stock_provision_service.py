"""
Service pour la gestion des données de stock de provision
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import calendar
from database.oracle import get_oracle_connection
from services.utils import AGENCY_TERRITORY_MAPPING, SERVICE_POINT_MAPPING

logger = logging.getLogger(__name__)


def get_stock_provision_data(month: Optional[int] = None, year: Optional[int] = None):
    """
    Récupère les données de stock de provision depuis Oracle
    
    Args:
        month: Mois à analyser (1-12). Si non fourni, utilise le mois courant.
        year: Année à analyser. Si non fourni, utilise l'année courante.
    
    Returns:
        Liste de dictionnaires avec les données de stock par branche
    """
    logger.info(f"🔍 get_stock_provision_data appelé avec month={month}, year={year}")
    
    # Utiliser le mois et l'année courants si non fournis
    if month is None or year is None:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calculer la date de fin du mois
    last_day = calendar.monthrange(year, month)[1]
    date_end = datetime(year, month, last_day)
    date_end_str = date_end.strftime("%d/%m/%Y")
    date_end_sql = date_end.strftime("%Y-%m-%d")
    
    logger.info(f"📅 Date utilisée: {date_end_str} (SQL: {date_end_sql})")
    
    # Construire la requête avec les dates formatées
    query = f"""
    WITH   SOLDE as ( 
        select 
        ac_no 
        ,sum(decode (drcr_ind, 'C', lcy_amount, 0)) - sum(decode (drcr_ind, 'D', lcy_amount, 0)) "SOLDE" 
        from CFSFCUBS145.acvw_all_ac_entries 
        where trn_dt <= TO_DATE('{date_end_str}', 'DD/MM/YYYY')
        group by ac_no 
        ),


    sld_depot as  ( select * from SOLDE  where  AC_NO like '254%'),


    UDF_PRET AS (
    select
     p.MAKER_ID
    ,p.ACCOUNT_NUMBER
    ,b.BRANCH_NAME
    ,b.BRANCH_CODE
    ,p.FIELD_CHAR_2 "CODE_GESTION_PRET"  
    ,(select max(u.LOV_DESC) from cfsfcubs145.UDTM_LOV u where FIELD_NAME='GESTION_PRET'and u.LOV=p.FIELD_CHAR_2)"CHARGE_AFFAIRE"    

    ,p.FIELD_CHAR_8 "CODE_SECTEUR_ACTIVITE"  
    ,(select max(u.LOV_DESC) from cfsfcubs145.UDTM_LOV u where FIELD_NAME='SECTEUR_ACTIVITE' and u.LOV=p.FIELD_CHAR_8)"SECTEUR_ACTIVITE"
    ,p.FIELD_CHAR_9 "CODE_SOUS_SECTEUR"  
    ,(select max(u.LOV_DESC) from cfsfcubs145.UDTM_LOV u where FIELD_NAME='CODE_SOUS_SECTEUR' and u.LOV=p.FIELD_CHAR_9)"SOUS_SECTEUR"

    ,p.FIELD_NUMBER_2  "CPT_DEPOT_GARANTIE" 
    ,p.FIELD_NUMBER_3  "MONTANT_DEPOT_GARANTIE_INITIAL"
    from CFSFCUBS145.CLTB_ACCOUNT_MASTER p ,CFSFCUBS145.STTM_BRANCH b
    where b.BRANCH_CODE=p.BRANCH_CODE)




    ,



     ENCOURS as( 
        select 
        c.account_number "NO_PRET" 
        ,UDF.BRANCH_NAME
        ,UDF.BRANCH_CODE
        ,UDF.CODE_GESTION_PRET
        ,UDF.CHARGE_AFFAIRE
        ,dep.AC_NO as Compt_Depot_Gar
        ,dep.SOLDE as Solde_Depot_Gar
        ,c.USER_DEFINED_STATUS "STATUT_DECLASSEMENT" 
        ,SUM(z.AMOUNT_DUE) "MT_CAPITAL_TA" 
        ,SUM(z.AMOUNT_DUE-z.AMOUNT_SETTLED) "ENCOURS_TOTAL" 
        ,SUM(CASE WHEN (c.USER_DEFINED_STATUS IN ('NORM', 'IMPA')) THEN (z.AMOUNT_DUE-z.AMOUNT_SETTLED) ELSE 0 END) "ENCOURS_SAIN" 
        ,SUM(CASE WHEN (c.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA')) THEN (z.AMOUNT_DUE-z.AMOUNT_SETTLED) ELSE 0 END) "ENCOURS_IMPAYE" 
        from CFSFCUBS145.cltb_account_master c 
        left join CFSFCUBS145.cltb_account_schedules z on z.account_number=c.account_number 
        left join sld_depot dep  on  dep.AC_NO=c.FIELD_NUMBER_2
        left join UDF_PRET UDF on c.account_number=UDF.ACCOUNT_NUMBER
        WHERE 
        c.ACCOUNT_STATUS not in ('L','V') 
        and z.COMPONENT_NAME in ('PRINCIPAL') 
        group by 
        c.account_number ,c.USER_DEFINED_STATUS, dep.AC_NO,dep.SOLDE ,UDF.BRANCH_NAME
        ,UDF.CODE_GESTION_PRET
        ,UDF.CHARGE_AFFAIRE,UDF.BRANCH_CODE
    ),


    Stock_Provision  as (select 
        ENC.NO_PRET,
        ENC.STATUT_DECLASSEMENT,
        ENC.BRANCH_CODE,
        ENC.BRANCH_NAME,
        ENC.ENCOURS_TOTAL,
        nvl(ENC.Solde_Depot_Gar,0) as Solde_Depot_Gar,
        ((ENC.ENCOURS_TOTAL - nvl(ENC.Solde_Depot_Gar,0))*40)/100 as Stock_Provision,
        ENC.CODE_GESTION_PRET
    from ENCOURS  ENC
    where  ENC.STATUT_DECLASSEMENT='DCL2'

    UNION

    select 
        ENC.NO_PRET,
        ENC.STATUT_DECLASSEMENT,
        ENC.BRANCH_CODE,
        ENC.BRANCH_NAME,
        ENC.ENCOURS_TOTAL,
        nvl(ENC.Solde_Depot_Gar,0) as Solde_Depot_Gar,
        ((ENC.ENCOURS_TOTAL - nvl(ENC.Solde_Depot_Gar,0))*80)/100 as Stock_Provision,
        ENC.CODE_GESTION_PRET
    from ENCOURS  ENC
    where  ENC.STATUT_DECLASSEMENT='DCL3'


    UNION

    select 
        ENC.NO_PRET,
        ENC.STATUT_DECLASSEMENT,
        ENC.BRANCH_CODE,
        ENC.BRANCH_NAME,
        ENC.ENCOURS_TOTAL,
        nvl(ENC.Solde_Depot_Gar,0) as Solde_Depot_Gar,
        ((ENC.ENCOURS_TOTAL - nvl(ENC.Solde_Depot_Gar,0))*100)/100 as Stock_Provision,
        ENC.CODE_GESTION_PRET
    from ENCOURS  ENC
    where  ENC.STATUT_DECLASSEMENT='DCL4'),




    Journal AS (
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


    PROVISION_COMPTABILISE  as (SELECT 

        a.AC_BRANCH,


        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{date_end_str}', 'DD/MM/YYYY') THEN a.LCY_AMOUNT ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{date_end_str}', 'DD/MM/YYYY') THEN a.LCY_AMOUNT ELSE 0 END) AS Provision_comptabilisee



      from Journal a
      where a.AC_NO in ('664120000001',
    '664200000001',
    '664300000001')
      group by 
        a.AC_BRANCH)




    select 
        ST.BRANCH_CODE,
        ST.BRANCH_NAME,
        sum(ST.STOCK_PROVISION) as STOCK_PROVISION,
        max(nvl(PC.Provision_comptabilisee, 0)) as PROVISION_COMPTABILISEE
    from Stock_Provision ST
    left join PROVISION_COMPTABILISE PC on PC.AC_BRANCH=ST.BRANCH_CODE
    group by ST.BRANCH_CODE,
        ST.BRANCH_NAME
    """
    
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        logger.info("📊 Exécution de la requête Stock Provision...")
        logger.info(f"📝 Date utilisée dans la requête: date_end_str={date_end_str}, date_end_sql={date_end_sql}")
        logger.debug(f"📝 Requête SQL (premiers 1000 caractères): {query[:1000]}...")
        try:
            cursor.execute(query)
        except Exception as sql_error:
            logger.error(f"❌ Erreur SQL détaillée: {str(sql_error)}")
            logger.error(f"❌ Requête SQL complète:\n{query}")
            raise
        
        # Récupérer les noms de colonnes
        columns = [desc[0] for desc in cursor.description]
        
        # Récupérer toutes les lignes
        rows = cursor.fetchall()
        
        # Convertir en liste de dictionnaires
        result = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convertir les nombres en float si nécessaire
                if isinstance(value, (int, float)):
                    row_dict[col] = float(value) if value is not None else 0
                else:
                    row_dict[col] = value
            result.append(row_dict)
        
        cursor.close()
        connection.close()
        
        logger.info(f"✅ {len(result)} lignes récupérées pour Stock Provision")
        
        # Organiser les données par territoire
        hierarchical_data = organize_stock_data_by_territory(result)
        
        return hierarchical_data
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"❌ Erreur lors de la récupération des données Stock Provision: {error_message}")
        logger.error(f"❌ Détails de l'erreur:\n{error_detail}", exc_info=True)
        # Afficher aussi la requête pour déboguer
        logger.error(f"❌ Requête SQL complète:\n{query}")
        logger.error(f"❌ Dates utilisées: date_end_str='{date_end_str}', date_end_sql='{date_end_sql}'")
        raise Exception(f"Erreur SQL Stock Provision: {error_message}")


def organize_stock_data_by_territory(data: List[Dict]) -> Dict:
    """
    Organise les données de stock provision par territoire
    
    Args:
        data: Liste de dictionnaires avec les données brutes (BRANCH_CODE, BRANCH_NAME, STOCK_PROVISION, PROVISION_COMPTABILISEE)
    
    Returns:
        Dictionnaire avec la structure hiérarchique organisée par territoire
    """
    hierarchical = {
        "TERRITOIRE": {},
        "POINT SERVICES": {}
    }
    
    # Mapping des noms de territoires vers les clés
    territory_key_map = {
        'DAKAR CENTRE VILLE': 'territoire_dakar_ville',
        'DAKAR BANLIEUE': 'territoire_dakar_banlieue',
        'PROVINCE CENTRE SUD': 'territoire_province_centre_sud',
        'PROVINCE NORD': 'territoire_province_nord'
    }
    
    # Noms complets des territoires
    territory_names = {
        'territoire_dakar_ville': 'TERRITOIRE DAKAR VILLE',
        'territoire_dakar_banlieue': 'TERRITOIRE DAKAR BANLIEUE',
        'territoire_province_centre_sud': 'TERRITOIRE PROVINCE CENTRE-SUD',
        'territoire_province_nord': 'TERRITOIRE PROVINCE NORD'
    }
    
    # Organiser les agences par territoire
    agencies_by_territory = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    # Pour les points de service et grand compte
    service_points_agencies = []
    grand_compte_agency = None
    
    for row in data:
        branch_name = row.get('BRANCH_NAME', '').upper()
        branch_code = str(row.get('BRANCH_CODE', ''))
        agency_data = {
            'BRANCH_CODE': row.get('BRANCH_CODE'),
            'BRANCH_NAME': row.get('BRANCH_NAME'),
            'STOCK_PROVISION': row.get('STOCK_PROVISION', 0),
            'PROVISION_COMPTABILISEE': row.get('PROVISION_COMPTABILISEE', 0)
        }
        
        # Vérifier si c'est le grand compte
        if 'GRAND COMPTE' in branch_name:
            grand_compte_agency = agency_data
            continue
        
        # Vérifier si c'est un point de service
        is_service_point = False
        normalized_name = ' '.join(branch_name.split())
        agency_name_without_prefix = normalized_name.replace('C-E ', '').replace('CE ', '').replace('COFINA EXPRESS ', '').strip()
        
        for service_point_name in SERVICE_POINT_MAPPING.keys():
            service_point_str = str(service_point_name) if service_point_name else ''
            service_point_normalized = ' '.join(service_point_str.upper().split())
            service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
            
            if (service_point_normalized == normalized_name or 
                service_point_without_prefix == agency_name_without_prefix or
                service_point_normalized in normalized_name or 
                normalized_name in service_point_normalized or
                (service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5) or
                (agency_name_without_prefix in service_point_without_prefix and len(agency_name_without_prefix) > 5)):
                is_service_point = True
                logger.info(f"✅ Point de service identifié (Stock): {row.get('BRANCH_NAME')} -> {service_point_name}")
                break
        
        if is_service_point:
            service_points_agencies.append(agency_data)
            continue
        
        # Trouver le territoire correspondant
        territory_name = None
        
        # Chercher dans le mapping par nom d'agence
        for key, territory in AGENCY_TERRITORY_MAPPING.items():
            if key.upper() in branch_name:
                territory_name = territory
                break
        
        # Si aucun territoire trouvé, utiliser DAKAR CENTRE VILLE par défaut
        if not territory_name:
            territory_name = 'DAKAR CENTRE VILLE'
            logger.warning(f"⚠️ Territoire non trouvé pour {branch_name}, assigné à DAKAR CENTRE VILLE")
        
        # Obtenir la clé du territoire
        territory_key = territory_key_map.get(territory_name, 'territoire_dakar_ville')
        
        # Ajouter l'agence au territoire
        agencies_by_territory[territory_key].append(agency_data)
    
    # Construire la structure hiérarchique avec les totaux
    for territory_key in ['territoire_dakar_ville', 'territoire_dakar_banlieue', 
                          'territoire_province_centre_sud', 'territoire_province_nord']:
        agencies = agencies_by_territory[territory_key]
        
        if agencies:
            # Calculer les totaux du territoire
            total_stock_provision = sum(ag.get('STOCK_PROVISION', 0) for ag in agencies)
            total_provision_comptabilisee = sum(ag.get('PROVISION_COMPTABILISEE', 0) for ag in agencies)
            
            hierarchical["TERRITOIRE"][territory_key] = {
                "name": territory_names[territory_key],
                "agencies": agencies,
                "totals": {
                    "stockProvision": total_stock_provision,
                    "provisionComptabilisee": total_provision_comptabilisee
                }
            }
    
    # Ajouter le grand compte dans TERRITOIRE si présent
    if grand_compte_agency:
        hierarchical["TERRITOIRE"]["grand_compte"] = {
            "name": "GRAND COMPTE",
            "agencies": [grand_compte_agency],
            "totals": {
                "stockProvision": grand_compte_agency.get('STOCK_PROVISION', 0),
                "provisionComptabilisee": grand_compte_agency.get('PROVISION_COMPTABILISEE', 0)
            }
        }
    
    # Ajouter les points de service
    if service_points_agencies:
        total_stock_provision_sp = sum(ag.get('STOCK_PROVISION', 0) for ag in service_points_agencies)
        total_provision_comptabilisee_sp = sum(ag.get('PROVISION_COMPTABILISEE', 0) for ag in service_points_agencies)
        
        hierarchical["POINT SERVICES"]["service_points"] = {
            "name": "POINT SERVICES",
            "agencies": service_points_agencies,
            "totals": {
                "stockProvision": total_stock_provision_sp,
                "provisionComptabilisee": total_provision_comptabilisee_sp
            }
        }
    
    logger.info(f"📊 Structure hiérarchique créée: {len(agencies_by_territory['territoire_dakar_ville'])} agences DAKAR VILLE, "
               f"{len(agencies_by_territory['territoire_dakar_banlieue'])} DAKAR BANLIEUE, "
               f"{len(agencies_by_territory['territoire_province_centre_sud'])} PROVINCE CENTRE-SUD, "
               f"{len(agencies_by_territory['territoire_province_nord'])} PROVINCE NORD, "
               f"{len(service_points_agencies)} points de service, "
               f"{'1' if grand_compte_agency else '0'} grand compte")
    
    return hierarchical
