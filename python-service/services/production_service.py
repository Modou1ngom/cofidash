"""
Service pour la gestion des données de production
"""
import logging
from datetime import datetime, date, timedelta
import calendar
from typing import Optional
from database.oracle import get_oracle_connection
from services.utils import get_territory_from_agency, get_territory_key, get_all_territories, SERVICE_POINT_MAPPING

logger = logging.getLogger(__name__)


def get_production_nombre_data(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """
    Récupère les données de production en nombre (nombre de crédits décaissés par agence) depuis Oracle.
    Basé sur la requête de ProNombre.py
    
    Args:
        date_m_debut: Date de début du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise le 1er du mois courant.
        date_m_fin: Date de fin du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise la date du jour.
        month: Mois à analyser (1-12). Si fourni avec year, calcule automatiquement les dates.
        year: Année à analyser. Si fourni avec month, calcule automatiquement les dates.
    
    Returns:
        Données de production par agence avec comparaison M vs M-1
    """
    # Calcul des dates si month et year sont fournis
    if month and year:
        date_m_debut_obj = date(year, month, 1)
        date_m_fin_obj = date(year, month, calendar.monthrange(year, month)[1])
        
        # Calcul du mois précédent (M-1)
        if month == 1:
            date_m1_debut_obj = date(year - 1, 12, 1)
            date_m1_fin_obj = date(year - 1, 12, 31)
        else:
            date_m1_debut_obj = date(year, month - 1, 1)
            date_m1_fin_obj = date(year, month - 1, calendar.monthrange(year, month - 1)[1])
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    elif year and not month:
        # Si seule l'année est fournie, comparer année complète avec année précédente
        date_m_debut_obj = date(year, 1, 1)
        date_m_fin_obj = date(year, 12, 31)
        
        date_m1_debut_obj = date(year - 1, 1, 1)
        date_m1_fin_obj = date(year - 1, 12, 31)
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    else:
        # Utiliser les dates fournies ou les dates par défaut
        if date_m_debut:
            date_m_debut_obj = datetime.strptime(date_m_debut, "%d/%m/%Y").date()
        else:
            today = date.today()
            date_m_debut_obj = today.replace(day=1)
        
        if date_m_fin:
            date_m_fin_obj = datetime.strptime(date_m_fin, "%d/%m/%Y").date()
        else:
            date_m_fin_obj = date.today()
        
        # Calcul automatique du mois précédent (M-1)
        first_day_m = date_m_debut_obj.replace(day=1)
        last_day_prev_month = first_day_m - timedelta(days=1)
        date_m1_debut_obj = last_day_prev_month.replace(day=1)
        date_m1_fin_obj = last_day_prev_month
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    
    # Connexion à Oracle
    conn = get_oracle_connection()
    cursor = conn.cursor()
    
    # Utilisation de paramètres positionnels pour oracledb
    sql_query = """
    WITH BRANCH AS (
        SELECT BRANCH_CODE, BRANCH_NAME
        FROM CFSFCUBS145.STTM_BRANCH
    ),
    DEBLOCAGE AS (
        SELECT
            y.ACCOUNT_NUMBER,
            COALESCE(y.DTYPE, 'VIDE') AS DTYPE,
            MAX(y.SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES y
        WHERE (y.DTYPE <> 'X' OR y.DTYPE IS NULL)
        GROUP BY y.ACCOUNT_NUMBER, COALESCE(y.DTYPE, 'VIDE')
    ),
    PRODUCTION_M AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:1, 'DD/MM/YYYY')
                                     AND TO_DATE(:2, 'DD/MM/YYYY')
    ),
    PRODUCTION_M_1 AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:3, 'DD/MM/YYYY')
                                     AND TO_DATE(:4, 'DD/MM/YYYY')
    ),
    OBJECTIF_PRODUCTION AS (
        SELECT  
            BRANCH_CODE,
            BRANCH_NAME,
            DECODE(
                BRANCH_CODE,
                501, 200,
                502, 300,
                503, 600,
                0
            ) AS OBJECTIF_PRODUCTION
        FROM CFSFCUBS145.STTM_BRANCH
    ),
    NBRE_DOSSIER_M AS (
        SELECT 
            BRANCH_CODE,
            BRANCH_NAME,
            COUNT(NO_PRET) AS NOMBRE_DE_CREDITS_DECAISSES_M
        FROM PRODUCTION_M
        GROUP BY BRANCH_CODE, BRANCH_NAME
    ),
    NBRE_DOSSIER_M_1 AS (
        SELECT 
            BRANCH_CODE,
            BRANCH_NAME,
            COUNT(NO_PRET) AS NOMBRE_DE_CREDITS_DECAISSES_M_1
        FROM PRODUCTION_M_1
        GROUP BY BRANCH_CODE, BRANCH_NAME
    ),
    ALL_BRANCHES AS (
        SELECT BRANCH_CODE, BRANCH_NAME FROM NBRE_DOSSIER_M
        UNION
        SELECT BRANCH_CODE, BRANCH_NAME FROM NBRE_DOSSIER_M_1
    )
    SELECT 
        AB.BRANCH_CODE AS CODE_AGENCE,
        AB.BRANCH_NAME AS AGENCE,
        COALESCE(OB.OBJECTIF_PRODUCTION, 0) AS OBJECTIF_PRODUCTION,
        COALESCE(NBM1.NOMBRE_DE_CREDITS_DECAISSES_M_1, 0) AS NOMBRE_DE_CREDITS_DECAISSES_M_1,
        COALESCE(NBM.NOMBRE_DE_CREDITS_DECAISSES_M, 0) AS NOMBRE_DE_CREDITS_DECAISSES_M,
        (COALESCE(NBM.NOMBRE_DE_CREDITS_DECAISSES_M, 0) - COALESCE(NBM1.NOMBRE_DE_CREDITS_DECAISSES_M_1, 0)) AS VARIATION_NOMBRE,
        ROUND(
            ((COALESCE(NBM.NOMBRE_DE_CREDITS_DECAISSES_M, 0) - COALESCE(NBM1.NOMBRE_DE_CREDITS_DECAISSES_M_1, 0))
            / NULLIF(COALESCE(NBM1.NOMBRE_DE_CREDITS_DECAISSES_M_1, 0), 0)) * 100, 2
        ) AS VARIATION_POURCENT,
        ROUND(
            (COALESCE(NBM.NOMBRE_DE_CREDITS_DECAISSES_M, 0) / NULLIF(COALESCE(OB.OBJECTIF_PRODUCTION, 0), 0)) * 100, 2
        ) AS TAUX_REALISATION
    FROM ALL_BRANCHES AB
    LEFT JOIN NBRE_DOSSIER_M NBM 
           ON NBM.BRANCH_CODE = AB.BRANCH_CODE
    LEFT JOIN NBRE_DOSSIER_M_1 NBM1 
           ON NBM1.BRANCH_CODE = AB.BRANCH_CODE
    LEFT JOIN OBJECTIF_PRODUCTION OB 
           ON OB.BRANCH_CODE = AB.BRANCH_CODE
    ORDER BY AB.BRANCH_CODE
    """
    
    # Exécuter la requête avec les paramètres positionnels
    cursor.execute(sql_query, [
        date_m_debut_str,
        date_m_fin_str,
        date_m1_debut_str,
        date_m1_fin_str
    ])
    
    # Récupérer les colonnes et les données
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convertir en liste de dictionnaires
    results = []
    for row in rows:
        row_dict = dict(zip(columns, row))
        # Convertir les Decimal en float pour JSON et gérer les valeurs NULL
        for key, value in row_dict.items():
            if value is None:
                # Mettre à 0 pour les valeurs numériques NULL
                if key in ['NOMBRE_DE_CREDITS_DECAISSES_M', 'NOMBRE_DE_CREDITS_DECAISSES_M_1', 
                           'VARIATION_NOMBRE', 'VARIATION_POURCENT', 'TAUX_REALISATION', 
                           'OBJECTIF_PRODUCTION']:
                    row_dict[key] = 0
                else:
                    row_dict[key] = None
            elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                # Convertir Decimal en float
                try:
                    row_dict[key] = float(value)
                except (ValueError, TypeError):
                    row_dict[key] = 0
        results.append(row_dict)
    
    # Requête pour récupérer les détails par CAF (déclinaison par charge d'affaire)
    sql_query_caf = """
    WITH BRANCH AS (
        SELECT BRANCH_CODE, BRANCH_NAME
        FROM CFSFCUBS145.STTM_BRANCH
    ),
    DEBLOCAGE AS (
        SELECT
            y.ACCOUNT_NUMBER,
            COALESCE(y.DTYPE, 'VIDE') AS DTYPE,
            MAX(y.SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES y
        WHERE (y.DTYPE <> 'X' OR y.DTYPE IS NULL)
        GROUP BY y.ACCOUNT_NUMBER, COALESCE(y.DTYPE, 'VIDE')
    ),
    PRODUCTION_M AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:1, 'DD/MM/YYYY')
                                     AND TO_DATE(:2, 'DD/MM/YYYY')
    ),
    PRODUCTION_M_1 AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:3, 'DD/MM/YYYY')
                                     AND TO_DATE(:4, 'DD/MM/YYYY')
    ),
    NBRE_DOSSIER_M AS (
        SELECT 
            p.BRANCH_CODE AS Code_Agence,
            p.BRANCH_NAME AS Agence,
            COALESCE(p.CHARGE_AFFAIRE, 'NON ASSIGNE') AS CHARGE_AFFAIRE,
            MAX(p.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
            COUNT(p.NO_PRET) AS Nombre_Dossiers_M
        FROM PRODUCTION_M p
        GROUP BY p.BRANCH_CODE, p.BRANCH_NAME, COALESCE(p.CHARGE_AFFAIRE, 'NON ASSIGNE')
    ),
    NBRE_DOSSIER_M_1 AS (
        SELECT 
            p1.BRANCH_CODE AS Code_Agence,
            p1.BRANCH_NAME AS Agence,
            COALESCE(p1.CHARGE_AFFAIRE, 'NON ASSIGNE') AS CHARGE_AFFAIRE,
            MAX(p1.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
            COUNT(p1.NO_PRET) AS Nombre_Dossiers_M_1
        FROM PRODUCTION_M_1 p1
        GROUP BY p1.BRANCH_CODE, p1.BRANCH_NAME, COALESCE(p1.CHARGE_AFFAIRE, 'NON ASSIGNE')
    )
    SELECT 
        COALESCE(m.Code_Agence, m1.Code_Agence) AS Code_Agence,
        COALESCE(m.Agence, m1.Agence) AS Agence,
        COALESCE(m.CHARGE_AFFAIRE, m1.CHARGE_AFFAIRE) AS CHARGE_AFFAIRE,
        COALESCE(m.CODE_GESTION_PRET, m1.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
        COALESCE(m.Nombre_Dossiers_M, 0) AS Nombre_Dossiers_M,
        COALESCE(m1.Nombre_Dossiers_M_1, 0) AS Nombre_Dossiers_M_1,
        (COALESCE(m.Nombre_Dossiers_M, 0) - COALESCE(m1.Nombre_Dossiers_M_1, 0)) as Variation_nombre,
        ROUND(
            (((COALESCE(m.Nombre_Dossiers_M, 0) - COALESCE(m1.Nombre_Dossiers_M_1, 0)) / NULLIF(COALESCE(m1.Nombre_Dossiers_M_1, 0), 0)) * 100), 
            2
        ) AS VARIATION_PCT
    FROM NBRE_DOSSIER_M m
    FULL OUTER JOIN NBRE_DOSSIER_M_1 m1
        ON m.Code_Agence = m1.Code_Agence
       AND m.CHARGE_AFFAIRE = m1.CHARGE_AFFAIRE
    ORDER BY COALESCE(m.Code_Agence, m1.Code_Agence), COALESCE(m.CHARGE_AFFAIRE, m1.CHARGE_AFFAIRE)
    """
    
    # Exécuter la requête pour les détails par CAF
    cursor.execute(sql_query_caf, [
        date_m_debut_str,
        date_m_fin_str,
        date_m1_debut_str,
        date_m1_fin_str
    ])
    
    # Récupérer les colonnes et les données pour les CAF
    columns_caf = [desc[0] for desc in cursor.description]
    rows_caf = cursor.fetchall()
    
    # Traiter les données par CAF pour créer le dictionnaire chargeAffaireDetails
    charge_affaire_data = {}
    for row in rows_caf:
        row_dict = dict(zip(columns_caf, row))
        # Convertir les Decimal en float pour JSON (Oracle retourne les noms de colonnes en majuscules)
        for key, value in row_dict.items():
            if value is None:
                if key and key.upper() in ['NOMBRE_DOSSIERS_M', 'NOMBRE_DOSSIERS_M_1', 'VARIATION_NOMBRE', 'VARIATION_PCT']:
                    row_dict[key] = 0
                else:
                    row_dict[key] = None
            elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                try:
                    row_dict[key] = float(value)
                except (ValueError, TypeError):
                    row_dict[key] = 0
        
        # Utiliser le CODE_AGENCE comme clé (comme dans collection_service)
        branch_code = str(row_dict.get('CODE_AGENCE', '') or '')
        if branch_code:
            if branch_code not in charge_affaire_data:
                charge_affaire_data[branch_code] = {}
            
            # Utiliser CHARGE_AFFAIRE comme clé secondaire
            # Gérer les cas où CHARGE_AFFAIRE est NULL ou vide
            charge_affaire = row_dict.get('CHARGE_AFFAIRE')
            if not charge_affaire or (isinstance(charge_affaire, str) and charge_affaire.strip() == ''):
                charge_affaire = 'NON ASSIGNE'
            
            # Oracle retourne les noms de colonnes en majuscules (ex: NOMBRE_DOSSIERS_M)
            nbre_m = float(row_dict.get('NOMBRE_DOSSIERS_M') or row_dict.get('Nombre_Dossiers_M', 0) or 0)
            nbre_m1 = float(row_dict.get('NOMBRE_DOSSIERS_M_1') or row_dict.get('Nombre_Dossiers_M_1', 0) or 0)
            var_nb = float(row_dict.get('VARIATION_NOMBRE') or row_dict.get('Variation_nombre', 0) or 0)
            var_pct = float(row_dict.get('VARIATION_PCT', 0) or 0)
            if charge_affaire not in charge_affaire_data[branch_code]:
                charge_affaire_data[branch_code][charge_affaire] = {
                    'chargeAffaire': charge_affaire,
                    'CHARGE_AFFAIRE': charge_affaire,
                    'codeGestion': row_dict.get('CODE_GESTION_PRET', '-') or '-',
                    'CODE_GESTION': row_dict.get('CODE_GESTION_PRET', '-') or '-',
                    'nombreDossiersM': nbre_m,
                    'NOMBRE_DOSSIERS_M': nbre_m,
                    'nombreDossiersM1': nbre_m1,
                    'NOMBRE_DOSSIERS_M_1': nbre_m1,
                    'variationNombre': var_nb,
                    'VARIATION_NOMBRE': var_nb,
                    'variationPct': var_pct,
                    'VARIATION_PCT': var_pct
                }
    
    # Convertir le dictionnaire en format liste pour chaque agence (comme dans collection_service)
    charge_affaire_by_agency = {}
    for agency_key, charges in charge_affaire_data.items():
        charge_affaire_by_agency[agency_key] = list(charges.values())
    
    cursor.close()
    conn.close()
    
    # Organiser les données par territoire selon le nouveau zonage
    territories_data = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    # Grouper les résultats par territoire
    # Les points de service seront séparés plus tard, donc on les met temporairement dans un territoire
    # pour qu'ils soient traités dans la boucle de séparation
    for row in results:
        agence_name = row.get('AGENCE', 'Inconnu')
        territory = get_territory_from_agency(agence_name)
        
        if territory:
            territory_key = get_territory_key(territory)
            if territory_key in territories_data:
                territories_data[territory_key].append(row)
            else:
                # Si le territoire n'est pas reconnu, mettre dans DAKAR VILLE par défaut
                logger.warning(f"⚠️ Territoire non reconnu pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                territories_data['territoire_dakar_ville'].append(row)
        else:
            # Vérifier si c'est un point de service avant d'assigner un territoire par défaut
            # Les points de service seront séparés plus tard, donc on les met temporairement dans DAKAR VILLE
            # pour qu'ils soient traités dans la boucle de séparation
            agency_name_upper = agence_name.upper().strip()
            agency_name_normalized = ' '.join(agency_name_upper.split())
            is_service_point = False
            
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_normalized = ' '.join(service_point_name.upper().split())
                if (service_point_normalized == agency_name_normalized or
                    service_point_normalized in agency_name_normalized or
                    agency_name_normalized in service_point_normalized):
                    is_service_point = True
                    break
            
            if not is_service_point:
                # Si ce n'est pas un point de service et qu'aucun territoire n'est trouvé, mettre dans DAKAR VILLE par défaut
                logger.warning(f"⚠️ Aucun territoire trouvé pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                territories_data['territoire_dakar_ville'].append(row)
            else:
                # C'est un point de service, le mettre temporairement dans DAKAR VILLE pour qu'il soit traité dans la boucle de séparation
                territories_data['territoire_dakar_ville'].append(row)
    
    # Calculer les totaux globaux
    total_m = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M', 0) or 0 for r in results)
    total_m1 = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M_1', 0) or 0 for r in results)
    total_variation = total_m - total_m1
    total_variation_pct = round((total_variation / (total_m1 or 1)) * 100, 2) if total_m1 > 0 else 0
    
    # Obtenir la structure complète des territoires
    all_territories = get_all_territories()
    
    # Séparer les points de service des agences
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
            agence_name = agency.get('AGENCE', 'Inconnu')
            agency_name_upper = agence_name.upper().strip()
            # Normaliser le nom (supprimer les tirets, espaces multiples, etc.)
            agency_name_normalized = ' '.join(agency_name_upper.split())
            
            # Vérifier si c'est un point de service
            is_service_point = False
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_upper = service_point_name.upper().strip()
                service_point_normalized = ' '.join(service_point_upper.split())
                
                # Normaliser aussi en supprimant les préfixes comme "C-E" pour comparaison
                agency_name_without_prefix = agency_name_normalized.replace('C-E ', '').replace('CE ', '').strip()
                service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
                
                # Vérifier plusieurs conditions pour une meilleure détection
                # 1. Correspondance exacte (après normalisation)
                if service_point_normalized == agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - exact): {agence_name} -> {service_point_name}")
                    break
                
                # 2. Correspondance sans préfixe
                if service_point_without_prefix == agency_name_without_prefix:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - sans préfixe): {agence_name} -> {service_point_name}")
                    break
                
                # 3. Le nom de l'agence contient le nom du point de service
                if service_point_normalized in agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - contient): {agence_name} -> {service_point_name}")
                    break
                
                # 4. Le nom de l'agence (sans préfixe) contient le nom du point de service (sans préfixe)
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - contient sans préfixe): {agence_name} -> {service_point_name}")
                    break
                
                # 5. Le nom du point de service contient le nom de l'agence (pour les cas courts)
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - inclus): {agence_name} -> {service_point_name}")
                    break
                
                # 6. Correspondance par mots-clés significatifs (pour gérer les variations)
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                agency_words = [w for w in agency_name_normalized.split() if len(w) > 3]
                
                # Si au moins 2 mots significatifs correspondent
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    service_points_data.append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - mots-clés): {agence_name} -> {service_point_name} (mots: {matching_words})")
                    break
            
            if not is_service_point:
                agencies_by_territory[territory_key].append(agency)
    
    # Calculer les totaux par territoire
    territories_totals = {}
    for territory_key, territory_rows in agencies_by_territory.items():
        territory_total_m = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M', 0) or 0 for r in territory_rows)
        territory_total_m1 = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M_1', 0) or 0 for r in territory_rows)
        territory_total_objectif = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in territory_rows)
        territory_variation = territory_total_m - territory_total_m1
        territory_variation_pct = round((territory_variation / (territory_total_m1 or 1)) * 100, 2) if territory_total_m1 > 0 else 0
        territory_atteinte = round((territory_total_m / (territory_total_objectif or 1)) * 100, 2) if territory_total_objectif > 0 else 0
        
        territories_totals[territory_key] = {
            'mois': territory_total_m,
            'mois1': territory_total_m1,
            'objectif': territory_total_objectif,
            'variation': territory_variation,
            'variation_pourcent': territory_variation_pct,
            'atteinte': territory_atteinte
        }
    
    # Calculer les totaux des points de service
    service_points_total_m = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M', 0) or 0 for r in service_points_data)
    service_points_total_m1 = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M_1', 0) or 0 for r in service_points_data)
    service_points_total_objectif = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in service_points_data)
    service_points_variation = service_points_total_m - service_points_total_m1
    service_points_variation_pct = round((service_points_variation / (service_points_total_m1 or 1)) * 100, 2) if service_points_total_m1 > 0 else 0
    service_points_atteinte = round((service_points_total_m / (service_points_total_objectif or 1)) * 100, 2) if service_points_total_objectif > 0 else 0
    
    # Logger les points de service détectés
    if service_points_data:
        service_point_names = [r.get('AGENCE', 'Inconnu') for r in service_points_data]
        logger.info(f"📋 Points de service détectés (production): {', '.join(service_point_names)}")
        logger.info(f"📊 Nombre de points de service: {len(service_points_data)}")
    else:
        logger.warning("⚠️ Aucun point de service détecté dans les données de production")
    
    # Construire la réponse dans le nouveau format hiérarchique
    # Niveau 1: TERRITOIRE et POINT SERVICES
    # Niveau 2: Les 4 territoires
    # Niveau 3: Les agences
    return {
        "period": {
            "m": {
                "debut": date_m_debut_str,
                "fin": date_m_fin_str
            },
            "m1": {
                "debut": date_m1_debut_str,
                "fin": date_m1_fin_str
            }
        },
        "total": {
            "mois": total_m,
            "mois1": total_m1,
            "variation": total_variation,
            "variation_pourcent": total_variation_pct
        },
        # Nouvelle structure hiérarchique
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": all_territories['territoire_dakar_ville']['name'],
                    "data": agencies_by_territory['territoire_dakar_ville'],
                    "total": territories_totals.get('territoire_dakar_ville', {})
                },
                "territoire_dakar_banlieue": {
                    "name": all_territories['territoire_dakar_banlieue']['name'],
                    "data": agencies_by_territory['territoire_dakar_banlieue'],
                    "total": territories_totals.get('territoire_dakar_banlieue', {})
                },
                "territoire_province_centre_sud": {
                    "name": all_territories['territoire_province_centre_sud']['name'],
                    "data": agencies_by_territory['territoire_province_centre_sud'],
                    "total": territories_totals.get('territoire_province_centre_sud', {})
                },
                "territoire_province_nord": {
                    "name": all_territories['territoire_province_nord']['name'],
                    "data": agencies_by_territory['territoire_province_nord'],
                    "total": territories_totals.get('territoire_province_nord', {})
                }
            },
            "POINT SERVICES": {
                "service_points": {
                    "name": "POINTS SERVICES",
                    "data": service_points_data,
                    "total": {
                        "mois": service_points_total_m,
                        "mois1": service_points_total_m1,
                        "objectif": service_points_total_objectif,
                        "variation": service_points_variation,
                        "variation_pourcent": service_points_variation_pct,
                        "atteinte": service_points_atteinte
                    }
                }
            }
        },
        # Format territories pour compatibilité
        "territories": {
            "territoire_dakar_ville": {
                "name": all_territories['territoire_dakar_ville']['name'],
                "data": agencies_by_territory['territoire_dakar_ville'],
                "total": territories_totals.get('territoire_dakar_ville', {})
            },
            "territoire_dakar_banlieue": {
                "name": all_territories['territoire_dakar_banlieue']['name'],
                "data": agencies_by_territory['territoire_dakar_banlieue'],
                "total": territories_totals.get('territoire_dakar_banlieue', {})
            },
            "territoire_province_centre_sud": {
                "name": all_territories['territoire_province_centre_sud']['name'],
                "data": agencies_by_territory['territoire_province_centre_sud'],
                "total": territories_totals.get('territoire_province_centre_sud', {})
            },
            "territoire_province_nord": {
                "name": all_territories['territoire_province_nord']['name'],
                "data": agencies_by_territory['territoire_province_nord'],
                "total": territories_totals.get('territoire_province_nord', {})
            }
        },
        "data": results,  # Garder les données brutes pour compatibilité
        "count": len(results),
        "chargeAffaireDetails": charge_affaire_by_agency  # Détails par charge d'affaire (CAF)
    }


