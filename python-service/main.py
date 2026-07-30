"""
Service Python pour générer des graphiques pour COFIdash Dashboard
Utilise FastAPI pour exposer des endpoints API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        start_backup_scheduler()
        logger.info(
            "✅ Pools Oracle (DASH + Flexcube), cache, base locale C360/New Deal "
            "et planificateur sauvegarde (06h / 12h) initialisés"
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoie les ressources à l'arrêt de l'application"""
    try:
        stop_backup_scheduler()
        close_pools()
        logger.info("✅ Pools de connexions Oracle fermés")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la fermeture: {e}", exc_info=True)

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
