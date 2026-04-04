"""
Service pour la gestion des données clients
"""
import logging
from datetime import datetime
from typing import Optional
from database.oracle import get_oracle_connection
from services.clients_dash_query import CLIENTS_DASH_QUERY
from services.utils import calculate_period_dates, get_territory_from_agency, get_territory_key, get_all_territories, SERVICE_POINT_MAPPING

logger = logging.getLogger(__name__)


def _normalize_dash_relation_row(row_dict: dict) -> dict:
    """Aligne les colonnes DASH_RELATION sur les clés attendues par le reste du service."""

    d = dict(row_dict)

    def g(*keys):
        for k in keys:
            v = d.get(k)
            if v is not None:
                return v
        return None

    n_m = g("NBRE_CLIENT_M", "Nbre_Client_M")
    n_m1 = g("NBRE_CLIENT_M_1", "Nbre_Client_M_1")
    d["Nbre_Client_M"] = float(n_m or 0)
    d["Nbre_Client_M_1"] = float(n_m1 or 0)
    d["NBRE_CLIENT_M"] = d["Nbre_Client_M"]
    d["NBRE_CLIENT_M_1"] = d["Nbre_Client_M_1"]
    d["FRAIS_M"] = float(g("FRAIS_OUV_CPT_M", "FRAIS_M") or 0)
    d["FRAIS_M_1"] = float(g("FRAIS_OUV_CPT_M_1", "FRAIS_M_1") or 0)
    d["VARIATION_POURCENT"] = float(g("VARIATION_POURCENT") or 0)
    m, m1 = d["Nbre_Client_M"], d["Nbre_Client_M_1"]
    d["POURCENT_REALISATION"] = round((m / m1) * 100, 2) if m1 else 0.0
    return d


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

    # Snapshot DASH_RELATION : MM/YYYY aligné sur la période (comme encours DAT / autres DASH)
    period_norm = str(period).strip().lower() if period else "month"
    if period_norm == "month":
        m, y = int(month or 0), int(year or 0)
        if not m or not y:
            now = datetime.now()
            m, y = now.month, now.year
        dash_month_year = f"{m:02d}/{y}"
    elif period_norm == "year":
        y = int(year or datetime.now().year)
        dash_month_year = f"12/{y}"
    else:
        try:
            d_end = datetime.strptime(date_m_fin_str, "%d/%m/%Y")
            dash_month_year = f"{d_end.month:02d}/{d_end.year}"
        except (ValueError, TypeError):
            now = datetime.now()
            dash_month_year = f"{now.month:02d}/{now.year}"

    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()

        cursor.arraysize = 1000
        cursor.prefetchrows = 1000

        logger.info("📊 Clients via DASH_RELATION, month_year=%s", dash_month_year)
        cursor.execute(CLIENTS_DASH_QUERY, {"month_year": dash_month_year})

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        logger.info(f"📊 Nombre de lignes retournées par Oracle (clients): {len(rows)}")
        if len(rows) > 0:
            logger.info(f"   Première ligne: {dict(zip(columns, rows[0]))}")

        numeric_keys = {
            "Nbre_Client_M",
            "Nbre_Client_M_1",
            "NBRE_CLIENT_M",
            "NBRE_CLIENT_M_1",
            "VARIATION",
            "VARIATION_POURCENT",
            "POURCENT_REALISATION",
            "FRAIS_M",
            "FRAIS_M_1",
            "FRAIS_OUV_CPT_M",
            "FRAIS_OUV_CPT_M_1",
        }
        results = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            for key, value in row_dict.items():
                if value is None:
                    if key in numeric_keys:
                        row_dict[key] = 0
                    else:
                        row_dict[key] = None
                elif hasattr(value, "__float__") and not isinstance(
                    value, (int, float, bool, str, type(None))
                ):
                    try:
                        row_dict[key] = float(value)
                    except (ValueError, TypeError):
                        row_dict[key] = 0
            row_dict = _normalize_dash_relation_row(row_dict)
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
    
    # Répartition par territoire : les anciens « points de service » sont rattachés à TERRITOIRE DAKAR VILLE
    agencies_by_territory = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    service_points_merged_count = 0

    for territory_key, agencies in territories_data.items():
        for agency in agencies:
            agency_name = agency.get('name') or 'Inconnu'
            if agency_name is None:
                agency_name = 'Inconnu'
            agency_name_upper = str(agency_name).upper().strip()
            agency_name_normalized = ' '.join(agency_name_upper.split())

            is_service_point = False
            for service_point_name in SERVICE_POINT_MAPPING.keys():
                service_point_upper = str(service_point_name).upper().strip() if service_point_name else ''
                service_point_normalized = ' '.join(service_point_upper.split())

                agency_name_without_prefix = agency_name_normalized.replace('C-E ', '').replace('CE ', '').strip()
                service_point_without_prefix = service_point_normalized.replace('C-E ', '').replace('CE ', '').strip()

                if service_point_normalized == agency_name_normalized:
                    is_service_point = True
                    break
                if service_point_without_prefix == agency_name_without_prefix:
                    is_service_point = True
                    break
                if service_point_normalized in agency_name_normalized:
                    is_service_point = True
                    break
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    is_service_point = True
                    break
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    is_service_point = True
                    break
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    is_service_point = True
                    break

            if is_service_point:
                agencies_by_territory['territoire_dakar_ville'].append(agency)
                service_points_merged_count += 1
                logger.info(f"✅ Point de service rattaché à TERRITOIRE DAKAR VILLE (clients): {agency_name}")
            else:
                agencies_by_territory[territory_key].append(agency)

    logger.info(f"📊 Points de service fusionnés dans territoire_dakar_ville (clients): {service_points_merged_count}")
    
    # Construire la réponse dans le nouveau format hiérarchique
    # Niveau 1: TERRITOIRE (points de service inclus sous territoire_dakar_ville)
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
            "POINT SERVICES": {}
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

