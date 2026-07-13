"""
Pools de connexions Oracle — DASH (REPORT_GROUPE) et Flexcube (CFSFCUBS145).
"""
import logging
import threading
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Callable, Optional

from database.oracle import get_oracle_connection_cofina, get_oracle_connection_flexcube

logger = logging.getLogger(__name__)

POOL_SIZE = 5
MAX_OVERFLOW = 10


class OracleConnectionPool:
    """Pool de connexions Oracle thread-safe."""

    def __init__(
        self,
        connect_fn: Callable,
        pool_size: int = POOL_SIZE,
        max_overflow: int = MAX_OVERFLOW,
        name: str = "oracle",
        warmup: int = 0,
    ):
        self._connect_fn = connect_fn
        self.name = name
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool = Queue(maxsize=pool_size)
        self._overflow = []
        self._lock = threading.Lock()
        self._created = 0
        self._initialize_pool(warmup=warmup)

    def _initialize_pool(self, warmup: int = 1):
        """Pré-chauffe au plus `warmup` connexion(s) ; 0 = initialisation paresseuse."""
        if warmup <= 0:
            logger.info("Pool Oracle [%s] prêt (connexions à la demande)", self.name)
            return
        try:
            for _ in range(min(warmup, self.pool_size)):
                conn = self._connect_fn()
                self._pool.put(conn)
                self._created += 1
            logger.info(
                "Pool Oracle [%s] initialisé avec %s connexion(s)",
                self.name,
                self._pool.qsize(),
            )
        except Exception as exc:
            logger.warning("Impossible de pré-initialiser le pool [%s]: %s", self.name, exc)

    def _create_connection(self):
        conn = self._connect_fn()
        self._created += 1
        logger.debug("Nouvelle connexion [%s] (total: %s)", self.name, self._created)
        return conn

    def get_connection(self, timeout: Optional[float] = None):
        conn = None
        try:
            conn = self._pool.get_nowait()
        except Empty:
            pass

        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.close()
                return conn
            except Exception:
                logger.warning("Connexion invalide [%s], recréation", self.name)
                try:
                    conn.close()
                except Exception:
                    pass
                return self._create_connection()

        with self._lock:
            if len(self._overflow) < self.max_overflow:
                conn = self._create_connection()
                self._overflow.append(conn)
                return conn

        logger.warning("Pool [%s] saturé, attente...", self.name)
        wait = 30.0 if timeout is None else timeout
        conn = self._pool.get(timeout=wait)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.close()
            return conn
        except Exception:
            logger.warning("Connexion invalide [%s], recréation", self.name)
            try:
                conn.close()
            except Exception:
                pass
            return self._create_connection()

    def return_connection(self, conn):
        if conn is None:
            return
        with self._lock:
            if conn in self._overflow:
                self._overflow.remove(conn)
        try:
            self._pool.put_nowait(conn)
        except Exception:
            with self._lock:
                if len(self._overflow) < self.max_overflow:
                    self._overflow.append(conn)
                    return
            try:
                conn.close()
            except Exception:
                pass

    @contextmanager
    def get_connection_context(self, timeout: Optional[float] = None):
        conn = None
        try:
            conn = self.get_connection(timeout)
            yield conn
        finally:
            if conn:
                self.return_connection(conn)

    def close_all(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
        with self._lock:
            for conn in self._overflow:
                try:
                    conn.close()
                except Exception:
                    pass
            self._overflow.clear()
        logger.info("Pool Oracle [%s] fermé", self.name)

    def get_stats(self):
        with self._lock:
            return {
                "name": self.name,
                "pool_size": self.pool_size,
                "available": self._pool.qsize(),
                "overflow": len(self._overflow),
                "total_created": self._created,
            }


_pool_cofina: Optional[OracleConnectionPool] = None
_pool_flexcube: Optional[OracleConnectionPool] = None


def get_pool_cofina() -> OracleConnectionPool:
    """Pool REPORT_GROUPE — tables DASH (CUSTOMERS, DASH_PRET, …)."""
    global _pool_cofina
    if _pool_cofina is None:
        _pool_cofina = OracleConnectionPool(
            get_oracle_connection_cofina,
            name="cofina-dash",
        )
    return _pool_cofina


def get_pool_flexcube() -> OracleConnectionPool:
    """Pool Flexcube — schéma CFSFCUBS145 (KYC, crédits, écritures, …)."""
    global _pool_flexcube
    if _pool_flexcube is None:
        _pool_flexcube = OracleConnectionPool(
            get_oracle_connection_flexcube,
            name="flexcube",
        )
    return _pool_flexcube


def get_pool() -> OracleConnectionPool:
    """Alias historique → pool DASH (REPORT_GROUPE)."""
    return get_pool_cofina()


def init_pools(
    pool_size: int = POOL_SIZE,
    max_overflow: int = MAX_OVERFLOW,
    warmup: int = 2,
):
    """Initialise les deux pools Oracle (warmup=0 : pas de connexion au démarrage)."""
    global _pool_cofina, _pool_flexcube
    close_pools()
    _pool_cofina = OracleConnectionPool(
        get_oracle_connection_cofina,
        pool_size=pool_size,
        max_overflow=max_overflow,
        name="cofina-dash",
        warmup=warmup,
    )
    _pool_flexcube = OracleConnectionPool(
        get_oracle_connection_flexcube,
        pool_size=pool_size,
        max_overflow=max_overflow,
        name="flexcube",
        warmup=warmup,
    )
    logger.info("Pools Oracle initialisés: cofina-dash + flexcube")


def init_pool(pool_size: int = POOL_SIZE, max_overflow: int = MAX_OVERFLOW):
    """Compatibilité — initialise les deux pools."""
    init_pools(pool_size, max_overflow)


def close_pools():
    global _pool_cofina, _pool_flexcube
    if _pool_cofina is not None:
        _pool_cofina.close_all()
        _pool_cofina = None
    if _pool_flexcube is not None:
        _pool_flexcube.close_all()
        _pool_flexcube = None


def close_pool():
    close_pools()
