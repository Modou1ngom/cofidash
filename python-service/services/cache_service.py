"""
Service de cache pour optimiser les performances des requêtes Oracle
"""
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from functools import wraps

logger = logging.getLogger(__name__)

# Cache en mémoire (peut être remplacé par Redis plus tard)
_cache: Dict[str, Dict[str, Any]] = {}
_cache_enabled = True
_default_ttl = 300  # 5 minutes par défaut


def generate_cache_key(*args, **kwargs) -> str:
    """Génère une clé de cache à partir des arguments"""
    # Créer une représentation stable des arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_cache(key: str) -> Optional[Any]:
    """Récupère une valeur du cache"""
    if not _cache_enabled:
        return None
    
    if key not in _cache:
        return None
    
    cache_entry = _cache[key]
    
    # Vérifier si le cache a expiré
    if datetime.now() > cache_entry['expires_at']:
        del _cache[key]
        logger.debug(f"Cache expiré pour la clé: {key}")
        return None
    
    logger.debug(f"Cache hit pour la clé: {key}")
    return cache_entry['value']


def set_cache(key: str, value: Any, ttl: int = None) -> None:
    """Stocke une valeur dans le cache"""
    if not _cache_enabled:
        return
    
    ttl = ttl or _default_ttl
    expires_at = datetime.now() + timedelta(seconds=ttl)
    
    _cache[key] = {
        'value': value,
        'expires_at': expires_at,
        'created_at': datetime.now()
    }
    
    logger.debug(f"Cache set pour la clé: {key} (TTL: {ttl}s)")


def clear_cache(pattern: Optional[str] = None) -> int:
    """Efface le cache. Si pattern est fourni, efface seulement les clés correspondantes"""
    if pattern:
        keys_to_delete = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_delete:
            del _cache[key]
        logger.info(f"Cache effacé: {len(keys_to_delete)} entrées correspondant à '{pattern}'")
        return len(keys_to_delete)
    else:
        count = len(_cache)
        _cache.clear()
        logger.info(f"Cache complètement effacé: {count} entrées")
        return count


def cache_result(ttl: int = None, key_prefix: str = ""):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Args:
        ttl: Time to live en secondes (défaut: 5 minutes)
        key_prefix: Préfixe pour la clé de cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Vérifier le cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Mettre en cache le résultat
            set_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Retourne des statistiques sur le cache"""
    now = datetime.now()
    valid_entries = sum(1 for entry in _cache.values() if entry['expires_at'] > now)
    expired_entries = len(_cache) - valid_entries
    
    return {
        'total_entries': len(_cache),
        'valid_entries': valid_entries,
        'expired_entries': expired_entries,
        'cache_enabled': _cache_enabled,
        'default_ttl': _default_ttl
    }


def enable_cache():
    """Active le cache"""
    global _cache_enabled
    _cache_enabled = True
    logger.info("Cache activé")


def disable_cache():
    """Désactive le cache"""
    global _cache_enabled
    _cache_enabled = False
    logger.info("Cache désactivé")


def set_default_ttl(ttl: int):
    """Définit le TTL par défaut"""
    global _default_ttl
    _default_ttl = ttl
    logger.info(f"TTL par défaut défini à {ttl} secondes")
