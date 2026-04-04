"""
Router pour les endpoints Oracle
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime
from database.oracle import get_oracle_connection
from services.clients_service import get_clients_data
from services.production_service import get_production_nombre_data, get_production_volume_data, get_encours_credit_data
from services.collection_service import get_collection_data
from services.transfer_service import get_transfer_data
from services.performance_service import get_agency_performance
from services.volume_dat_service import get_volume_dat_data
from services.encours_service import get_encours_data
from services.depot_garantie_service import get_depot_garantie_data
from services.prepaid_card_service import get_prepaid_card_sales_data
from services.portefeuille_risque_service import (
    get_portefeuille_risque_data,
    get_portefeuille_risque_caf_data,
)
from services.entrees_par_service import get_entrees_par_data
from services.reference_compte_service import get_gl_by_code, search_gl
from services.cr_par_agence_service import get_cr_data_by_parent_gl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oracle", tags=["oracle"])


@router.get("/test")
async def test_oracle_connection():
    """Teste la connexion à Oracle"""
    try:
        conn = get_oracle_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Connexion Oracle réussie", "result": result[0]}
    except HTTPException:
        # Propager les HTTPException directement (elles contiennent déjà le message détaillé)
        raise
    except Exception as e:
        # Pour les autres exceptions, créer un message d'erreur détaillé
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors du test de connexion Oracle: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur de connexion: {error_message}"
        )


@router.get("/tables")
async def get_oracle_tables(schema: Optional[str] = None, limit: Optional[int] = 1000):
    """Récupère la liste des tables disponibles"""
    try:
        conn = get_oracle_connection()
        cursor = conn.cursor()
        tables = []
        
        # Si un schéma est spécifié, filtrer par schéma
        if schema:
            query = """
                SELECT owner || '.' || table_name as table_name 
                FROM all_tables 
                WHERE owner = UPPER(:schema)
                ORDER BY owner, table_name
            """
            if limit:
                query += f" FETCH FIRST {limit} ROWS ONLY"
            cursor.execute(query, [schema])
            tables = [row[0] for row in cursor.fetchall()]
        else:
            # D'abord essayer user_tables (tables du schéma de l'utilisateur)
            query = """
                SELECT table_name 
                FROM user_tables 
                ORDER BY table_name
            """
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Si aucune table dans user_tables, récupérer toutes les tables accessibles
            if len(tables) == 0:
                query = """
                    SELECT DISTINCT owner || '.' || table_name as table_name 
                    FROM all_tables 
                    ORDER BY owner, table_name
                """
                if limit:
                    query += f" FETCH FIRST {limit} ROWS ONLY"
                cursor.execute(query)
                tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des tables: {str(e)}")


@router.post("/query")
async def execute_oracle_query(query: dict):
    """Exécute une requête SQL personnalisée"""
    try:
        sql = query.get('sql', '')
        if not sql:
            raise HTTPException(status_code=400, detail="La requête SQL est requise")
        
        conn = get_oracle_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Récupérer les noms de colonnes
        columns = [desc[0] for desc in cursor.description]
        
        # Récupérer les données
        rows = cursor.fetchall()
        
        # Convertir en liste de dictionnaires
        results = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return {"data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exécution de la requête: {str(e)}")


@router.get("/data/clients")
async def get_clients_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None
):
    """
    Récupère les données clients depuis Oracle dans le format attendu par le dashboard
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12) - pour period="month"
        year: Année à analyser
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Structure retournée:
    {
        "globalResult": { "mois", "mois1", "evolution", "cumulAnnee" },
        "corporateZones": { "zone1": { "agencies": [...] }, "zone2": { "agencies": [...] } },
        "retailZones": { "zone1": { "agencies": [...] }, "zone2": { "agencies": [...] } }
    }
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_clients_data: period={period}, zone={zone}, month={month}, year={year}, date={date}")
        data = get_clients_data(period, zone, month, year, date)
        return {"data": data}
    except HTTPException:
        # Propager les HTTPException directement (elles contiennent déjà le message détaillé)
        raise
    except Exception as e:
        # Pour les autres exceptions, créer un message d'erreur détaillé
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données clients: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données clients: {error_message}"
        )


