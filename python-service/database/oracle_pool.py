"""
Pool de connexions Oracle pour optimiser les performances
"""
import logging
import threading
from queue import Queue, Empty
from typing import Optional
from contextlib import contextmanager
from database.oracle import get_oracle_connection
from config.settings import ORACLE_CONFIG

logger = logging.getLogger(__name__)

# Configuration du pool
POOL_SIZE = 5
MAX_OVERFLOW = 10
POOL_TIMEOUT = 30  # secondes

class OracleConnectionPool:
    """Pool de connexions Oracle thread-safe"""
    
    def __init__(self, pool_size: int = POOL_SIZE, max_overflow: int = MAX_OVERFLOW):
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool = Queue(maxsize=pool_size)
        self._overflow = []
        self._lock = threading.Lock()
        self._created = 0
        
        # Pré-créer quelques connexions
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialise le pool avec quelques connexions"""
        try:
            for _ in range(min(3, self.pool_size)):
                conn = get_oracle_connection()
                self._pool.put(conn)
                self._created += 1
            logger.info(f"Pool Oracle initialisé avec {self._pool.qsize()} connexions")
        except Exception as e:
            logger.warning(f"Impossible de pré-initialiser le pool: {e}")
    
    def _create_connection(self):
        """Crée une nouvelle connexion"""
        try:
            conn = get_oracle_connection()
            self._created += 1
            logger.debug(f"Nouvelle connexion créée (total: {self._created})")
            return conn
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une connexion: {e}")
            raise
    
    def get_connection(self, timeout: float = POOL_TIMEOUT):
        """
        Récupère une connexion du pool
        
        Args:
            timeout: Timeout en secondes pour obtenir une connexion
            
        Returns:
            Connexion Oracle
        """
        # Essayer d'obtenir une connexion du pool principal
        try:
            conn = self._pool.get(timeout=timeout)
            # Vérifier si la connexion est toujours valide
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.close()
                return conn
            except Exception:
                # La connexion est invalide, en créer une nouvelle
                logger.warning("Connexion invalide détectée, création d'une nouvelle")
                try:
                    conn.close()
                except:
                    pass
                return self._create_connection()
        except Empty:
            # Pool principal vide, vérifier le overflow
            with self._lock:
                if len(self._overflow) < self.max_overflow:
                    conn = self._create_connection()
                    self._overflow.append(conn)
                    return conn
                else:
                    # Attendre qu'une connexion soit disponible
                    logger.warning(f"Pool saturé, attente d'une connexion disponible...")
                    conn = self._pool.get(timeout=timeout)
                    return conn
    
    def return_connection(self, conn):
        """Retourne une connexion au pool"""
        if conn is None:
            return
        
        # Vérifier si la connexion est dans le overflow
        with self._lock:
            if conn in self._overflow:
                self._overflow.remove(conn)
                try:
                    conn.close()
                except:
                    pass
                return
        
        # Retourner au pool principal
        try:
            self._pool.put_nowait(conn)
        except:
            # Pool plein, fermer la connexion
            try:
                conn.close()
            except:
                pass
    
    @contextmanager
    def get_connection_context(self, timeout: float = POOL_TIMEOUT):
        """
        Context manager pour obtenir une connexion du pool
        
        Usage:
            with pool.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        conn = None
        try:
            conn = self.get_connection(timeout)
            yield conn
        finally:
            if conn:
                self.return_connection(conn)
    
    def close_all(self):
        """Ferme toutes les connexions du pool"""
        # Fermer les connexions du pool principal
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except:
                pass
        
        # Fermer les connexions du overflow
        with self._lock:
            for conn in self._overflow:
                try:
                    conn.close()
                except:
                    pass
            self._overflow.clear()
        
        logger.info("Toutes les connexions du pool ont été fermées")
    
    def get_stats(self):
        """Retourne des statistiques sur le pool"""
        with self._lock:
            return {
                'pool_size': self.pool_size,
                'available': self._pool.qsize(),
                'overflow': len(self._overflow),
                'total_created': self._created
            }


# Instance globale du pool
_pool: Optional[OracleConnectionPool] = None


def get_pool() -> OracleConnectionPool:
    """Récupère l'instance globale du pool"""
    global _pool
    if _pool is None:
        _pool = OracleConnectionPool()
    return _pool


def init_pool(pool_size: int = POOL_SIZE, max_overflow: int = MAX_OVERFLOW):
    """Initialise le pool avec des paramètres personnalisés"""
    global _pool
    if _pool is not None:
        _pool.close_all()
    _pool = OracleConnectionPool(pool_size, max_overflow)
    logger.info(f"Pool Oracle initialisé: size={pool_size}, max_overflow={max_overflow}")


def close_pool():
    """Ferme le pool global"""
    global _pool
    if _pool is not None:
        _pool.close_all()
        _pool = None
