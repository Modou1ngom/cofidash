"""
Service Python pour générer des graphiques pour COFIdash Dashboard
Utilise FastAPI pour exposer des endpoints API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

from routers import charts, oracle, cache, c360, vue360
from database.oracle_pool import init_pools, close_pools
from database.c360_local_db import init_local_db
from services.cache_service import enable_cache
from services.new_deal import (
    start_backup_scheduler,
    stop_backup_scheduler,
    init_new_deal_local_db,
)
from services.objectif_epv_vue_backup_service import init_objectif_epv_vue_local_db
from services.objectif_epv_vue_backup_scheduler import (
    start_objectif_epv_vue_scheduler,
    stop_objectif_epv_vue_scheduler,
)
from services.collecte_epargne_a_vue_backup_service import init_collecte_epv_vue_local_db
from services.collecte_epargne_a_vue_backup_scheduler import (
    start_collecte_epv_vue_scheduler,
    stop_collecte_epv_vue_scheduler,
)


# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(title="COFIdash Charts API", version="1.0.0")

# Initialiser le pool de connexions Oracle au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialise les ressources au démarrage de l'application"""
    try:
        init_pools(pool_size=5, max_overflow=10)
        enable_cache()
        init_local_db()
        init_new_deal_local_db()
        init_objectif_epv_vue_local_db()
        init_collecte_epv_vue_local_db()
        start_backup_scheduler()
        start_objectif_epv_vue_scheduler()
        start_collecte_epv_vue_scheduler()
        logger.info(
            "✅ Pools Oracle, cache, bases locales (C360/New Deal/objectifs EPV/"
            "collecte EPV) et planificateurs initialisés "
            "(New Deal 06h/12h, objectifs 1er du mois, collecte EPV chaque jour 06h)"
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoie les ressources à l'arrêt de l'application"""
    try:
        stop_backup_scheduler()
        stop_objectif_epv_vue_scheduler()
        stop_collecte_epv_vue_scheduler()
        close_pools()
        logger.info("✅ Pools de connexions Oracle fermés")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la fermeture: {e}", exc_info=True)

# Les réponses de données atteignent plusieurs Mo de JSON très répétitif.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Configuration CORS pour permettre les requêtes depuis Laravel/Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(charts.router)
app.include_router(oracle.router)
app.include_router(cache.router)
app.include_router(c360.router)
app.include_router(vue360.router)


@app.get("/")
async def root():
    """Endpoint de santé"""
    return {"status": "ok", "service": "COFIdash Charts API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