@router.get("/data/production/nombre")
async def get_production_nombre_data_endpoint(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: Optional[str] = None,
    date: Optional[str] = None,
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
    try:
        return get_production_nombre_data(
            date_m_debut, date_m_fin, month, year, period=period, ref_date=date
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données de production: {str(e)}\n{error_detail}"
        )


# Endpoint de compatibilité (ancienne route)
@router.get("/data/production")
async def get_production_data_endpoint(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: Optional[str] = None,
    date: Optional[str] = None,
):
    """
    Récupère les données de production en nombre (nombre de crédits décaissés par agence) depuis Oracle.
    Route de compatibilité - utilise /api/oracle/data/production/nombre en interne.
    """
    return await get_production_nombre_data_endpoint(
        date_m_debut, date_m_fin, month, year, period, date
    )


@router.get("/data/production-volume")
async def get_production_volume_data_endpoint(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    period: Optional[str] = None,
    date: Optional[str] = None,
):
    """
    Récupère les données de production en volume (montant de crédits décaissés par agence) depuis Oracle.
    Inclut également les frais de dossier.
    
    Args:
        date_m_debut: Date de début du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise le 1er du mois courant.
        date_m_fin: Date de fin du mois en cours (format: DD/MM/YYYY). Si non fournie, utilise la date du jour.
        month: Mois à analyser (1-12). Si fourni avec year, calcule automatiquement les dates.
        year: Année à analyser. Si fourni avec month, calcule automatiquement les dates.
    
    Returns:
        Données de production en volume par agence avec comparaison M vs M-1, incluant les frais de dossier
    """
    try:
        return get_production_volume_data(
            date_m_debut, date_m_fin, month, year, period=period, ref_date=date
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données de production en volume: {str(e)}\n{error_detail}"
        )


@router.get("/data/encours-credit")
async def get_encours_credit_data_endpoint(
    month_m: Optional[int] = None,
    year_m: Optional[int] = None,
    month_m1: Optional[int] = None,
    year_m1: Optional[int] = None,
    period: Optional[str] = None,
    date: Optional[str] = None,
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
    try:
        return get_encours_credit_data(
            month_m, year_m, month_m1, year_m1, period=period, ref_date=date
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données d'encours crédit: {str(e)}\n{error_detail}"
        )


@router.get("/data/collection")
async def get_collection_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None
):
    """
    Récupère les données de collection depuis Oracle dans le format attendu par le dashboard
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12) - pour period="month"
        year: Année à analyser
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Structure retournée:
    {
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": "TERRITOIRE DAKAR VILLE",
                    "agencies": [...],
                    "totals": {...}
                },
                ...
            },
            "POINT SERVICES": {
                "service_points": {
                    "agencies": [...],
                    "totals": {...}
                }
            }
        }
    }
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_collection_data: period={period}, zone={zone}, month={month}, year={year}, date={date}")
        
        # Appeler la fonction get_collection_data qui utilise les requêtes séparées
        result = get_collection_data(period=period, zone=zone, month=month, year=year, date=date)
        
        # Retourner les données dans le format attendu par le frontend
        return {
            "data": {
                "hierarchicalData": result.get('hierarchicalData', {}),
                "globalResult": result.get('globalResult', {}),
                "grandCompte": result.get('grandCompte', {}),
                "chargeAffaireDetails": result.get('chargeAffaireDetails', {})
            },
            "chargeAffaireDetails": result.get('chargeAffaireDetails', {})
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données collection: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données collection: {error_message}"
        )


@router.get("/data/volume-dat")
async def get_volume_dat_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None
):
    """
    Récupère les données Volume DAT depuis Oracle dans le format attendu par le dashboard
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12) - pour period="month"
        year: Année à analyser
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Structure retournée:
    {
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": "DAKAR CENTRE VILLE",
                    "agencies": [...],
                    "totals": {...}
                },
                ...
            },
            "POINT SERVICES": {
                "service_points": {
                    "agencies": [...],
                    "totals": {...}
                }
            }
        }
    }
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_volume_dat_data: period={period}, zone={zone}, month={month}, year={year}, date={date}")
        
        # Appeler la fonction get_volume_dat_data
        result = get_volume_dat_data(period=period, zone=zone, month=month, year=year, date=date)
        
        # Retourner les données dans le format attendu par le frontend
        return {
            "data": {
                "hierarchicalData": result.get('hierarchicalData', {}),
                "snapshot": result.get('snapshot'),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données Volume DAT: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données Volume DAT: {error_message}"
        )


@router.get("/data/encours")
async def get_encours_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
    type: Optional[str] = "compte-courant"
):
    """
    Récupère les données Encours depuis Oracle
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période semaine (format YYYY-MM-DD)
        type: Type d'encours ("compte-courant", "epargne-simple", "epargne-pep-simple", "epargne-projet")
    
    Returns:
        Dictionnaire avec les données Encours organisées par zones
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_encours_data: period={period}, zone={zone}, month={month}, year={year}, date={date}, type={type}")
        result = get_encours_data(period=period, zone=zone, month=month, year=year, date=date, encours_type=type)
        return {
            "data": {
                "hierarchicalData": result.get('hierarchicalData', {})
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données Encours: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données Encours: {error_message}"
        )


@router.get("/data/depot-garantie")
async def get_depot_garantie_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None
):
    """
    Récupère les données Dépôt de Garantie depuis Oracle dans le format attendu par le dashboard
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12) - pour period="month"
        year: Année à analyser
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Structure retournée:
    {
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": "DAKAR CENTRE VILLE",
                    "agencies": [...],
                    "totals": {...}
                },
                ...
            },
            "POINT SERVICES": {
                "service_points": {
                    "agencies": [...],
                    "totals": {...}
                }
            }
        }
    }
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_depot_garantie_data: period={period}, zone={zone}, month={month}, year={year}, date={date}")
        
        # Appeler la fonction get_depot_garantie_data
        result = get_depot_garantie_data(period=period, zone=zone, month=month, year=year, date=date)
        
        # Retourner les données dans le format attendu par le frontend
        return {
            "data": {
                "hierarchicalData": result.get('hierarchicalData', {})
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données Dépôt de Garantie: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données Dépôt de Garantie: {error_message}"
        )


@router.get("/data/transfers")
async def get_transfer_data_endpoint(
    period: Optional[str] = "month",
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
    service: Optional[str] = "om"
):
    """
    Récupère les données de transferts d'argent depuis Oracle
    
    Args:
        period: Période d'analyse ("week", "month", "year"). Par défaut "month".
        month: Mois à analyser (1-12). Si non fourni, utilise le mois courant.
        year: Année à analyser. Si non fourni, utilise l'année courante.
        date: Date au format YYYY-MM-DD - pour period="week"
        service: Service de transfert ("om", "wave", "ria", "wu"). Par défaut "om" (Orange Money)
    
    Returns:
        Données de transferts d'argent par agence et par service avec:
        - Tableau détaillé des agences (objectif, volume M, volume M-1, variation, TRO, contribution, commission)
        - Résumé par service de transfert (volume et commission)
    """
    try:
        # S'assurer que month et year sont des entiers
        if month is not None:
            month = int(month)
        if year is not None:
            year = int(year)
        logger.info(f"📅 Paramètres reçus pour get_transfer_data: period={period}, month={month} (type: {type(month)}), year={year} (type: {type(year)}), date={date}, service={service}")
        data = get_transfer_data(period=period, month=month, year=year, date=date, service=service)
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données de transferts: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données de transferts: {error_message}"
        )


