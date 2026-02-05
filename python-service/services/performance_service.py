"""
Service pour calculer les performances des agences
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime
from services.clients_service import get_clients_data
from services.collection_service import get_collection_data
from services.production_service import get_production_nombre_data, get_production_volume_data

logger = logging.getLogger(__name__)


def get_agency_performance(
    data_type: str,
    period: Optional[str] = "month",
    month: Optional[int] = None,
    year: Optional[int] = None,
    collection_tab: Optional[str] = None
) -> Dict:
    """
    Récupère les données de performance des agences selon le type de données
    
    Args:
        data_type: Type de données ('client', 'collection', 'credit', etc.)
        period: Période d'analyse ("week", "month", "year")
        month: Mois à analyser (1-12)
        year: Année à analyser
        collection_tab: Pour data_type='collection', spécifie l'onglet ('collecte' ou 'solde')
    
    Returns:
        Dictionnaire avec top5Nombre, flop5Nombre, top5Volume, flop5Volume
    """
    try:
        # Récupérer les données selon le type
        if data_type == 'client':
            data = get_clients_data(period=period, month=month, year=year)
            nombre_metric = 'nouveauxClientsM'
            volume_metric = 'fraisM'
        elif data_type == 'collection':
            data = get_collection_data(period=period, month=month, year=year)
            if collection_tab == 'solde':
                nombre_metric = 'sldM'
                volume_metric = 'sldM'
            else:  # collecte par défaut
                nombre_metric = 'collecteM'
                volume_metric = 'mtEcheance'
        elif data_type == 'credit':
            data = get_production_nombre_data(month=month, year=year)
            nombre_metric = 'nombreCredits'
            volume_metric = 'montantCredits'
        else:
            # Par défaut, utiliser les données clients
            data = get_clients_data(period=period, month=month, year=year)
            nombre_metric = 'nouveauxClientsM'
            volume_metric = 'fraisM'
        
        # Extraire les agences et leurs métriques
        agencies = _extract_agencies_from_data(data, data_type, nombre_metric, volume_metric)
        
        # Classer les agences
        top5_nombre, flop5_nombre = _get_top_flop_by_metric(agencies, 'nombre', 5)
        top5_volume, flop5_volume = _get_top_flop_by_metric(agencies, 'volume', 5)
        
        return {
            'top5Nombre': [ag['name'] for ag in top5_nombre],
            'flop5Nombre': [ag['name'] for ag in flop5_nombre],
            'top5Volume': [ag['name'] for ag in top5_volume],
            'flop5Volume': [ag['name'] for ag in flop5_volume]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des performances: {str(e)}", exc_info=True)
        raise


def _extract_agencies_from_data(data: Dict, data_type: str, nombre_metric: str, volume_metric: str) -> List[Dict]:
    """
    Extrait les agences et leurs métriques depuis les données
    """
    agencies = []
    
    # Extraire les données hiérarchiques
    hierarchical_data = None
    if data and isinstance(data, dict):
        if 'data' in data and 'hierarchicalData' in data['data']:
            hierarchical_data = data['data']['hierarchicalData']
        elif 'hierarchicalData' in data:
            hierarchical_data = data['hierarchicalData']
        elif 'data' in data:
            hierarchical_data = data['data']
    
    if not hierarchical_data:
        return agencies
    
    # Extraire depuis TERRITOIRE
    if 'TERRITOIRE' in hierarchical_data:
        for territory in hierarchical_data['TERRITOIRE'].values():
            if 'agencies' in territory and isinstance(territory['agencies'], list):
                for agency in territory['agencies']:
                    agency_name = _get_agency_name(agency)
                    if agency_name and agency_name.upper() not in ['INCONNU', 'UNKNOWN']:
                        nombre = _get_metric_value(agency, nombre_metric)
                        volume = _get_metric_value(agency, volume_metric)
                        
                        agencies.append({
                            'name': agency_name,
                            'nombre': nombre,
                            'volume': volume
                        })
    
    # Extraire depuis POINT SERVICES
    if 'POINT SERVICES' in hierarchical_data:
        for service_point in hierarchical_data['POINT SERVICES'].values():
            if 'agencies' in service_point and isinstance(service_point['agencies'], list):
                for agency in service_point['agencies']:
                    agency_name = _get_agency_name(agency)
                    if agency_name and agency_name.upper() not in ['INCONNU', 'UNKNOWN']:
                        nombre = _get_metric_value(agency, nombre_metric)
                        volume = _get_metric_value(agency, volume_metric)
                        
                        agencies.append({
                            'name': agency_name,
                            'nombre': nombre,
                            'volume': volume
                        })
    
    # Si pas de données hiérarchiques, essayer territories
    if not agencies and 'territories' in data:
        for territory in data['territories'].values():
            if 'agencies' in territory and isinstance(territory['agencies'], list):
                for agency in territory['agencies']:
                    agency_name = _get_agency_name(agency)
                    if agency_name and agency_name.upper() not in ['INCONNU', 'UNKNOWN']:
                        nombre = _get_metric_value(agency, nombre_metric)
                        volume = _get_metric_value(agency, volume_metric)
                        
                        agencies.append({
                            'name': agency_name,
                            'nombre': nombre,
                            'volume': volume
                        })
    
    return agencies


def _get_agency_name(agency: Dict) -> str:
    """Extrait le nom de l'agence depuis l'objet agence"""
    return (
        agency.get('name') or
        agency.get('AGENCE') or
        agency.get('agency') or
        ''
    )


def _get_metric_value(agency: Dict, metric: str) -> float:
    """Récupère la valeur d'une métrique depuis l'agence"""
    metric_map = {
        'nouveauxClientsM': agency.get('nouveauxClientsM', 0),
        'fraisM': agency.get('fraisM', 0),
        'collecteM': agency.get('collecteM') or agency.get('COLLECTE_M', 0),
        'mtEcheance': agency.get('mtEcheance') or agency.get('MT_ECHEANCE', 0),
        'sldM': agency.get('sldM') or agency.get('SLD_M', 0),
        'nombreCredits': agency.get('nombreCredits', 0),
        'montantCredits': agency.get('montantCredits', 0)
    }
    
    return float(metric_map.get(metric, 0) or 0)


def _get_top_flop_by_metric(agencies: List[Dict], metric: str, limit: int = 5) -> tuple:
    """
    Retourne les top et flop agences selon une métrique
    
    Args:
        agencies: Liste des agences avec leurs métriques
        metric: Métrique à utiliser ('nombre' ou 'volume')
        limit: Nombre d'agences à retourner (défaut: 5)
    
    Returns:
        Tuple (top_list, flop_list)
    """
    # Filtrer les agences avec des valeurs > 0
    valid_agencies = [ag for ag in agencies if ag.get(metric, 0) > 0]
    
    # Trier par ordre décroissant pour top
    sorted_agencies = sorted(valid_agencies, key=lambda x: x.get(metric, 0), reverse=True)
    
    # Top N
    top = sorted_agencies[:limit]
    
    # Flop N (les moins performantes)
    flop = sorted_agencies[-limit:] if len(sorted_agencies) >= limit else sorted_agencies
    flop.reverse()  # Inverser pour avoir du pire au moins pire
    
    return top, flop
