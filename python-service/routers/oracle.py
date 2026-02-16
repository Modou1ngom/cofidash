"""
Router pour les endpoints Oracle
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
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
    try:
        return get_production_nombre_data(date_m_debut, date_m_fin, month, year)
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
    year: Optional[int] = None
):
    """
    Récupère les données de production en nombre (nombre de crédits décaissés par agence) depuis Oracle.
    Route de compatibilité - utilise /api/oracle/data/production/nombre en interne.
    """
    return await get_production_nombre_data_endpoint(date_m_debut, date_m_fin, month, year)


@router.get("/data/production-volume")
async def get_production_volume_data_endpoint(
    date_m_debut: Optional[str] = None,
    date_m_fin: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
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
        return get_production_volume_data(date_m_debut, date_m_fin, month, year)
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
    try:
        return get_encours_credit_data(month_m, year_m, month_m1, year_m1)
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
                "hierarchicalData": result.get('hierarchicalData', {})
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
    date: Optional[str] = None
):
    """
    Récupère les données de transferts d'argent depuis Oracle
    
    Args:
        period: Période d'analyse ("week", "month", "year"). Par défaut "month".
        month: Mois à analyser (1-12). Si non fourni, utilise le mois courant.
        year: Année à analyser. Si non fourni, utilise l'année courante.
        date: Date au format YYYY-MM-DD - pour period="week"
    
    Returns:
        Données de transferts d'argent par agence et par service avec:
        - Tableau détaillé des agences (objectif, volume M, volume M-1, variation, TRO, contribution, commission)
        - Résumé par service de transfert (volume et commission)
    """
    try:
        logger.info(f"📅 Paramètres reçus pour get_transfer_data: period={period}, month={month}, year={year}, date={date}")
        data = get_transfer_data(period=period, month=month, year=year, date=date)
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