@router.get("/data/prepaid-card-sales")
async def get_prepaid_card_sales_data_endpoint(
    period: Optional[str] = "month", 
    zone: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None
):
    """
    Récupère les données de ventes de cartes prépayées (CofiCarte) depuis Oracle
    
    Args:
        period: Période d'analyse ("week", "month", "year")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12) - pour period="month"
        year: Année à analyser
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Returns:
        Structure hiérarchique avec:
        - hierarchicalData.TERRITOIRE: territoires avec leurs agences et totaux
        - hierarchicalData.POINT SERVICES: points de service avec leurs données
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_prepaid_card_sales_data: period={period}, zone={zone}, month={month}, year={year}, date={date}")
        result = get_prepaid_card_sales_data(period=period, zone=zone, month=month, year=year, date=date)
        # Le service retourne déjà la structure avec hierarchicalData
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"Erreur lors de la récupération des données de ventes de cartes prépayées: {error_message}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données de ventes de cartes prépayées: {error_message}"
        )


@router.get("/data/agency-performance")
async def get_agency_performance_endpoint(
    data_type: str = "client",
    period: Optional[str] = "month",
    month: Optional[int] = None,
    year: Optional[int] = None,
    collection_tab: Optional[str] = None
):
    """
    Récupère les performances des agences (Top 5 et Flop 5) selon le type de données
    
    Args:
        data_type: Type de données ('client', 'collection', 'credit', etc.)
        period: Période d'analyse ("week", "month", "year")
        month: Mois à analyser (1-12)
        year: Année à analyser
        collection_tab: Pour data_type='collection', spécifie l'onglet ('collecte' ou 'solde')
    
    Returns:
        {
            "top5Nombre": ["Agence 1", "Agence 2", ...],
            "flop5Nombre": ["Agence 1", "Agence 2", ...],
            "top5Volume": ["Agence 1", "Agence 2", ...],
            "flop5Volume": ["Agence 1", "Agence 2", ...]
        }
    """
    try:
        # Si month et year ne sont pas fournis, utiliser le mois en cours
        if month is None or year is None:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        result = get_agency_performance(
            data_type=data_type,
            period=period,
            month=month,
            year=year,
            collection_tab=collection_tab
        )
        
        return result
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Erreur lors de la récupération des performances: {str(e)}\n{error_detail}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des performances: {str(e)}"
        )


@router.get("/data/portefeuille-risque")
async def get_portefeuille_risque_data_endpoint(
    month: Optional[int] = None,
    year: Optional[int] = None,
    month_ref: Optional[int] = None,
    year_ref: Optional[int] = None
):
    """
    Récupère les données de portefeuille à risque (PAR) depuis Oracle
    
    Args:
        month: Mois en cours (1-12). Si non fourni, utilise le mois courant.
        year: Année du mois en cours. Si non fourni, utilise l'année courante.
        month_ref: Mois de référence (1-12). Si non fourni, mois précédent du mois en cours.
        year_ref: Année du mois de référence. Si non fourni, déduite du mois en cours.
    
    Structure retournée:
    {
        "data": [...],  # Données brutes
        "hierarchicalData": {
            "TERRITOIRE": {
                "territoire_dakar_ville": {
                    "name": "TERRITOIRE DAKAR VILLE",
                    "agencies": [...],
                    "totals": {...}
                },
                ...
            },
            "POINT SERVICES": {}
        }
    }
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_portefeuille_risque_data: month={month}, year={year}, month_ref={month_ref}, year_ref={year_ref}")
        result = get_portefeuille_risque_data(month=month, year=year, month_ref=month_ref, year_ref=year_ref)
        
        # Retourner les données dans le format attendu par le frontend
        return {
            "data": result.get("data", []),
            "hierarchicalData": result.get("hierarchicalData", {
                "TERRITOIRE": {},
                "POINT SERVICES": {}
            })
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"❌ Erreur lors de la récupération des données portefeuille à risque: {error_message}\n{error_detail}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données portefeuille à risque: {error_message}"
        )