def get_production_volume_data(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """
    Récupère les données de production en volume (montant de crédits décaissés par agence) depuis Oracle.
    Basé sur la requête SQL fournie qui calcule le volume débloqué (AMOUNT_FINANCED).
    
    Args:
        date_m_debut: Date de début du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise le 1er du mois courant.
        date_m_fin: Date de fin du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise la date du jour.
        month: Mois à analyser (1-12). Si fourni avec year, calcule automatiquement les dates.
        year: Année à analyser. Si fourni avec month, calcule automatiquement les dates.
    
    Returns:
        Données de production en volume par agence avec comparaison M vs M-1, incluant les frais de dossier
    """
    # Calcul des dates si month et year sont fournis
    if month and year:
        date_m_debut_obj = date(year, month, 1)
        date_m_fin_obj = date(year, month, calendar.monthrange(year, month)[1])
        
        # Calcul du mois précédent (M-1)
        if month == 1:
            date_m1_debut_obj = date(year - 1, 12, 1)
            date_m1_fin_obj = date(year - 1, 12, 31)
        else:
            date_m1_debut_obj = date(year, month - 1, 1)
            date_m1_fin_obj = date(year, month - 1, calendar.monthrange(year, month - 1)[1])
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    elif year and not month:
        # Si seule l'année est fournie, comparer année complète avec année précédente
        date_m_debut_obj = date(year, 1, 1)
        date_m_fin_obj = date(year, 12, 31)
        
        date_m1_debut_obj = date(year - 1, 1, 1)
        date_m1_fin_obj = date(year - 1, 12, 31)
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    else:
        # Utiliser les dates fournies ou les dates par défaut
        if date_m_debut:
            date_m_debut_obj = datetime.strptime(date_m_debut, "%d/%m/%Y").date()
        else:
            today = date.today()
            date_m_debut_obj = today.replace(day=1)
        
        if date_m_fin:
            date_m_fin_obj = datetime.strptime(date_m_fin, "%d/%m/%Y").date()
        else:
            date_m_fin_obj = date.today()
        
        # Calcul automatique du mois précédent (M-1)
        first_day_m = date_m_debut_obj.replace(day=1)
        last_day_prev_month = first_day_m - timedelta(days=1)
        date_m1_debut_obj = last_day_prev_month.replace(day=1)
        date_m1_fin_obj = last_day_prev_month
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    
    # Connexion à Oracle
    conn = get_oracle_connection()
    cursor = conn.cursor()
    
    # Requête SQL basée sur celle fournie par l'utilisateur
    sql_query = """
    WITH BRANCH AS (
        SELECT BRANCH_CODE, BRANCH_NAME
        FROM cfsfcubs145.STTM_BRANCH
    ),
    JOURNAL_DETTE_RATTACHEE AS (
        SELECT
            A.AC_BRANCH,
            A.AC_ENTRY_SR_NO,
            A.AMOUNT_TAG,
            A.RELATED_ACCOUNT,
            A.RELATED_CUSTOMER,
            A.AUTH_ID,
            A.USER_ID,
            A.module,
            A.event,
            A.TRN_CODE,
            A.DRCR_IND,
            A.BATCH_NO,
            A.AC_NO,
            CPT.ACCOUNT_CLASS,
            CL.DESCRIPTION,
            A.TRN_REF_NO AS NO_TRANSACT,
            A.LCY_AMOUNT AS DETTE_RATTACHEE,
            CPT.ACY_CURR_BALANCE AS SOLDE_COMPTABLE,
            DECODE(CPT.RECORD_STAT, 'O', 'OUVERT', 'C', 'FERME') AS STATUT,
            A.trn_dt,
            A.VALUE_DT
        FROM
            cfsfcubs145.ACVW_ALL_AC_ENTRIES A
        LEFT JOIN cfsfcubs145.STTM_CUST_ACCOUNT CPT ON A.AC_NO = CPT.CUST_AC_NO
        LEFT JOIN cfsfcubs145.STTM_ACCOUNT_CLASS CL ON CPT.ACCOUNT_CLASS = CL.ACCOUNT_CLASS
        WHERE
            A.DRCR_IND = 'C'
            AND A.TRN_CODE IN ('045')
            AND A.EVENT = 'IACR'
    ),
    RESULT_DETTE_RAT_M AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(JL8.DETTE_RATTACHEE) AS DETTE_RATTACHEE
        FROM JOURNAL_DETTE_RATTACHEE JL8
        LEFT JOIN BRANCH BR ON JL8.AC_BRANCH = BR.BRANCH_CODE
        WHERE JL8.VALUE_DT BETWEEN TO_DATE(:1, 'DD/MM/YYYY') AND TO_DATE(:2, 'DD/MM/YYYY')
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    ),
    RESULT_DETTE_RAT_M_1 AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(JL8.DETTE_RATTACHEE) AS DETTE_RATTACHEE
        FROM JOURNAL_DETTE_RATTACHEE JL8
        LEFT JOIN BRANCH BR ON JL8.AC_BRANCH = BR.BRANCH_CODE
        WHERE JL8.VALUE_DT BETWEEN TO_DATE(:7, 'DD/MM/YYYY') AND TO_DATE(:8, 'DD/MM/YYYY')
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    ),
    DEBLOCAGE AS (
        SELECT
            y.ACCOUNT_NUMBER,
            COALESCE(y.DTYPE, 'VIDE') AS DTYPE,
            MAX(y.SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES y
        WHERE (y.DTYPE <> 'X' OR y.DTYPE IS NULL)
        GROUP BY y.ACCOUNT_NUMBER, COALESCE(y.DTYPE, 'VIDE')
    ),
    UDF_PRET AS (
        SELECT
            p.ACCOUNT_NUMBER,
            p.FIELD_CHAR_2 AS CODE_GESTION_PRET,
            (SELECT MAX(u.LOV_DESC)
             FROM CFSFCUBS145.UDTM_LOV u 
             WHERE u.FIELD_NAME = 'GESTION_PRET'
               AND u.LOV = p.FIELD_CHAR_2) AS CHARGE_AFFAIRE
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER p
    ),
    PRODUCTION_M AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.AMOUNT_FINANCED,
            SUM(NVL(z.AMOUNT_DUE, 0)) AS MT_CAPITAL_TA,
            SUM(NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) AS ENCOURS_TOTAL_M,
            SUM(CASE 
                    WHEN w.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                    THEN (NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) 
                    ELSE 0 
                END) AS ENCOURS_SAIN_M,
            SUM(CASE 
                    WHEN w.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                    THEN (NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) 
                    ELSE 0 
                END) AS ENCOURS_IMPAYE_M
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
               ON z.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN DEBLOCAGE d 
               ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br 
               ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE 
            w.ACCOUNT_STATUS NOT IN ('L', 'V')
            AND z.COMPONENT_NAME = 'PRINCIPAL'
            AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:3, 'DD/MM/YYYY') 
                                       AND TO_DATE(:4, 'DD/MM/YYYY')
        GROUP BY w.ACCOUNT_NUMBER, w.BRANCH_CODE, br.BRANCH_NAME, w.FIELD_CHAR_2, w.AMOUNT_FINANCED, U1.LOV_DESC
    ),
    PRODUCTION_M_1 AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.AMOUNT_FINANCED,
            SUM(NVL(z.AMOUNT_DUE, 0)) AS MT_CAPITAL_TA,
            SUM(NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) AS ENCOURS_TOTAL_M,
            SUM(CASE 
                    WHEN w.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                    THEN (NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) 
                    ELSE 0 
                END) AS ENCOURS_SAIN_M,
            SUM(CASE 
                    WHEN w.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                    THEN (NVL(z.AMOUNT_DUE, 0) - NVL(z.AMOUNT_SETTLED, 0)) 
                    ELSE 0 
                END) AS ENCOURS_IMPAYE_M
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
               ON z.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN DEBLOCAGE d 
               ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br 
               ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE 
            w.ACCOUNT_STATUS NOT IN ('L', 'V')
            AND z.COMPONENT_NAME = 'PRINCIPAL'
            AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:5, 'DD/MM/YYYY') 
                                       AND TO_DATE(:6, 'DD/MM/YYYY')
        GROUP BY w.ACCOUNT_NUMBER, w.BRANCH_CODE, br.BRANCH_NAME, w.FIELD_CHAR_2, w.AMOUNT_FINANCED, U1.LOV_DESC
    ),
    OBJECTIF_PRODUCTION AS (
        SELECT  
            BRANCH_CODE,
            BRANCH_NAME,
            DECODE(
                BRANCH_CODE,
                501, 2000000000,
                502, 3000000000,
                503, 600000000,
                0
            ) AS OBJECTIF_PRODUCTION
        FROM CFSFCUBS145.STTM_BRANCH
    ),
    Volume_Debloque AS (
        SELECT 
            p.BRANCH_CODE AS Code_Agence,
            p.BRANCH_NAME AS Agence,
            SUM(p.AMOUNT_FINANCED) AS Volume_Debloque
        FROM PRODUCTION_M p
        GROUP BY p.BRANCH_CODE, p.BRANCH_NAME
    ),
    Volume_Debloque_1 AS (
        SELECT 
            p1.BRANCH_CODE AS Code_Agence,
            p1.BRANCH_NAME AS Agence,
            SUM(p1.AMOUNT_FINANCED) AS Volume_Debloque_1
        FROM PRODUCTION_M_1 p1
        GROUP BY p1.BRANCH_CODE, p1.BRANCH_NAME
    ),
    Frais_Dossier_M AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            COALESCE(SUM(RDR.DETTE_RATTACHEE), 0) AS FRAIS_DOSSIER
        FROM BRANCH BR
        LEFT JOIN RESULT_DETTE_RAT_M RDR ON RDR.BRANCH_CODE = BR.BRANCH_CODE
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    ),
    Frais_Dossier_M_1 AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            COALESCE(SUM(RDR.DETTE_RATTACHEE), 0) AS FRAIS_DOSSIER
        FROM BRANCH BR
        LEFT JOIN RESULT_DETTE_RAT_M_1 RDR ON RDR.BRANCH_CODE = BR.BRANCH_CODE
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    )
    SELECT 
        NBM.Code_Agence,
        NBM.Agence,
        OB.OBJECTIF_PRODUCTION,
        COALESCE(NBM1.Volume_Debloque_1, 0) AS VOLUME_CREDIT_DECAISSE_M_1,
        COALESCE(NBM.Volume_Debloque, 0) AS VOLUME_CREDIT_DECAISSE_M,
        (COALESCE(NBM.Volume_Debloque, 0) - COALESCE(NBM1.Volume_Debloque_1, 0)) AS VARIATION_VOLUME,
        ROUND(
            (((COALESCE(NBM.Volume_Debloque, 0) - COALESCE(NBM1.Volume_Debloque_1, 0))) / NULLIF(COALESCE(NBM1.Volume_Debloque_1, 0), 0)) * 100, 
            2
        ) AS VARIATION_POURCENT,
        ROUND(
            ((COALESCE(NBM.Volume_Debloque, 0)) / NULLIF(OB.OBJECTIF_PRODUCTION, 0)) * 100, 
            2
        ) AS TAUX_REALISATION,
        COALESCE(FDM1.FRAIS_DOSSIER, 0) AS FRAIS_DOSSIER_M_1,
        COALESCE(FDM.FRAIS_DOSSIER, 0) AS FRAIS_DOSSIER_M,
        (COALESCE(FDM.FRAIS_DOSSIER, 0) - COALESCE(FDM1.FRAIS_DOSSIER, 0)) AS ECART_FRAIS,
        COALESCE(FDM.FRAIS_DOSSIER, 0) AS VARIATION_FRAIS
    FROM Volume_Debloque NBM
    LEFT JOIN Volume_Debloque_1 NBM1 ON NBM1.Code_Agence = NBM.Code_Agence
    LEFT JOIN OBJECTIF_PRODUCTION OB ON OB.BRANCH_CODE = NBM.Code_Agence
    LEFT JOIN Frais_Dossier_M FDM ON FDM.BRANCH_CODE = NBM.Code_Agence
    LEFT JOIN Frais_Dossier_M_1 FDM1 ON FDM1.BRANCH_CODE = NBM.Code_Agence
    ORDER BY NBM.Code_Agence
    """
    
    # Exécuter la requête avec les paramètres positionnels
    # :1, :2 = dates M pour frais de dossier
    # :3, :4 = dates M pour production
    # :5, :6 = dates M-1 pour production
    # :7, :8 = dates M-1 pour frais de dossier
    cursor.execute(sql_query, [
        date_m_debut_str,      # :1 - début M pour frais
        date_m_fin_str,        # :2 - fin M pour frais
        date_m_debut_str,      # :3 - début M pour production
        date_m_fin_str,        # :4 - fin M pour production
        date_m1_debut_str,     # :5 - début M-1 pour production
        date_m1_fin_str,       # :6 - fin M-1 pour production
        date_m1_debut_str,     # :7 - début M-1 pour frais 
        date_m1_fin_str        # :8 - fin M-1 pour frais
    ])
    
    # Récupérer les colonnes et les données
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convertir en liste de dictionnaires
    results = []
    for row in rows:
        row_dict = dict(zip(columns, row))
        # Convertir les Decimal en float pour JSON et gérer les valeurs NULL
        for key, value in row_dict.items():
            if value is None:
                if key in ['VOLUME_CREDIT_DECAISSE_M', 'VOLUME_CREDIT_DECAISSE_M_1', 
                           'VARIATION_VOLUME', 'VARIATION_POURCENT', 'TAUX_REALISATION', 
                           'OBJECTIF_PRODUCTION', 'FRAIS_DOSSIER_M', 'FRAIS_DOSSIER_M_1',
                           'ECART_FRAIS', 'VARIATION_FRAIS']:
                    row_dict[key] = 0
                else:
                    row_dict[key] = None
            elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                try:
                    row_dict[key] = float(value)
                except (ValueError, TypeError):
                    row_dict[key] = 0
        results.append(row_dict)
    
    # Requête pour récupérer les détails par CAF (déclinaison par charge d'affaire) - VOLUME
    sql_query_caf = """
    WITH BRANCH AS (
        SELECT BRANCH_CODE, BRANCH_NAME
        FROM cfsfcubs145.STTM_BRANCH
    ),
    DEBLOCAGE AS (
        SELECT
            y.ACCOUNT_NUMBER,
            COALESCE(y.DTYPE, 'VIDE') AS DTYPE,
            MAX(y.SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES y
        WHERE (y.DTYPE <> 'X' OR y.DTYPE IS NULL)
        GROUP BY y.ACCOUNT_NUMBER, COALESCE(y.DTYPE, 'VIDE')
    ),
    PRODUCTION_M AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.AMOUNT_FINANCED
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:1, 'DD/MM/YYYY')
                                     AND TO_DATE(:2, 'DD/MM/YYYY')
    ),
    PRODUCTION_M_1 AS (
        SELECT 
            w.ACCOUNT_NUMBER AS NO_PRET,
            w.BRANCH_CODE,
            br.BRANCH_NAME,
            w.FIELD_CHAR_2 AS CODE_GESTION_PRET,
            U1.LOV_DESC as CHARGE_AFFAIRE,
            w.AMOUNT_FINANCED
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER w
        LEFT JOIN DEBLOCAGE d ON d.ACCOUNT_NUMBER = w.ACCOUNT_NUMBER
        LEFT JOIN BRANCH br ON br.BRANCH_CODE = w.BRANCH_CODE
        LEFT JOIN CFSFCUBS145.UDTM_LOV U1 ON U1.FIELD_NAME='GESTION_PRET' and U1.LOV=w.FIELD_CHAR_2
        WHERE w.ACCOUNT_STATUS NOT IN ('L','V')
          AND d.SCHEDULE_LINKAGE BETWEEN TO_DATE(:3, 'DD/MM/YYYY')
                                     AND TO_DATE(:4, 'DD/MM/YYYY')
    ),
    VOLUME_DEBLOQUE_M AS (
        SELECT 
            p.BRANCH_CODE AS Code_Agence,
            p.BRANCH_NAME AS Agence,
            COALESCE(p.CHARGE_AFFAIRE, 'NON ASSIGNE') AS CHARGE_AFFAIRE,
            MAX(p.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
            SUM(p.AMOUNT_FINANCED) AS Volume_Debloque_M
        FROM PRODUCTION_M p
        GROUP BY p.BRANCH_CODE, p.BRANCH_NAME, COALESCE(p.CHARGE_AFFAIRE, 'NON ASSIGNE')
    ),
    VOLUME_DEBLOQUE_M_1 AS (
        SELECT 
            p1.BRANCH_CODE AS Code_Agence,
            p1.BRANCH_NAME AS Agence,
            COALESCE(p1.CHARGE_AFFAIRE, 'NON ASSIGNE') AS CHARGE_AFFAIRE,
            MAX(p1.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
            SUM(p1.AMOUNT_FINANCED) AS Volume_Debloque_M_1
        FROM PRODUCTION_M_1 p1
        GROUP BY p1.BRANCH_CODE, p1.BRANCH_NAME, COALESCE(p1.CHARGE_AFFAIRE, 'NON ASSIGNE')
    )
    SELECT 
        COALESCE(m.Code_Agence, m1.Code_Agence) AS Code_Agence,
        COALESCE(m.Agence, m1.Agence) AS Agence,
        COALESCE(m.CHARGE_AFFAIRE, m1.CHARGE_AFFAIRE) AS CHARGE_AFFAIRE,
        COALESCE(m.CODE_GESTION_PRET, m1.CODE_GESTION_PRET) AS CODE_GESTION_PRET,
        COALESCE(m.Volume_Debloque_M, 0) AS Volume_Debloque_M,
        COALESCE(m1.Volume_Debloque_M_1, 0) AS Volume_Debloque_M_1,
        (COALESCE(m.Volume_Debloque_M, 0) - COALESCE(m1.Volume_Debloque_M_1, 0)) as Variation_volume,
        ROUND(
            (((COALESCE(m.Volume_Debloque_M, 0) - COALESCE(m1.Volume_Debloque_M_1, 0)) / NULLIF(COALESCE(m1.Volume_Debloque_M_1, 0), 0)) * 100), 
            2
        ) AS VARIATION_PCT
    FROM VOLUME_DEBLOQUE_M m
    FULL OUTER JOIN VOLUME_DEBLOQUE_M_1 m1
        ON m.Code_Agence = m1.Code_Agence
       AND m.CHARGE_AFFAIRE = m1.CHARGE_AFFAIRE
    ORDER BY COALESCE(m.Code_Agence, m1.Code_Agence), COALESCE(m.CHARGE_AFFAIRE, m1.CHARGE_AFFAIRE)
    """
    
    # Exécuter la requête pour les détails par CAF
    cursor.execute(sql_query_caf, [
        date_m_debut_str,      # :1 - début M pour production
        date_m_fin_str,        # :2 - fin M pour production
        date_m1_debut_str,     # :3 - début M-1 pour production
        date_m1_fin_str        # :4 - fin M-1 pour production
    ])
    
    # Récupérer les colonnes et les données pour les CAF
    columns_caf = [desc[0] for desc in cursor.description]
    rows_caf = cursor.fetchall()
    
    logger.info(f"📊 Colonnes CAF (volume) retournées: {columns_caf}")
    logger.info(f"📊 Nombre de lignes CAF (volume): {len(rows_caf)}")
    if len(rows_caf) > 0:
        sample_row = dict(zip(columns_caf, rows_caf[0]))
        logger.info(f"📊 Exemple de ligne CAF (volume): Code_Agence={sample_row.get('CODE_AGENCE')}, Volume_M={sample_row.get('VOLUME_DEBLOQUE_M') or sample_row.get('Volume_Debloque_M')}, Volume_M1={sample_row.get('VOLUME_DEBLOQUE_M_1') or sample_row.get('Volume_Debloque_M_1')}")
    
    # Traiter les données par CAF pour créer le dictionnaire chargeAffaireDetails
    charge_affaire_data = {}
    for row in rows_caf:
        row_dict = dict(zip(columns_caf, row))
        # Convertir les Decimal en float pour JSON
        for key, value in row_dict.items():
            if value is None:
                # Gérer les noms de colonnes en majuscules et minuscules
                if key.upper() in ['VOLUME_DEBLOQUE_M', 'VOLUME_DEBLOQUE_M_1', 'VARIATION_VOLUME', 'VARIATION_PCT']:
                    row_dict[key] = 0
                else:
                    row_dict[key] = None
            elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                try:
                    row_dict[key] = float(value)
                except (ValueError, TypeError):
                    row_dict[key] = 0
        
        # Utiliser le CODE_AGENCE comme clé (comme dans collection_service)
        branch_code = str(row_dict.get('CODE_AGENCE', ''))
        if branch_code:
            if branch_code not in charge_affaire_data:
                charge_affaire_data[branch_code] = {}
            
            # Utiliser CHARGE_AFFAIRE comme clé secondaire
            # Gérer les cas où CHARGE_AFFAIRE est NULL ou vide
            charge_affaire = row_dict.get('CHARGE_AFFAIRE')
            if not charge_affaire or charge_affaire.strip() == '':
                charge_affaire = 'NON ASSIGNE'
            
            if charge_affaire not in charge_affaire_data[branch_code]:
                # Oracle retourne les noms de colonnes en majuscules, donc utiliser les deux formats
                volume_m = row_dict.get('VOLUME_DEBLOQUE_M') or row_dict.get('Volume_Debloque_M') or 0
                volume_m1 = row_dict.get('VOLUME_DEBLOQUE_M_1') or row_dict.get('Volume_Debloque_M_1') or 0
                variation_vol = row_dict.get('VARIATION_VOLUME') or row_dict.get('Variation_volume') or 0
                variation_pct = row_dict.get('VARIATION_PCT') or row_dict.get('Variation_PCT') or 0
                
                charge_affaire_data[branch_code][charge_affaire] = {
                    'chargeAffaire': charge_affaire,
                    'CHARGE_AFFAIRE': charge_affaire,
                    'codeGestion': row_dict.get('CODE_GESTION_PRET', '-'),
                    'CODE_GESTION': row_dict.get('CODE_GESTION_PRET', '-'),
                    'volumeDebloqueM': float(volume_m or 0),
                    'VOLUME_DEBLOQUE_M': float(volume_m or 0),
                    'volumeDebloqueM1': float(volume_m1 or 0),
                    'VOLUME_DEBLOQUE_M_1': float(volume_m1 or 0),
                    'variationVolume': float(variation_vol or 0),
                    'VARIATION_VOLUME': float(variation_vol or 0),
                    'variationPct': float(variation_pct or 0),
                    'VARIATION_PCT': float(variation_pct or 0)
                }
    
    # Convertir le dictionnaire en format liste pour chaque agence (comme dans collection_service)
    charge_affaire_by_agency = {}
    for agency_key, charges in charge_affaire_data.items():
        charge_affaire_by_agency[agency_key] = list(charges.values())
    
    # Logger pour déboguer
    if charge_affaire_by_agency:
        sample_key = list(charge_affaire_by_agency.keys())[0]
        if charge_affaire_by_agency[sample_key]:
            sample_caf = charge_affaire_by_agency[sample_key][0]
            logger.info(f"📊 Exemple CAF (volume) pour agence {sample_key}: volumeM={sample_caf.get('volumeDebloqueM')}, volumeM1={sample_caf.get('volumeDebloqueM1')}, variationPct={sample_caf.get('variationPct')}")
    
    cursor.close()
    conn.close()
    
    # Organiser les données par territoire (même logique que pour get_production_nombre_data)
    territories_data = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    for row in results:
        agence_name = row.get('AGENCE', 'Inconnu')
        territory = get_territory_from_agency(agence_name)
        
        if territory:
            territory_key = get_territory_key(territory)
            if territory_key in territories_data:
                territories_data[territory_key].append(row)
            else:
                logger.warning(f"⚠️ Territoire non reconnu pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                territories_data['territoire_dakar_ville'].append(row)
        else:
            agency_name_upper = agence_name.upper().strip()
            agency_name_normalized = ' '.join(agency_name_upper.split())
            is_service_point = False
            
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_normalized = ' '.join(service_point_name.upper().split())
                if (service_point_normalized == agency_name_normalized or
                    service_point_normalized in agency_name_normalized or
                    agency_name_normalized in service_point_normalized):
                    is_service_point = True
                    break
            
            if not is_service_point:
                logger.warning(f"⚠️ Aucun territoire trouvé pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                territories_data['territoire_dakar_ville'].append(row)
            else:
                territories_data['territoire_dakar_ville'].append(row)
    
    # Calculer les totaux globaux
    total_volume_m = sum(r.get('VOLUME_CREDIT_DECAISSE_M', 0) or 0 for r in results)
    total_volume_m1 = sum(r.get('VOLUME_CREDIT_DECAISSE_M_1', 0) or 0 for r in results)
    total_variation_volume = total_volume_m - total_volume_m1
    total_variation_pct = round((total_variation_volume / (total_volume_m1 or 1)) * 100, 2) if total_volume_m1 > 0 else 0
    total_frais_m = sum(r.get('FRAIS_DOSSIER_M', 0) or 0 for r in results)
    total_frais_m1 = sum(r.get('FRAIS_DOSSIER_M_1', 0) or 0 for r in results)
    total_ecart_frais = total_frais_m - total_frais_m1
    
    # Obtenir la structure complète des territoires
    all_territories = get_all_territories()
    
    # Séparer les points de service des agences
    service_points_data = []
    agencies_by_territory = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    # Identifier et séparer les points de service (même logique que get_production_nombre_data)
    for territory_key, agencies in territories_data.items():
        for agency in agencies:
            agence_name = agency.get('AGENCE', 'Inconnu')
            agency_name_upper = agence_name.upper().strip()
            agency_name_normalized = ' '.join(agency_name_upper.split())
            
            is_service_point = False
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_upper = service_point_name.upper().strip()
                service_point_normalized = ' '.join(service_point_upper.split())
                
                agency_name_without_prefix = agency_name_normalized.replace('C-E ', '').replace('CE ', '').strip()
                service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
                
                if service_point_normalized == agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix == agency_name_without_prefix:
                    service_points_data.append(agency)
                    is_service_point = True
                    break
                if service_point_normalized in agency_name_normalized:
                    service_points_data.append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    break
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    service_points_data.append(agency)
                    is_service_point = True
                    break
                
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    service_points_data.append(agency)
                    is_service_point = True
                    break
            
            if not is_service_point:
                agencies_by_territory[territory_key].append(agency)
    
    # Calculer les totaux par territoire
    territories_totals = {}
    for territory_key, territory_rows in agencies_by_territory.items():
        territory_total_volume_m = sum(r.get('VOLUME_CREDIT_DECAISSE_M', 0) or 0 for r in territory_rows)
        territory_total_volume_m1 = sum(r.get('VOLUME_CREDIT_DECAISSE_M_1', 0) or 0 for r in territory_rows)
        territory_total_objectif = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in territory_rows)
        territory_variation_volume = territory_total_volume_m - territory_total_volume_m1
        territory_variation_pct = round((territory_variation_volume / (territory_total_volume_m1 or 1)) * 100, 2) if territory_total_volume_m1 > 0 else 0
        territory_atteinte = round((territory_total_volume_m / (territory_total_objectif or 1)) * 100, 2) if territory_total_objectif > 0 else 0
        territory_frais_m = sum(r.get('FRAIS_DOSSIER_M', 0) or 0 for r in territory_rows)
        territory_frais_m1 = sum(r.get('FRAIS_DOSSIER_M_1', 0) or 0 for r in territory_rows)
        territory_ecart_frais = territory_frais_m - territory_frais_m1
        
        territories_totals[territory_key] = {
            'volumeM': territory_total_volume_m,
            'volumeM1': territory_total_volume_m1,
            'objectif': territory_total_objectif,
            'variationVolume': territory_variation_volume,
            'variation_pourcent': territory_variation_pct,
            'atteinte': territory_atteinte,
            'fraisM': territory_frais_m,
            'fraisM1': territory_frais_m1,
            'ecartFrais': territory_ecart_frais,
            'variationFrais': territory_frais_m
        }
    
    # Calculer les totaux des points de service
    service_points_total_volume_m = sum(r.get('VOLUME_CREDIT_DECAISSE_M', 0) or 0 for r in service_points_data)
    service_points_total_volume_m1 = sum(r.get('VOLUME_CREDIT_DECAISSE_M_1', 0) or 0 for r in service_points_data)
    service_points_total_objectif = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in service_points_data)
    service_points_variation_volume = service_points_total_volume_m - service_points_total_volume_m1
    service_points_variation_pct = round((service_points_variation_volume / (service_points_total_volume_m1 or 1)) * 100, 2) if service_points_total_volume_m1 > 0 else 0
    service_points_atteinte = round((service_points_total_volume_m / (service_points_total_objectif or 1)) * 100, 2) if service_points_total_objectif > 0 else 0
    service_points_frais_m = sum(r.get('FRAIS_DOSSIER_M', 0) or 0 for r in service_points_data)
    service_points_frais_m1 = sum(r.get('FRAIS_DOSSIER_M_1', 0) or 0 for r in service_points_data)
    service_points_ecart_frais = service_points_frais_m - service_points_frais_m1
    
    # Logger les points de service détectés
    if service_points_data:
        service_point_names = [r.get('AGENCE', 'Inconnu') for r in service_points_data]
        logger.info(f"📋 Points de service détectés (production volume): {', '.join(service_point_names)}")
        logger.info(f"📊 Nombre de points de service: {len(service_points_data)}")
    else:
        logger.warning("⚠️ Aucun point de service détecté dans les données de production volume")
    
    # Construire la réponse dans le nouveau format hiérarchique
    return {
        "period": {
            "m": {
                "debut": date_m_debut_str,
                "fin": date_m_fin_str
            },
            "m1": {
                "debut": date_m1_debut_str,
                "fin": date_m1_fin_str
            }
        },
        "total": {
            "volumeM": total_volume_m,
            "volumeM1": total_volume_m1,
            "variationVolume": total_variation_volume,
            "variation_pourcent": total_variation_pct,
            "fraisM": total_frais_m,
            "fraisM1": total_frais_m1,
            "ecartFrais": total_ecart_frais
        },
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": all_territories['territoire_dakar_ville']['name'],
                    "data": agencies_by_territory['territoire_dakar_ville'],
                    "total": territories_totals.get('territoire_dakar_ville', {})
                },
                "territoire_dakar_banlieue": {
                    "name": all_territories['territoire_dakar_banlieue']['name'],
                    "data": agencies_by_territory['territoire_dakar_banlieue'],
                    "total": territories_totals.get('territoire_dakar_banlieue', {})
                },
                "territoire_province_centre_sud": {
                    "name": all_territories['territoire_province_centre_sud']['name'],
                    "data": agencies_by_territory['territoire_province_centre_sud'],
                    "total": territories_totals.get('territoire_province_centre_sud', {})
                },
                "territoire_province_nord": {
                    "name": all_territories['territoire_province_nord']['name'],
                    "data": agencies_by_territory['territoire_province_nord'],
                    "total": territories_totals.get('territoire_province_nord', {})
                }
            },
            "POINT SERVICES": {
                "service_points": {
                    "name": "POINTS SERVICES",
                    "data": service_points_data,
                    "total": {
                        "volumeM": service_points_total_volume_m,
                        "volumeM1": service_points_total_volume_m1,
                        "objectif": service_points_total_objectif,
                        "variationVolume": service_points_variation_volume,
                        "variation_pourcent": service_points_variation_pct,
                        "atteinte": service_points_atteinte,
                        "fraisM": service_points_frais_m,
                        "fraisM1": service_points_frais_m1,
                        "ecartFrais": service_points_ecart_frais,
                        "variationFrais": service_points_frais_m
                    }
                }
            }
        },
        "territories": {
            "territoire_dakar_ville": {
                "name": all_territories['territoire_dakar_ville']['name'],
                "data": agencies_by_territory['territoire_dakar_ville'],
                "total": territories_totals.get('territoire_dakar_ville', {})
            },
            "territoire_dakar_banlieue": {
                "name": all_territories['territoire_dakar_banlieue']['name'],
                "data": agencies_by_territory['territoire_dakar_banlieue'],
                "total": territories_totals.get('territoire_dakar_banlieue', {})
            },
            "territoire_province_centre_sud": {
                "name": all_territories['territoire_province_centre_sud']['name'],
                "data": agencies_by_territory['territoire_province_centre_sud'],
                "total": territories_totals.get('territoire_province_centre_sud', {})
            },
            "territoire_province_nord": {
                "name": all_territories['territoire_province_nord']['name'],
                "data": agencies_by_territory['territoire_province_nord'],
                "total": territories_totals.get('territoire_province_nord', {})
            }
        },
        "data": results,
        "count": len(results),
        "chargeAffaireDetails": charge_affaire_by_agency  # Détails par charge d'affaire (CAF)
    }


