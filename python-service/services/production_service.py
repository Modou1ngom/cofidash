"""
Service pour la gestion des données de production
"""
import logging
from datetime import datetime, date, timedelta
import calendar
from typing import Optional
from services.utils import get_territory_from_agency, get_territory_key, get_all_territories, SERVICE_POINT_MAPPING

logger = logging.getLogger(__name__)


def _is_grand_compte_production_row(row: dict) -> bool:
    """Ligne Oracle dont l’agence est le Grand compte (exclue des territoires, exposée dans grandCompte)."""
    name = row.get("AGENCE") or row.get("Agence") or ""
    n = " ".join(str(name).upper().split())
    return "GRAND COMPTE" in n or "GRAND COMPTES" in n or "GRAND_COMPTE" in n


def get_production_nombre_data(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: Optional[str] = None,
    ref_date: Optional[str] = None,
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
    
    # Données pré-agrégées DASH (snapshot MIGRATION_DATE_MINUS1 aligné Volume DAT)
    from services.production_dash_service import (
        aggregate_nombre_dash_rows_by_agency,
        build_production_nombre_charge_details_by_agency,
        fetch_dash_production_nombre_rows,
        normalize_nombre_row_from_dash,
        resolve_production_period,
    )

    period_eff = resolve_production_period(period, month, year, date_m_debut, date_m_fin)
    raw_rows = fetch_dash_production_nombre_rows(period_eff, month, year, ref_date)
    charge_affaire_by_agency = build_production_nombre_charge_details_by_agency(raw_rows)
    raw_rows = aggregate_nombre_dash_rows_by_agency(raw_rows)
    results = []
    for row in raw_rows:
        row_dict = normalize_nombre_row_from_dash(row)
        for key, value in list(row_dict.items()):
            if value is None:
                if key in [
                    "NOMBRE_DE_CREDITS_DECAISSES_M",
                    "NOMBRE_DE_CREDITS_DECAISSES_M_1",
                    "VARIATION_NOMBRE",
                    "VARIATION_POURCENT",
                    "TAUX_REALISATION",
                    "OBJECTIF_PRODUCTION",
                ]:
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
        results.append(row_dict)

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
    grand_compte_rows = []
    for row in results:
        if _is_grand_compte_production_row(row):
            grand_compte_rows.append(row)
            logger.info(f"✅ Production nombre — Grand compte isolé: {row.get('AGENCE')}")
            continue

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
    
    # Points de service rattachés à territoire_dakar_ville
    agencies_by_territory = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
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
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - exact): {agence_name} -> {service_point_name}")
                    break
                
                # 2. Correspondance sans préfixe
                if service_point_without_prefix == agency_name_without_prefix:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - sans préfixe): {agence_name} -> {service_point_name}")
                    break
                
                # 3. Le nom de l'agence contient le nom du point de service
                if service_point_normalized in agency_name_normalized:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - contient): {agence_name} -> {service_point_name}")
                    break
                
                # 4. Le nom de l'agence (sans préfixe) contient le nom du point de service (sans préfixe)
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - contient sans préfixe): {agence_name} -> {service_point_name}")
                    break
                
                # 5. Le nom du point de service contient le nom de l'agence (pour les cas courts)
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    logger.info(f"✅ Point de service identifié (production - inclus): {agence_name} -> {service_point_name}")
                    break
                
                # 6. Correspondance par mots-clés significatifs (pour gérer les variations)
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                agency_words = [w for w in agency_name_normalized.split() if len(w) > 3]
                
                # Si au moins 2 mots significatifs correspondent
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
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
    
    grand_compte_payload = None
    if grand_compte_rows:
        gc_m = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M', 0) or 0 for r in grand_compte_rows)
        gc_m1 = sum(r.get('NOMBRE_DE_CREDITS_DECAISSES_M_1', 0) or 0 for r in grand_compte_rows)
        gc_obj = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in grand_compte_rows)
        ag_name = grand_compte_rows[0].get('AGENCE') or 'AGENCE GRAND COMPTE'
        grand_compte_payload = {
            'name': ag_name,
            'objectif': gc_obj,
            'm': gc_m,
            'm1': gc_m1,
        }
        logger.info(
            "✅ Production nombre — grandCompte: objectif=%s m=%s (lignes=%s)",
            gc_obj, gc_m, len(grand_compte_rows),
        )
    
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
            "mois": total_m,
            "mois1": total_m1,
            "variation": total_variation,
            "variation_pourcent": total_variation_pct
        },
        "grandCompte": grand_compte_payload,
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
            "POINT SERVICES": {}
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
    year: Optional[int] = None,
    period: Optional[str] = None,
    ref_date: Optional[str] = None,
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
    
    # Données DASH_PRODUCTION_VOLUME (snapshot MIGRATION_DATE_MINUS1)
    from services.production_dash_service import (
        aggregate_volume_dash_rows_by_agency,
        build_production_volume_charge_details_by_agency,
        fetch_dash_production_volume_rows,
        normalize_volume_row_from_dash,
        resolve_production_period,
    )

    period_eff = resolve_production_period(period, month, year, date_m_debut, date_m_fin)
    raw_vol = fetch_dash_production_volume_rows(period_eff, month, year, ref_date)
    charge_affaire_by_agency = build_production_volume_charge_details_by_agency(raw_vol)
    raw_vol = aggregate_volume_dash_rows_by_agency(raw_vol)
    results = []
    for row in raw_vol:
        row_dict = normalize_volume_row_from_dash(row)
        for key, value in list(row_dict.items()):
            if value is None:
                if key in [
                    "VOLUME_CREDIT_DECAISSE_M",
                    "VOLUME_CREDIT_DECAISSE_M_1",
                    "VARIATION_VOLUME",
                    "VARIATION_POURCENT",
                    "TAUX_REALISATION",
                    "OBJECTIF_PRODUCTION",
                    "FRAIS_DOSSIER_M",
                    "FRAIS_DOSSIER_M_1",
                    "ECART_FRAIS",
                    "VARIATION_FRAIS",
                ]:
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
        results.append(row_dict)

    # Organiser les données par territoire (même logique que pour get_production_nombre_data)
    territories_data = {
        'territoire_dakar_ville': [],
        'territoire_dakar_banlieue': [],
        'territoire_province_centre_sud': [],
        'territoire_province_nord': []
    }
    
    grand_compte_rows = []
    for row in results:
        if _is_grand_compte_production_row(row):
            grand_compte_rows.append(row)
            logger.info(f"✅ Production volume — ligne Grand compte isolée: {row.get('AGENCE')}")
            continue

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
    
    # Points de service rattachés à territoire_dakar_ville
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
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix == agency_name_without_prefix:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_normalized in agency_name_normalized:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
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
    
    grand_compte_payload = None
    if grand_compte_rows:
        gc_vol_m = sum(r.get('VOLUME_CREDIT_DECAISSE_M', 0) or 0 for r in grand_compte_rows)
        gc_vol_m1 = sum(r.get('VOLUME_CREDIT_DECAISSE_M_1', 0) or 0 for r in grand_compte_rows)
        gc_obj = sum(r.get('OBJECTIF_PRODUCTION', 0) or 0 for r in grand_compte_rows)
        gc_frais_m = sum(r.get('FRAIS_DOSSIER_M', 0) or 0 for r in grand_compte_rows)
        gc_frais_m1 = sum(r.get('FRAIS_DOSSIER_M_1', 0) or 0 for r in grand_compte_rows)
        gc_var_vol = gc_vol_m - gc_vol_m1
        gc_var_pct = round((gc_var_vol / (gc_vol_m1 or 1)) * 100, 2) if gc_vol_m1 else 0.0
        gc_atteinte = round((gc_vol_m / (gc_obj or 1)) * 100, 2) if gc_obj else 0.0
        terr_sum_m = sum(t.get('volumeM', 0) or 0 for t in territories_totals.values())
        _denom_gc = terr_sum_m + gc_vol_m
        gc_contrib = round((gc_vol_m / _denom_gc) * 100, 2) if _denom_gc > 0 else 0.0
        ag_name = grand_compte_rows[0].get('AGENCE') or 'AGENCE GRAND COMPTE'
        grand_compte_payload = {
            'name': ag_name,
            'objectif': gc_obj,
            'volumeM': gc_vol_m,
            'volumeM1': gc_vol_m1,
            'fraisM': gc_frais_m,
            'fraisM1': gc_frais_m1,
            'variationVolume': gc_var_vol,
            'variationPourcent': gc_var_pct,
            'atteinte': gc_atteinte,
            'contribution': gc_contrib,
        }
        logger.info(
            "✅ Production volume — grandCompte: objectif=%s volumeM=%s (lignes=%s)",
            gc_obj, gc_vol_m, len(grand_compte_rows),
        )
    
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
        "grandCompte": grand_compte_payload,
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
            "POINT SERVICES": {}
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
    year_m1: Optional[int] = None,
    period: Optional[str] = None,
    ref_date: Optional[str] = None,
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
    
    # Données DASH_EVOLUTION_ENCOURS (snapshot MIGRATION_DATE_MINUS1, aligné Volume DAT)
    from services.production_dash_service import (
        fetch_dash_evolution_encours_rows,
        normalize_encours_row_from_dash,
        resolve_production_period,
    )

    period_eff = resolve_production_period(period, month_m, year_m, None, None)
    raw_rows = fetch_dash_evolution_encours_rows(period_eff, month_m, year_m, ref_date)
    results = []
    for row in raw_rows:
        row_dict = normalize_encours_row_from_dash(row)
        for key, value in list(row_dict.items()):
            if value is None:
                if key in (
                    "PTF_M1",
                    "PTF_M",
                    "VARIATION_PTF",
                    "TAUX_CROISSANCE_PTF",
                    "PRODUIT_INT_M1",
                    "PRODUIT_INT_M",
                    "VARIATION_PRODUIT_INT",
                    "TAUX_CROISSANCE_PRODUIT_INT",
                ):
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
        results.append(row_dict)

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
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix == agency_name_without_prefix:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_normalized in agency_name_normalized:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if service_point_without_prefix in agency_name_without_prefix and len(service_point_without_prefix) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                if agency_name_normalized in service_point_normalized and len(agency_name_normalized) > 5:
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
                    is_service_point = True
                    break
                
                service_point_words = [w for w in service_point_normalized.split() if len(w) > 3]
                matching_words = [w for w in service_point_words if w in agency_name_normalized]
                if len(matching_words) >= min(2, len(service_point_words)):
                    agencies_by_territory['territoire_dakar_ville'].append(agency)
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

