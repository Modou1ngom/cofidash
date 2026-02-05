"""
Endpoints pour gérer le cache
"""
from fastapi import APIRouter
from services.cache_service import (
    clear_cache, get_cache_stats, enable_cache, 
    disable_cache, set_default_ttl
)

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_statistics():
    """Retourne les statistiques du cache"""
    return get_cache_stats()


@router.post("/clear")
async def clear_cache_endpoint(pattern: str = None):
    """Efface le cache. Optionnellement, efface seulement les clés correspondant à un pattern"""
    count = clear_cache(pattern)
    return {"message": f"Cache effacé: {count} entrées", "count": count}


@router.post("/enable")
async def enable_cache_endpoint():
    """Active le cache"""
    enable_cache()
    return {"message": "Cache activé"}


@router.post("/disable")
async def disable_cache_endpoint():
    """Désactive le cache"""
    disable_cache()
    return {"message": "Cache désactivé"}


@router.post("/ttl")
async def set_ttl_endpoint(ttl: int):
    """Définit le TTL par défaut du cache en secondes"""
    set_default_ttl(ttl)
    return {"message": f"TTL par défaut défini à {ttl} secondes"}