def get_encours_credit_data(
    month_m: Optional[int] = None,
    year_m: Optional[int] = None,
    month_m1: Optional[int] = None,
    year_m1: Optional[int] = None
):
    """
    Récupère les données d'évolution de l'encours crédit (PTF et Produit d'intérêt) depuis Oracle.
    
    Args:
        month_m: Mois M (1-12). Si fourni avec year_m, calcule automatiquement les dates.
        year_m: Année M. Si fourni avec month_m, calcule automatiquement les dates.
        month_m1: Mois M-1 (1-12). Si non fourni, utilise le mois précédent de M.
        year_m1: Année M-1. Si non fourni, calcule automatiquement.
    
    Returns:
        Données d'évolution de l'encours crédit par agence avec PTF et Produit d'intérêt pour M et M-1
    """
    import calendar
    
    # Calcul des dates si month et year sont fournis
    if month_m and year_m:
        date_m_debut_obj = date(year_m, month_m, 1)
        date_m_fin_obj = date(year_m, month_m, calendar.monthrange(year_m, month_m)[1])
        
        # Calcul du mois précédent (M-1)
        if month_m1 and year_m1:
            date_m1_debut_obj = date(year_m1, month_m1, 1)
            date_m1_fin_obj = date(year_m1, month_m1, calendar.monthrange(year_m1, month_m1)[1])
        elif month_m == 1:
            date_m1_debut_obj = date(year_m - 1, 12, 1)
            date_m1_fin_obj = date(year_m - 1, 12, 31)
        else:
            date_m1_debut_obj = date(year_m, month_m - 1, 1)
            date_m1_fin_obj = date(year_m, month_m - 1, calendar.monthrange(year_m, month_m - 1)[1])
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    else:
        # Utiliser le mois et l'année actuels par défaut
        today = date.today()
        date_m_debut_obj = today.replace(day=1)
        date_m_fin_obj = today
        
        # Calcul automatique du mois précédent (M-1)
        first_day_m = date_m_debut_obj.replace(day=1)
        last_day_prev_month = first_day_m - timedelta(days=1)
        date_m1_debut_obj = last_day_prev_month.replace(day=1)
        date_m1_fin_obj = last_day_prev_month
        
        date_m_debut_str = date_m_debut_obj.strftime("%d/%m/%Y")
        date_m_fin_str = date_m_fin_obj.strftime("%d/%m/%Y")
        date_m1_debut_str = date_m1_debut_obj.strftime("%d/%m/%Y")
        date_m1_fin_str = date_m1_fin_obj.strftime("%d/%m/%Y")
    
    # Connexion à Oracle
    conn = get_oracle_connection()
    cursor = conn.cursor()
    
    # Requête SQL combinée pour PTF et Produit d'intérêt
    sql_query = """
    WITH DEBLOCAGE AS (
        SELECT
            ACCOUNT_NUMBER,
            COALESCE(DTYPE, 'VIDE') AS DTYPE,
            MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
        FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES
        WHERE (DTYPE <> 'X' OR DTYPE IS NULL)
        GROUP BY ACCOUNT_NUMBER, COALESCE(DTYPE, 'VIDE')
    ),
     
    ENCOURS_M AS (
        SELECT 
            c.ACCOUNT_NUMBER AS NO_PRET,
            c.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(NVL(z.AMOUNT_DUE,0)) AS MT_CAPITAL_TA,
            SUM(NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) AS ENCOURS_TOTAL_M,
            SUM(CASE WHEN c.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                     THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_SAIN,
            SUM(CASE WHEN c.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                     THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_IMPAYE
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
        LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
               ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
        LEFT JOIN DEBLOCAGE d 
               ON d.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
        LEFT JOIN cfsfcubs145.STTM_BRANCH BR on BR.BRANCH_CODE=c.BRANCH_CODE
        WHERE 
            c.ACCOUNT_STATUS NOT IN ('L', 'V')
            AND z.COMPONENT_NAME = 'PRINCIPAL'
            AND d.SCHEDULE_LINKAGE <= TO_DATE(:1, 'DD/MM/YYYY')
        GROUP BY c.ACCOUNT_NUMBER, c.BRANCH_CODE, BR.BRANCH_NAME
    ),
     
    result_M AS (
        SELECT  
            EM.BRANCH_CODE,
            EM.BRANCH_NAME,
            SUM(EM.ENCOURS_TOTAL_M) AS ENCOURS_TOTAL_M
        FROM ENCOURS_M EM 
        GROUP BY EM.BRANCH_CODE, EM.BRANCH_NAME
    ),
     
    ENCOURS_M_1 AS (
        SELECT 
            c.ACCOUNT_NUMBER AS NO_PRET,
            c.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(NVL(z.AMOUNT_DUE,0)) AS MT_CAPITAL_TA,
            SUM(NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) AS ENCOURS_TOTAL_M_1,
            SUM(CASE WHEN c.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                     THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_SAIN,
            SUM(CASE WHEN c.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                     THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_IMPAYE
        FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
        LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
               ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
        LEFT JOIN DEBLOCAGE d 
               ON d.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
        LEFT JOIN cfsfcubs145.STTM_BRANCH BR on BR.BRANCH_CODE=c.BRANCH_CODE
        WHERE 
            c.ACCOUNT_STATUS NOT IN ('L', 'V')
            AND z.COMPONENT_NAME = 'PRINCIPAL'
            AND d.SCHEDULE_LINKAGE <= TO_DATE(:2, 'DD/MM/YYYY')
        GROUP BY c.ACCOUNT_NUMBER, c.BRANCH_CODE, BR.BRANCH_NAME
    ),
     
    result_M_1 AS (
        SELECT  
            EM1.BRANCH_CODE,
            EM1.BRANCH_NAME,
            SUM(EM1.ENCOURS_TOTAL_M_1) AS ENCOURS_TOTAL_M_1
        FROM ENCOURS_M_1 EM1 
        GROUP BY EM1.BRANCH_CODE, EM1.BRANCH_NAME
    ),
    
    BRANCH AS (
        SELECT BRANCH_CODE, BRANCH_NAME
        FROM cfsfcubs145.STTM_BRANCH
    ),
    
    JOURNAL_INT AS (
        SELECT
            A.AC_BRANCH,
            A.AC_ENTRY_SR_NO,
            A.AMOUNT_TAG,
            A.RELATED_ACCOUNT,
            A.RELATED_CUSTOMER,
            A.AUTH_ID,
            A.USER_ID,
            A.module,
            A.event,
            A.TRN_CODE,
            A.DRCR_IND,
            A.BATCH_NO,
            A.AC_NO,
            CPT.ACCOUNT_CLASS,
            CL.DESCRIPTION,
            A.TRN_REF_NO AS NO_TRANSACT,
            A.LCY_AMOUNT AS INTERET_SUR_CREDIT,
            CPT.ACY_CURR_BALANCE AS SOLDE_COMPTABLE,
            DECODE(CPT.RECORD_STAT, 'O', 'OUVERT', 'C', 'FERME') AS STATUT,
            A.trn_dt,
            A.VALUE_DT
        FROM cfsfcubs145.ACVW_ALL_AC_ENTRIES A
        LEFT JOIN cfsfcubs145.STTM_CUST_ACCOUNT CPT ON A.AC_NO = CPT.CUST_AC_NO
        LEFT JOIN cfsfcubs145.STTM_ACCOUNT_CLASS CL ON CPT.ACCOUNT_CLASS = CL.ACCOUNT_CLASS
        WHERE
            A.DRCR_IND = 'C'
            AND A.AMOUNT_TAG in ('MAIN_INT_ACCR')
            AND A.module='CL'
    ),
    
    RESUL_INT_M AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(JLT.INTERET_SUR_CREDIT) AS INTERET_SUR_CREDIT_M
        FROM JOURNAL_INT JLT
        LEFT JOIN BRANCH BR ON JLT.AC_BRANCH = BR.BRANCH_CODE
        WHERE JLT.trn_dt BETWEEN TO_DATE(:3, 'DD/MM/YYYY') AND TO_DATE(:4, 'DD/MM/YYYY')
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    ),
    
    RESUL_INT_M_1 AS (
        SELECT 
            BR.BRANCH_CODE,
            BR.BRANCH_NAME,
            SUM(JLT1.INTERET_SUR_CREDIT) AS INTERET_SUR_CREDIT_M1
        FROM JOURNAL_INT JLT1
        LEFT JOIN BRANCH BR ON JLT1.AC_BRANCH = BR.BRANCH_CODE
        WHERE JLT1.trn_dt BETWEEN TO_DATE(:5, 'DD/MM/YYYY') AND TO_DATE(:6, 'DD/MM/YYYY')
        GROUP BY BR.BRANCH_CODE, BR.BRANCH_NAME
    )
     
    SELECT 
        RSM.BRANCH_CODE AS CODE_AGENCE,
        RSM.BRANCH_NAME AS AGENCE,
        COALESCE(RSM1.ENCOURS_TOTAL_M_1, 0) / 1000000 AS PTF_M1,
        COALESCE(RSM.ENCOURS_TOTAL_M, 0) / 1000000 AS PTF_M,
        (COALESCE(RSM.ENCOURS_TOTAL_M, 0) - COALESCE(RSM1.ENCOURS_TOTAL_M_1, 0)) / 1000000 AS VARIATION_PTF,
        CASE 
            WHEN COALESCE(RSM1.ENCOURS_TOTAL_M_1, 0) > 0 
            THEN ROUND(((COALESCE(RSM.ENCOURS_TOTAL_M, 0) - COALESCE(RSM1.ENCOURS_TOTAL_M_1, 0)) / RSM1.ENCOURS_TOTAL_M_1) * 100, 2)
            ELSE 0
        END AS TAUX_CROISSANCE_PTF,
        COALESCE(RSIM1.INTERET_SUR_CREDIT_M1, 0) / 1000000 AS PRODUIT_INT_M1,
        COALESCE(RSIM.INTERET_SUR_CREDIT_M, 0) / 1000000 AS PRODUIT_INT_M,
        (COALESCE(RSIM.INTERET_SUR_CREDIT_M, 0) - COALESCE(RSIM1.INTERET_SUR_CREDIT_M1, 0)) / 1000000 AS VARIATION_PRODUIT_INT,
        CASE 
            WHEN COALESCE(RSIM1.INTERET_SUR_CREDIT_M1, 0) > 0 
            THEN ROUND(((COALESCE(RSIM.INTERET_SUR_CREDIT_M, 0) - COALESCE(RSIM1.INTERET_SUR_CREDIT_M1, 0)) / RSIM1.INTERET_SUR_CREDIT_M1) * 100, 2)
            ELSE 0
        END AS TAUX_CROISSANCE_PRODUIT_INT
    FROM result_M RSM 
    LEFT JOIN result_M_1 RSM1 ON RSM1.BRANCH_CODE = RSM.BRANCH_CODE
    LEFT JOIN RESUL_INT_M RSIM ON RSIM.BRANCH_CODE = RSM.BRANCH_CODE
    LEFT JOIN RESUL_INT_M_1 RSIM1 ON RSIM1.BRANCH_CODE = RSM.BRANCH_CODE
    GROUP BY RSM.BRANCH_CODE, RSM.BRANCH_NAME, RSM1.ENCOURS_TOTAL_M_1, RSM.ENCOURS_TOTAL_M, 
             RSIM.INTERET_SUR_CREDIT_M, RSIM1.INTERET_SUR_CREDIT_M1
    ORDER BY RSM.BRANCH_NAME
    """
    
    try:
        cursor.execute(sql_query, [
            date_m_fin_str,      # :1 - fin M pour ENCOURS_M
            date_m1_fin_str,     # :2 - fin M-1 pour ENCOURS_M_1
            date_m_debut_str,    # :3 - début M pour produit d'intérêt
            date_m_fin_str,      # :4 - fin M pour produit d'intérêt
            date_m1_debut_str,   # :5 - début M-1 pour produit d'intérêt
            date_m1_fin_str      # :6 - fin M-1 pour produit d'intérêt
        ])
        
        # Récupérer les colonnes et les données
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convertir en liste de dictionnaires
        results = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            # Convertir les Decimal en float pour JSON et gérer les valeurs NULL
            for key, value in row_dict.items():
                if value is None:
                    row_dict[key] = 0
                elif hasattr(value, '__float__') and not isinstance(value, (int, float, bool, str, type(None))):
                    try:
                        row_dict[key] = float(value)
                    except (ValueError, TypeError):
                        row_dict[key] = 0
            results.append(row_dict)
        
        cursor.close()
        conn.close()
        
        # Organiser les données par territoire (même logique que pour production)
        territories_data = {
            'territoire_dakar_ville': [],
            'territoire_dakar_banlieue': [],
            'territoire_province_centre_sud': [],
            'territoire_province_nord': []
        }
        
        for row in results:
            agence_name = row.get('AGENCE', 'Inconnu')
            territory = get_territory_from_agency(agence_name)
            
            if territory:
                territory_key = get_territory_key(territory)
                if territory_key in territories_data:
                    territories_data[territory_key].append(row)
                else:
                    logger.warning(f"⚠️ Territoire non reconnu pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                    territories_data['territoire_dakar_ville'].append(row)
            else:
                agency_name_upper = agence_name.upper().strip()
                agency_name_normalized = ' '.join(agency_name_upper.split())
                is_service_point = False
                
                for service_point_name in SERVICE_POINT_MAPPING.keys():
                    service_point_normalized = ' '.join(service_point_name.upper().split())
                    if (service_point_normalized == agency_name_normalized or
                        service_point_normalized in agency_name_normalized or
                        agency_name_normalized in service_point_normalized):
                        is_service_point = True
                        break
                
                if not is_service_point:
                    logger.warning(f"⚠️ Aucun territoire trouvé pour l'agence {agence_name}, assigné à DAKAR VILLE par défaut")
                    territories_data['territoire_dakar_ville'].append(row)
                else:
                    territories_data['territoire_dakar_ville'].append(row)
        
        # Séparer les points de service des agences
        service_points_data = []
        agencies_by_territory = {
            'territoire_dakar_ville': [],
            'territoire_dakar_banlieue': [],
            'territoire_province_centre_sud': [],
            'territoire_province_nord': []
        }
        
        # Identifier et séparer les points de service (même logique que get_production_volume_data)
        for territory_key, agencies in territories_data.items():
            for agency in agencies:
                agence_name = agency.get('AGENCE', 'Inconnu')
                agency_name_upper = agence_name.upper().strip()
                agency_name_normalized = ' '.join(agency_name_upper.split())
                
                is_service_point = False
                for service_point_name in SERVICE_POINT_MAPPING.keys():
                    service_point_upper = service_point_name.upper().strip()
                    service_point_normalized = ' '.join(service_point_upper.split())
                    
                    agency_name_without_prefix = agency_name_normalized.replace('C-E ', '').replace('CE ', '').strip()
                    service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()
                    
                    if service_point_normalized == agency_name_normalized:
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                    if service_point_without_prefix == agency_name_without_prefix:
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                    if service_point_normalized in agency_name_normalized:
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                    if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                    if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                    
                    service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                    matching_words = [w for w in service_point_words if w in agency_name_normalized]
                    if len(matching_words) >= min(2, len(service_point_words)):
                        service_points_data.append(agency)
                        is_service_point = True
                        break
                
                if not is_service_point:
                    agencies_by_territory[territory_key].append(agency)
        
        # Obtenir la structure complète des territoires
        all_territories = get_all_territories()
        
        # Créer la structure hiérarchique
        hierarchical_data = {
            'TERRITOIRE': {},
            'POINT SERVICES': {}
        }
        
        # Calculer les totaux par territoire
        territories_totals = {}
        for territory_key, territory_rows in agencies_by_territory.items():
            if territory_rows:
                territory_total_ptf_m1 = sum(r.get('PTF_M1', 0) or 0 for r in territory_rows)
                territory_total_ptf_m = sum(r.get('PTF_M', 0) or 0 for r in territory_rows)
                territory_total_prod_int_m1 = sum(r.get('PRODUIT_INT_M1', 0) or 0 for r in territory_rows)
                territory_total_prod_int_m = sum(r.get('PRODUIT_INT_M', 0) or 0 for r in territory_rows)
                
                territory_variation_ptf = territory_total_ptf_m - territory_total_ptf_m1
                territory_taux_croissance_ptf = round((territory_variation_ptf / (territory_total_ptf_m1 or 1)) * 100, 2) if territory_total_ptf_m1 > 0 else 0
                
                territory_variation_prod_int = territory_total_prod_int_m - territory_total_prod_int_m1
                territory_taux_croissance_prod_int = round((territory_variation_prod_int / (territory_total_prod_int_m1 or 1)) * 100, 2) if territory_total_prod_int_m1 > 0 else 0
                
                territories_totals[territory_key] = {
                    'PTF_M1': territory_total_ptf_m1,
                    'PTF_M': territory_total_ptf_m,
                    'VARIATION_PTF': territory_variation_ptf,
                    'TAUX_CROISSANCE_PTF': territory_taux_croissance_ptf,
                    'PRODUIT_INT_M1': territory_total_prod_int_m1,
                    'PRODUIT_INT_M': territory_total_prod_int_m,
                    'VARIATION_PRODUIT_INT': territory_variation_prod_int,
                    'TAUX_CROISSANCE_PRODUIT_INT': territory_taux_croissance_prod_int
                }
                
                territory_name = {
                    'territoire_dakar_ville': 'TERRITOIRE DAKAR VILLE',
                    'territoire_dakar_banlieue': 'TERRITOIRE DAKAR BANLIEUE',
                    'territoire_province_centre_sud': 'TERRITOIRE PROVINCE CENTRE-SUD',
                    'territoire_province_nord': 'TERRITOIRE PROVINCE NORD'
                }.get(territory_key, territory_key)
                
                hierarchical_data['TERRITOIRE'][territory_key] = {
                    'name': territory_name,
                    'data': territory_rows,
                    'total': territories_totals[territory_key]
                }
        
        # Calculer les totaux des points de service
        if service_points_data:
            service_points_total_ptf_m1 = sum(r.get('PTF_M1', 0) or 0 for r in service_points_data)
            service_points_total_ptf_m = sum(r.get('PTF_M', 0) or 0 for r in service_points_data)
            service_points_total_prod_int_m1 = sum(r.get('PRODUIT_INT_M1', 0) or 0 for r in service_points_data)
            service_points_total_prod_int_m = sum(r.get('PRODUIT_INT_M', 0) or 0 for r in service_points_data)
            
            service_points_variation_ptf = service_points_total_ptf_m - service_points_total_ptf_m1
            service_points_taux_croissance_ptf = round((service_points_variation_ptf / (service_points_total_ptf_m1 or 1)) * 100, 2) if service_points_total_ptf_m1 > 0 else 0
            
            service_points_variation_prod_int = service_points_total_prod_int_m - service_points_total_prod_int_m1
            service_points_taux_croissance_prod_int = round((service_points_variation_prod_int / (service_points_total_prod_int_m1 or 1)) * 100, 2) if service_points_total_prod_int_m1 > 0 else 0
            
            hierarchical_data['POINT SERVICES']['service_points'] = {
                'name': 'POINT SERVICES',
                'data': service_points_data,
                'total': {
                    'PTF_M1': service_points_total_ptf_m1,
                    'PTF_M': service_points_total_ptf_m,
                    'VARIATION_PTF': service_points_variation_ptf,
                    'TAUX_CROISSANCE_PTF': service_points_taux_croissance_ptf,
                    'PRODUIT_INT_M1': service_points_total_prod_int_m1,
                    'PRODUIT_INT_M': service_points_total_prod_int_m,
                    'VARIATION_PRODUIT_INT': service_points_variation_prod_int,
                    'TAUX_CROISSANCE_PRODUIT_INT': service_points_taux_croissance_prod_int
                }
            }
        
        return {
            "period": {
                "m": {
                    "debut": date_m_debut_str,
                    "fin": date_m_fin_str,
                    "month": month_m or date_m_debut_obj.month,
                    "year": year_m or date_m_debut_obj.year
                },
                "m1": {
                    "debut": date_m1_debut_str,
                    "fin": date_m1_fin_str,
                    "month": month_m1 or date_m1_debut_obj.month,
                    "year": year_m1 or date_m1_debut_obj.year
                }
            },
            "hierarchicalData": hierarchical_data,
            "data": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données d'encours crédit: {str(e)}", exc_info=True)
        cursor.close()
        conn.close()
        raise

