"""
Service pour la gestion des données clients
"""
import logging
from typing import Optional
from database.oracle import get_oracle_connection
from services.utils import calculate_period_dates, get_territory_from_agency, get_territory_key, get_all_territories, SERVICE_POINT_MAPPING

logger = logging.getLogger(__name__)


def get_clients_data(period: str = "month", zone: Optional[str] = None, 
                     month: Optional[int] = None, year: Optional[int] = None, date: Optional[str] = None):
    """
    Récupère les données clients depuis Oracle dans le format attendu par le dashboard
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
    
    Returns:
        Dictionnaire avec les données clients organisées par zones
    """
    logger.info(f"🔍 get_clients_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}")
    
    # Utiliser le pool de connexions et le cache
    from database.oracle_pool import get_pool
    from services.cache_service import get_cache, set_cache, generate_cache_key
    
    # Générer une clé de cache basée sur les paramètres
    cache_key = f"clients:{generate_cache_key(period, zone, month, year, date)}"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données clients récupérées depuis le cache")
        return cached_result
    
    # Calculer les dates
    dates = calculate_period_dates(period, month, year, date)
    date_m_debut_str = dates['date_m_debut_str']
    date_m_fin_str = dates['date_m_fin_str']
    date_m1_debut_str = dates['date_m1_debut_str']
    date_m1_fin_str = dates['date_m1_fin_str']
    
    logger.info(f"📅 Dates utilisées pour la requête Oracle: M={date_m_debut_str} à {date_m_fin_str}, M-1={date_m1_debut_str} à {date_m1_fin_str}")
    
    # Requête SQL basée sur la requête fournie
    query = """
    with  udf_client_dc as (
        select
            sc.CUSTOMER_NO "MATRICULE_CLIENT"
            ,b.BRANCH_CODE  as CODE_BUREAU
            ,b.BRANCH_NAME as AGENCE
        from CFSFCUBS145.STTM_CUSTOMER sc
        left join CFSFCUBS145.STTM_BRANCH b on b.BRANCH_CODE = sc.LOCAL_BRANCH
        where sc.customer_no not like '000001'
    ),
    RESULT_M as (
        select
            sc.CUSTOMER_NO as MATRICULE_CLIENT
            ,b.BRANCH_CODE  as CODE_BUREAU
            ,b.BRANCH_NAME as AGENCE
        from CFSFCUBS145.STTM_CUSTOMER sc
        left join CFSFCUBS145.STTM_BRANCH b on b.BRANCH_CODE = sc.LOCAL_BRANCH
        where SC.CIF_CREATION_DATE between TO_DATE(:1, 'DD/MM/YYYY') and TO_DATE(:2, 'DD/MM/YYYY')
            and sc.CUSTOMER_CATEGORY <>'219'
            and sc.CUSTOMER_CATEGORY <> '006'
            and sc.MAKER_ID <> 'APIUSER1'
    ),
    RESULT_M_1 as (
        select
            sc.CUSTOMER_NO as MATRICULE_CLIENT_1
            ,b.BRANCH_CODE  as CODE_BUREAU
            ,b.BRANCH_NAME as AGENCE
        from CFSFCUBS145.STTM_CUSTOMER sc
        left join CFSFCUBS145.STTM_BRANCH b on b.BRANCH_CODE = sc.LOCAL_BRANCH
        where SC.CIF_CREATION_DATE between TO_DATE(:3, 'DD/MM/YYYY') and TO_DATE(:4, 'DD/MM/YYYY')
            and sc.CUSTOMER_CATEGORY <>'219'
            and sc.CUSTOMER_CATEGORY <> '006'
            and sc.MAKER_ID <> 'APIUSER1'
    ),
    NBRE_M as (
        select 
            rm.CODE_BUREAU,
            rm.AGENCE,
            count(rm.MATRICULE_CLIENT) as Nbre_Client_M
        from RESULT_M rm
        group by rm.CODE_BUREAU, rm.AGENCE
    ),
    NBRE_M_1 as (
        select 
            rm1.CODE_BUREAU,
            rm1.AGENCE,
            count(rm1.MATRICULE_CLIENT_1) as Nbre_Client_M_1
        from RESULT_M_1 rm1
        group by rm1.AGENCE, rm1.CODE_BUREAU
    ),
    -- Requête pour les frais d'ouverture de compte
    -- Inclure tous les comptes de frais d'ouverture (commençant par 70293)
    -- pour capturer les frais de toutes les agences, y compris le grand compte
    Journal AS (
        SELECT
            a.TRN_REF_NO,
            a.AC_ENTRY_SR_NO,
            a.AC_BRANCH,
            a.AC_NO,
            a.DRCR_IND,
            a.LCY_AMOUNT,
            a.VALUE_DT,
            a.VALUE_DT AS TRN_DT
        FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES a
        WHERE a.AC_NO LIKE '70293%'
        -- Inclure aussi les comptes spécifiques mentionnés dans la requête originale
        OR a.AC_NO IN (
            '702930000272','702930000273','702930000274','702930000275',
            '702930000276','702930000277','702930000278','702930000279',
            '702930000280','702930000281','702930000282','702930000283',
            '702930000284','702930000285','702930000286','702930000287',
            '702930000288','702930000289','702930000290','702930000291',
            '702930000292','702930000293','702930000294','702930000295',
            '702930000296','702930000297','702930000298'
        )
    ),
    RESULT_FRAIS_M AS (
        SELECT
            j.AC_BRANCH AS CODE_AGENCE,
            b.BRANCH_NAME AS AGENCE,
            DECODE(j.DRCR_IND,'C',j.LCY_AMOUNT,0) AS MOUVEMENT_CREDIT
        FROM Journal j
        LEFT JOIN CFSFCUBS145.STTM_BRANCH b
            ON b.BRANCH_CODE = j.AC_BRANCH
        WHERE j.TRN_DT BETWEEN TO_DATE(:1, 'DD/MM/YYYY') AND TO_DATE(:2, 'DD/MM/YYYY')
    ),
    RESULT_FRAIS_M_1 AS (
        SELECT
            j.AC_BRANCH AS CODE_AGENCE,
            DECODE(j.DRCR_IND,'C',j.LCY_AMOUNT,0) AS MOUVEMENT_CREDIT
        FROM Journal j
        WHERE j.TRN_DT BETWEEN TO_DATE(:3, 'DD/MM/YYYY') AND TO_DATE(:4, 'DD/MM/YYYY')
    ),
    FRAIS_OUV_M AS (
        SELECT
            CODE_AGENCE,
            AGENCE,
            SUM(MOUVEMENT_CREDIT) AS FRAIS_OUVERTURE_COMPTE_M
        FROM RESULT_FRAIS_M
        GROUP BY CODE_AGENCE, AGENCE
    ),
    FRAIS_OUV_M_1 AS (
        SELECT
            CODE_AGENCE,
            SUM(MOUVEMENT_CREDIT) AS FRAIS_OUVERTURE_COMPTE_M_1
        FROM RESULT_FRAIS_M_1
        GROUP BY CODE_AGENCE
    )
    select 
        COALESCE(nb.CODE_BUREAU, nb1.CODE_BUREAU, fm.CODE_AGENCE, gc.CODE_BUREAU) as CODE_BUREAU,
        COALESCE(nb.AGENCE, nb1.AGENCE, fm.AGENCE, gc.AGENCE) as AGENCE,
        NVL(nb.Nbre_Client_M, 0) as Nbre_Client_M,
        NVL(nb1.Nbre_Client_M_1, 0) as Nbre_Client_M_1,
        ROUND(
            (((NVL(nb.Nbre_Client_M, 0) - NVL(nb1.Nbre_Client_M_1, 0))) / NULLIF(nb1.Nbre_Client_M_1, 0)) * 100, 
            2
        ) AS VARIATION_POURCENT,
        ROUND(
            ((NVL(nb.Nbre_Client_M, 0)) / NULLIF(nb1.Nbre_Client_M_1, 0)) * 100, 
            2
        ) AS POURCENT_REALISATION,
        NVL(fm.FRAIS_OUVERTURE_COMPTE_M, 0) as FRAIS_M,
        NVL(fm1.FRAIS_OUVERTURE_COMPTE_M_1, 0) as FRAIS_M_1
    from NBRE_M nb
    full outer join NBRE_M_1 nb1 on nb1.CODE_BUREAU = nb.CODE_BUREAU
    full outer join FRAIS_OUV_M fm on fm.CODE_AGENCE = COALESCE(nb.CODE_BUREAU, nb1.CODE_BUREAU)
    full outer join FRAIS_OUV_M_1 fm1 on fm1.CODE_AGENCE = COALESCE(nb.CODE_BUREAU, nb1.CODE_BUREAU, fm.CODE_AGENCE)
    -- S'assurer que le grand compte apparaît même s'il n'a pas de données
    full outer join (
        SELECT BRANCH_CODE as CODE_BUREAU, BRANCH_NAME as AGENCE
        FROM CFSFCUBS145.STTM_BRANCH
        WHERE UPPER(BRANCH_NAME) LIKE '%GRAND%COMPTE%'
    ) gc on gc.CODE_BUREAU = COALESCE(nb.CODE_BUREAU, nb1.CODE_BUREAU, fm.CODE_AGENCE)
    order by COALESCE(nb.CODE_BUREAU, nb1.CODE_BUREAU, fm.CODE_AGENCE, gc.CODE_BUREAU)
    """
    
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        
        # Optimisations Oracle
        cursor.arraysize = 1000
        cursor.prefetchrows = 1000
        
        # Exécuter la requête avec les paramètres positionnels
        # Oracle compte chaque occurrence de :1, :2, :3, :4 dans toute la requête
        # Comme ils sont utilisés deux fois (clients et frais), on doit passer les valeurs deux fois
        cursor.execute(query, [
            date_m_debut_str,      # :1 pour RESULT_M
            date_m_fin_str,        # :2 pour RESULT_M
            date_m1_debut_str,     # :3 pour RESULT_M_1
            date_m1_fin_str,       # :4 pour RESULT_M_1
            date_m_debut_str,      # :1 pour RESULT_FRAIS_M (réutilisé mais Oracle le compte)
            date_m_fin_str,        # :2 pour RESULT_FRAIS_M
            date_m1_debut_str,     # :3 pour RESULT_FRAIS_M_1
            date_m1_fin_str        # :4 pour RESULT_FRAIS_M_1
        ])
        
        # Récupérer les colonnes et les données
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        logger.info(f"📊 Nombre de lignes retournées par Oracle (clients): {len(rows)}")
        if len(rows) > 0:
            logger.info(f"   Première ligne: {dict(zip(columns, rows[0]))}")
        
        # Convertir en liste de dictionnaires
        results = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            # Convertir les Decimal en float pour JSON et gérer les valeurs NULL
            for key, value in row_dict.items():
                if value is None:
                    if key in ['Nbre_Client_M', 'Nbre_Client_M_1', 'VARIATION_POURCENT', 'POURCENT_REALISATION', 'FRAIS_M', 'FRAIS_M_1']:
                        row_dict[key] = 0
                    else:
                        row_dict[key] = None
                elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                    try:
                        row_dict[key] = float(value)
                    except (ValueError, TypeError):
                        row_dict[key] = 0
            results.append(row_dict)
        
        cursor.close()
    
    logger.info(f"📊 Nombre d'agences après traitement: {len(results)}")
    
    # Vérifier si le grand compte est dans les résultats
    grand_compte_in_results = False
    for agence_data in results:
        agence_name = agence_data.get('AGENCE') or agence_data.get('Agence') or ''
        if agence_name and ('GRAND COMPTE' in str(agence_name).upper() or 'GRAND_COMPTE' in str(agence_name).upper()):
            grand_compte_in_results = True
            logger.info(f"✅ Grand compte trouvé dans les résultats: {agence_name}")
            break
    
    if not grand_compte_in_results:
        logger.warning("⚠️ Grand compte non trouvé dans les résultats SQL, il sera créé avec des valeurs à 0")
    
    # Transformer les résultats dans le format attendu par le frontend
    # Utiliser le nouveau zonage avec les territoires
    territories_data = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    grand_compte = None
    
    # Mapping selon le nouveau zonage
    for agence_data in results:
        # Récupérer le nom de l'agence en gérant les valeurs None
        agence_name = agence_data.get('AGENCE') or agence_data.get('Agence') or 'Inconnu'
        if agence_name is None:
            agence_name = 'Inconnu'
        
        # Oracle retourne les colonnes en majuscules, donc utiliser les deux variantes
        nbre_client_m = agence_data.get('NBRE_CLIENT_M') or agence_data.get('Nbre_Client_M') or 0
        nbre_client_m1 = agence_data.get('NBRE_CLIENT_M_1') or agence_data.get('Nbre_Client_M_1') or 0
        variation_pourcent = agence_data.get('VARIATION_POURCENT') or agence_data.get('Variation_Pourcent') or 0
        
        # Récupérer les frais d'ouverture de compte
        frais_m = float(agence_data.get('FRAIS_M') or agence_data.get('Frais_M') or 0)
        frais_m1 = float(agence_data.get('FRAIS_M_1') or agence_data.get('Frais_M_1') or 0)
        variation_frais = frais_m - frais_m1
        taux_croissance_frais = (frais_m1 > 0) and ((variation_frais / frais_m1) * 100) or 0
        
        # Vérifier si c'est le grand compte (vérifier que agence_name est une chaîne avant d'appeler upper())
        agence_name_upper = str(agence_name).upper() if agence_name else ''
        if 'GRAND COMPTE' in agence_name_upper or 'GRAND_COMPTE' in agence_name_upper:
            grand_compte = {
                'name': agence_name,
                'nouveauxClientsM': int(nbre_client_m or 0),
                'nouveauxClientsM1': int(nbre_client_m1 or 0),
                'variationClients': int(nbre_client_m or 0) - int(nbre_client_m1 or 0),
                'tauxCroissanceClients': float(variation_pourcent or 0),
                'fraisM': frais_m,
                'fraisM1': frais_m1,
                'variationFrais': variation_frais,
                'tauxCroissanceFrais': taux_croissance_frais
            }
            continue
        
        agency_obj = {
            'name': agence_name,
            'nouveauxClientsM': int(nbre_client_m or 0),
            'nouveauxClientsM1': int(nbre_client_m1 or 0),
            'variationClients': int(nbre_client_m or 0) - int(nbre_client_m1 or 0),
            'tauxCroissanceClients': float(variation_pourcent or 0),
            'fraisM': frais_m,
            'fraisM1': frais_m1,
            'variationFrais': variation_frais,
            'tauxCroissanceFrais': taux_croissance_frais
        }
        
        # Utiliser le nouveau mapping de territoire
        territory = get_territory_from_agency(agence_name)
        if territory:
            territory_key = get_territory_key(territory)
            if territory_key in territories_data:
                territories_data[territory_key].append(agency_obj)
                logger.debug(f"✅ Agence {agence_name} assignée à {territory}")
            else:
                # Si le territoire n'est pas reconnu, mettre dans DAKAR VILLE par défaut
                logger.warning(f"⚠️ Territoire non reconnu pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                territories_data['territoire_dakar_ville'].append(agency_obj)
        else:
            # Si aucune correspondance, mettre dans DAKAR VILLE par défaut
            logger.warning(f"⚠️ Aucun territoire trouvé pour l'agence '{agence_name}', assigné à DAKAR VILLE par défaut")
            territories_data['territoire_dakar_ville'].append(agency_obj)
    
    # Logger le nombre d'agences par territoire pour débogage
    logger.info(f"📊 Répartition des agences par territoire:")
    for territory_key, agencies in territories_data.items():
        logger.info(f"   {territory_key}: {len(agencies)} agences")
        if agencies:
            logger.info(f"      Agences: {[a['name'] for a in agencies[:5]]}")  # Afficher les 5 premières
    
    # Calculer les totaux globaux
    total_mois = sum(
        sum(agency.get('nouveauxClientsM', 0) for agency in agencies)
        for agencies in territories_data.values()
    )
    
    total_mois1 = sum(
        sum(agency.get('nouveauxClientsM1', 0) for agency in agencies)
        for agencies in territories_data.values()
    )
    
    # Ajouter le grand compte aux totaux si présent
    if grand_compte:
        total_mois += grand_compte.get('nouveauxClientsM', 0)
        total_mois1 += grand_compte.get('nouveauxClientsM1', 0)
    
    total_variation = total_mois - total_mois1
    evolution = round((total_variation / (total_mois1 or 1)) * 100, 2) if total_mois1 > 0 else 0
    
    # TODO: Calculer cumulAnnee - nécessitera une requête supplémentaire pour l'année complète
    cumul_annee = 0
    
    # Obtenir la structure complète des territoires
    try:
        all_territories = get_all_territories()
        # Vérifier que toutes les clés nécessaires sont présentes
        required_keys = ['territoire_dakar_ville', 'territoire_dakar_banlieue', 
                        'territoire_province_centre_sud', 'territoire_province_nord']
        for key in required_keys:
            if key not in all_territories:
                logger.error(f"❌ Clé manquante dans all_territories: {key}")
                raise KeyError(f"Clé manquante dans all_territories: {key}")
            if 'name' not in all_territories[key]:
                logger.error(f"❌ Clé 'name' manquante pour {key} dans all_territories")
                raise KeyError(f"Clé 'name' manquante pour {key} dans all_territories")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de all_territories: {e}", exc_info=True)
        # Créer une structure par défaut en cas d'erreur
        all_territories = {
            'territoire_dakar_ville': {'name': 'TERRITOIRE DAKAR VILLE'},
            'territoire_dakar_banlieue': {'name': 'TERRITOIRE DAKAR BANLIEUE'},
            'territoire_province_centre_sud': {'name': 'TERRITOIRE PROVINCE CENTRE SUD'},
            'territoire_province_nord': {'name': 'TERRITOIRE PROVINCE NORD'}
        }
        logger.warning("⚠️ Utilisation de la structure par défaut pour all_territories")
    
    # Séparer les points de service des agences
    # Les points de service sont des agences spéciales qui doivent être affichés séparément
    service_points_data = []
    agencies_by_territory = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    # Identifier et séparer les points de service
    for territory_key, agencies in territories_data.items():
        for agency in agencies:
            agency_name = agency.get('name') or 'Inconnu'
            if agency_name is None:
                agency_name = 'Inconnu'
            agency_name_upper = str(agency_name).upper().strip()
            # Normaliser le nom (supprimer les tirets, espaces multiples, etc.)
            agency_name_normalized = ' '.join(agency_name_upper.split())
            
            # Vérifier si c'est un point de service
            is_service_point = False
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_upper = str(service_point_name).upper().strip() if service_point_name else ''
                service_point_normalized = ' '.join(service_point_upper.split())
                
                # Normaliser aussi en supprimant les préfixes comme "C-E" pour comparaison
                agency_name_without_prefix = agency_name_normalized.replace('C-E ', '').replace('CE ', '').strip()
                service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
                
                # Vérifier plusieurs conditions pour une meilleure détection
                # 1. Correspondance exacte (après normalisation)
                if service_point_normalized == agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - exact): {agency_name} -> {service_point_name}")
                    break
                
                # 2. Correspondance sans préfixe
                if service_point_without_prefix == agency_name_without_prefix:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - sans préfixe): {agency_name} -> {service_point_name}")
                    break
                
                # 3. Le nom de l'agence contient le nom du point de service
                if service_point_normalized in agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - contient): {agency_name} -> {service_point_name}")
                    break
                
                # 4. Le nom de l'agence (sans préfixe) contient le nom du point de service (sans préfixe)
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - contient sans préfixe): {agency_name} -> {service_point_name}")
                    break
                
                # 5. Le nom du point de service contient le nom de l'agence (pour les cas courts)
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - inclus): {agency_name} -> {service_point_name}")
                    break
                
                # 6. Correspondance par mots-clés significatifs (pour gérer les variations)
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                agency_words = [w for w in agency_name_normalized.split() if len(w) > 3]
                
                # Si au moins 2 mots significatifs correspondent
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (clients - mots-clés): {agency_name} -> {service_point_name} (mots: {matching_words})")
                    break
            
            if not is_service_point:
                agencies_by_territory[territory_key].append(agency)
    
    # Logger le nombre de points de service détectés
    logger.info(f"📊 Nombre total de points de service détectés (clients): {len(service_points_data)}")
    if service_points_data:
        service_point_names = [ag.get('name', ag.get('AGENCE', 'Inconnu')) for ag in service_points_data]
        logger.info(f"📋 Points de service détectés (clients): {', '.join(service_point_names)}")
    else:
        logger.warning("⚠️ Aucun point de service détecté dans les données clients")
    
    # Construire la réponse dans le nouveau format hiérarchique
    # Niveau 1: TERRITOIRE et POINT SERVICES
    # Niveau 2: Les 4 territoires
    # Niveau 3: Les agences
    # Vérifier que toutes les clés nécessaires sont présentes avant de construire la réponse
    territory_keys = ['territoire_dakar_ville', 'territoire_dakar_banlieue', 
                      'territoire_province_centre_sud', 'territoire_province_nord']
    for key in territory_keys:
        if key not in all_territories:
            logger.error(f"❌ Clé manquante dans all_territories lors de la construction de la réponse: {key}")
            raise KeyError(f"Clé manquante dans all_territories: {key}")
        if key not in agencies_by_territory:
            logger.error(f"❌ Clé manquante dans agencies_by_territory lors de la construction de la réponse: {key}")
            raise KeyError(f"Clé manquante dans agencies_by_territory: {key}")
    
    response_data = {
        "globalResult": {
            "mois": total_mois,
            "mois1": total_mois1,
            "evolution": evolution,
            "cumulAnnee": cumul_annee
        },
        # Nouvelle structure hiérarchique
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": all_territories['territoire_dakar_ville']['name'],
                    "agencies": agencies_by_territory['territoire_dakar_ville']
                },
                "territoire_dakar_banlieue": {
                    "name": all_territories['territoire_dakar_banlieue']['name'],
                    "agencies": agencies_by_territory['territoire_dakar_banlieue']
                },
                "territoire_province_centre_sud": {
                    "name": all_territories['territoire_province_centre_sud']['name'],
                    "agencies": agencies_by_territory['territoire_province_centre_sud']
                },
                "territoire_province_nord": {
                    "name": all_territories['territoire_province_nord']['name'],
                    "agencies": agencies_by_territory['territoire_province_nord']
                }
            },
            "POINT SERVICES": {
                "service_points": {
                    "name": "POINTS SERVICES",
                    "agencies": service_points_data
                }
            }
        },
        # Format territories pour compatibilité
        "territories": {
            "territoire_dakar_ville": {
                "name": all_territories['territoire_dakar_ville']['name'],
                "agencies": agencies_by_territory['territoire_dakar_ville']
            },
            "territoire_dakar_banlieue": {
                "name": all_territories['territoire_dakar_banlieue']['name'],
                "agencies": agencies_by_territory['territoire_dakar_banlieue']
            },
            "territoire_province_centre_sud": {
                "name": all_territories['territoire_province_centre_sud']['name'],
                "agencies": agencies_by_territory['territoire_province_centre_sud']
            },
            "territoire_province_nord": {
                "name": all_territories['territoire_province_nord']['name'],
                "agencies": agencies_by_territory['territoire_province_nord']
            }
        },
        # Compatibilité avec l'ancien format (zone1/zone2)
        "corporateZones": {
            "zone1": {
                "name": "TERRITOIRE DAKAR VILLE",
                "agencies": agencies_by_territory['territoire_dakar_ville']
            },
            "zone2": {
                "name": "TERRITOIRE PROVINCE CENTRE-SUD",
                "agencies": agencies_by_territory['territoire_province_centre_sud']
            }
        },
        "retailZones": {
            "zone1": {
                "name": "TERRITOIRE DAKAR BANLIEUE",
                "agencies": agencies_by_territory['territoire_dakar_banlieue']
            },
            "zone2": {
                "name": "TERRITOIRE PROVINCE NORD",
                "agencies": agencies_by_territory['territoire_province_nord']
            }
        }
    }
    
    # Ajouter le grand compte si disponible, sinon créer un grand compte avec des valeurs à 0
    if grand_compte:
        response_data["grandCompte"] = grand_compte
        logger.info(f"✅ Grand compte ajouté: {grand_compte.get('name', 'Inconnu')}")
    else:
        # Créer un grand compte avec des valeurs à 0 si aucun grand compte n'a été trouvé
        response_data["grandCompte"] = {
            'name': 'AGENCE GRAND COMPTE',
            'nouveauxClientsM': 0,
            'nouveauxClientsM1': 0,
            'variationClients': 0,
            'tauxCroissanceClients': 0,
            'fraisM': 0,
            'fraisM1': 0,
            'variationFrais': 0,
            'tauxCroissanceFrais': 0
        }
        logger.info("⚠️ Grand compte créé avec des valeurs à 0 (aucune donnée trouvée)")
    
    # Mettre en cache le résultat (TTL de 5 minutes)
    set_cache(cache_key, response_data, ttl=300)
    
    return response_data