@router.get("/data/stock-provision")
async def get_stock_provision_data_endpoint(
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """
    Récupère les données de stock de provision depuis Oracle
    
    Args:
        month: Mois à analyser (1-12). Si non fourni, utilise le mois courant.
        year: Année à analyser. Si non fourni, utilise l'année courante.
    
    Returns:
        Liste de dictionnaires avec les données de stock par branche
    """
    try:
        from services.stock_provision_service import get_stock_provision_data
        logger.info(f"📊 Récupération des données Stock Provision: month={month}, year={year}")
        result = get_stock_provision_data(month=month, year=year)
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_message = str(e) if str(e) else repr(e)
        logger.error(f"❌ Erreur lors de la récupération des données Stock Provision: {error_message}\n{error_detail}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des données Stock Provision: {error_message}"
        )


@router.get("/data/portefeuille-risque-caf")
async def get_portefeuille_risque_caf_endpoint(
    agency: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    month_ref: Optional[int] = None,
    year_ref: Optional[int] = None,
):
    """
    Récupère les données de portefeuille à risque agrégées par CAF
    (chargé d'affaires) pour une agence donnée.

    Args:
        agency: Nom de l'agence (doit correspondre à la colonne AGENCE de la requête PAR).
        month: Mois en cours (1-12).
        year: Année du mois en cours.
        month_ref: Mois de référence (1-12).
        year_ref: Année du mois de référence.
    """
    try:
        agency_param = (agency or "").strip()
        logger.info(
            "📊 Récupération des données PAR | CAF: agency=%s, month=%s, year=%s, month_ref=%s, year_ref=%s",
            agency_param or "(toutes)",
            month,
            year,
            month_ref,
            year_ref,
        )
        caf_list = get_portefeuille_risque_caf_data(
            agency=agency_param or None,
            month=month,
            year=year,
            month_ref=month_ref,
            year_ref=year_ref,
        )
        return {"agency": agency_param or "", "caf": caf_list}
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        error_message = str(e) if str(e) else repr(e)
        logger.error(
            "❌ Erreur lors de la récupération des données PAR | CAF: %s\n%s",
            error_message,
            error_detail,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données PAR | CAF: {error_message}",
        )


@router.get("/data/entrees-par")
async def get_entrees_par_endpoint(
    month: Optional[int] = None,
    year: Optional[int] = None,
    par: int = 0,
):
    """
    Récupère les entrées PAR et provisions pour un palier donné (0, 30, 90, 180, 360).
    Date = dernier jour du mois (month/year).
    """
    try:
        if par not in (0, 30, 90, 180, 360):
            raise HTTPException(status_code=400, detail="par doit être 0, 30, 90, 180 ou 360")
        data = get_entrees_par_data(month=month, year=year, par_bucket=par)
        return {"data": data, "par": par, "month": month, "year": year}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_message = str(e) if str(e) else repr(e)
        logger.error("❌ Entrées PAR: %s\n%s", error_message, error_detail, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Entrées PAR: {error_message}")


@router.get("/data/gl-lookup")
async def get_gl_lookup_endpoint(gl_code: Optional[str] = None, gl_desc: Optional[str] = None):
    """
    Récupère un ou des GL depuis CFSFCUBS145.GLVW_GLMASTER_E.
    
    - gl_code: recherche exacte par code (retourne 1 résultat)
    - gl_desc: recherche partielle par libellé (retourne une liste)
    
    Returns:
        {"numero_gl": ..., "nom_gl": ...} ou liste pour la recherche par libellé
    """
    try:
        if gl_code:
            result = get_gl_by_code(gl_code)
            if result:
                return {"data": result}
            return {"data": None, "message": "GL non trouvé"}
        if gl_desc:
            results = search_gl(gl_desc=gl_desc)
            return {"data": results}
        raise HTTPException(status_code=400, detail="Fournir gl_code ou gl_desc")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("Erreur GL lookup: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/data/cr-par-agence")
async def get_cr_par_agence_data(body: dict):
    """
    Données CR par agence pour une liste de parent GL (sous-rubrique).
    Body: { "date_from": "DD/MM/YYYY", "date_to": "DD/MM/YYYY", "parent_gl_codes": ["702120000000", ...] }
    Retourne les montants par AC_BRANCH / BRANCH_NAME pour la période VALUE_DT.
    """
    try:
        date_from = (body.get("date_from") or "").strip()
        date_to = (body.get("date_to") or "").strip()
        codes = body.get("parent_gl_codes") or []
        if not date_from or not date_to:
            raise HTTPException(status_code=400, detail="date_from et date_to requis (DD/MM/YYYY)")
        if not codes:
            return {"data": []}
        rows = get_cr_data_by_parent_gl(
            date_from=date_from,
            date_to=date_to,
            parent_gl_codes=[str(c).strip() for c in codes],
        )
        return {"data": rows}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("Erreur CR par Agence: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

