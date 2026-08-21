"""
Pools de connexions Oracle — DASH (REPORT_GROUPE) et Flexcube (CFSFCUBS145).
"""
import logging
import threading
import time
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Callable, Optional

from database.oracle import get_oracle_connection_cofina, get_oracle_connection_flexcube

logger = logging.getLogger(__name__)

# Pools statiques : taille fixe, pas de sessions « overflow ».
FLEXCUBE_POOL_SIZE = 8
DASH_POOL_SIZE = 0  # base DASH / REPORT_GROUPE désactivée
MAX_OVERFLOW = 0
POOL_SIZE = FLEXCUBE_POOL_SIZE  # alias historique (Flexcube)
# Ping SELECT 1 uniquement si la connexion a dormi plus longtemps.
_PING_AFTER_IDLE_SEC = 60.0


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
        self.max_total = max(0, pool_size) + max(0, max_overflow)
        # Queue(maxsize=0) = file infinie en Python : on force au moins 1 si le pool est actif.
        self._pool = Queue(maxsize=self.max_total if self.max_total > 0 else 1)
        self._lock = threading.Lock()
        self._created = 0
        self._checked_out = 0
        self._initialize_pool(warmup=warmup)

    def _initialize_pool(self, warmup: int = 1):
        """Pré-chauffe au plus `warmup` connexion(s) ; 0 = initialisation paresseuse."""
        if warmup <= 0:
            logger.info("Pool Oracle [%s] prêt (connexions à la demande)", self.name)
            return
        try:
            for _ in range(min(warmup, self.pool_size)):
                conn = self._connect_fn()
                self._mark_used(conn)
                self._pool.put(conn)
                self._created += 1
            logger.info(
                "Pool Oracle [%s] initialisé avec %s connexion(s)",
                self.name,
                self._pool.qsize(),
            )
        except Exception as exc:
            logger.warning("Impossible de pré-initialiser le pool [%s]: %s", self.name, exc)

    @staticmethod
    def _mark_used(conn) -> None:
        try:
            conn._cofidash_last_used = time.monotonic()
        except Exception:
            pass

    @staticmethod
    def _needs_ping(conn) -> bool:
        last = getattr(conn, "_cofidash_last_used", 0.0)
        try:
            return (time.monotonic() - float(last or 0.0)) >= _PING_AFTER_IDLE_SEC
        except Exception:
            return True

    @staticmethod
    def _ping(conn) -> bool:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.close()
            return True
        except Exception:
            return False

    def _create_connection(self):
        conn = self._connect_fn()
        self._mark_used(conn)
        logger.debug("Nouvelle connexion [%s] (total: %s)", self.name, self._created)
        return conn

    def _close_quietly(self, conn) -> None:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    def get_connection(self, timeout: Optional[float] = None):
        conn = None
        try:
            conn = self._pool.get_nowait()
        except Empty:
            pass

        if conn is None:
            reserved = False
            with self._lock:
                if self._created < self.max_total:
                    self._created += 1
                    reserved = True
            if reserved:
                try:
                    conn = self._create_connection()
                    with self._lock:
                        self._checked_out += 1
                    return conn
                except Exception:
                    with self._lock:
                        self._created = max(0, self._created - 1)
                    raise

        if conn is None:
            stats = self.get_stats()
            logger.warning(
                "Pool [%s] saturé, attente... (in_use=%s created=%s idle=%s max=%s)",
                self.name,
                stats["in_use"],
                stats["total_created"],
                stats["available"],
                self.max_total,
            )
            wait = 30.0 if timeout is None else timeout
            conn = self._pool.get(timeout=wait)

        if self._needs_ping(conn) and not self._ping(conn):
            logger.warning("Connexion invalide [%s], recréation", self.name)
            self._close_quietly(conn)
            try:
                conn = self._create_connection()
            except Exception:
                with self._lock:
                    self._created = max(0, self._created - 1)
                raise

        self._mark_used(conn)
        with self._lock:
            self._checked_out += 1
        return conn

    def return_connection(self, conn):
        if conn is None:
            return
        with self._lock:
            self._checked_out = max(0, self._checked_out - 1)
        self._mark_used(conn)
        try:
            self._pool.put_nowait(conn)
        except Exception:
            self._close_quietly(conn)
            with self._lock:
                self._created = max(0, self._created - 1)

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
            self._created = 0
            self._checked_out = 0
        logger.info("Pool Oracle [%s] fermé", self.name)

    def get_stats(self):
        with self._lock:
            created = self._created
            in_use = self._checked_out
        idle = self._pool.qsize()
        return {
            "name": self.name,
            "pool_size": self.pool_size,
            "available": idle,
            "in_use": in_use,
            "overflow": max(0, created - self.pool_size),
            "total_created": created,
        }


_pool_cofina: Optional[OracleConnectionPool] = None
_pool_flexcube: Optional[OracleConnectionPool] = None
_dash_disabled = True


class DashPoolDisabled(RuntimeError):
    """La base DASH (REPORT_GROUPE) n'est plus ouverte par Cofidash."""


def get_pool_cofina() -> OracleConnectionPool:
    """Pool REPORT_GROUPE — tables DASH. Désactivé : plus aucune session."""
    global _pool_cofina
    if _dash_disabled or _pool_cofina is None:
        raise DashPoolDisabled(
            "La base DASH n'est plus utilisée. "
            "Les écrans reporting DASH (production, DAT, transferts…) sont indisponibles."
        )
    return _pool_cofina


def get_pool_flexcube() -> OracleConnectionPool:
    """Pool Flexcube — schéma CFSFCUBS145 (KYC, crédits, écritures, …)."""
    global _pool_flexcube
    if _pool_flexcube is None:
        _pool_flexcube = OracleConnectionPool(
            get_oracle_connection_flexcube,
            pool_size=FLEXCUBE_POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            name="flexcube",
        )
    return _pool_flexcube


def get_pool() -> OracleConnectionPool:
    """Alias historique → pool DASH (REPORT_GROUPE)."""
    return get_pool_cofina()


def init_pools(
    pool_size: Optional[int] = None,
    max_overflow: int = MAX_OVERFLOW,
    warmup: Optional[int] = None,
    flexcube_size: int = FLEXCUBE_POOL_SIZE,
    dash_size: int = DASH_POOL_SIZE,
):
    """Initialise le pool Flexcube. Le pool DASH n'est créé que si dash_size > 0."""
    global _pool_cofina, _pool_flexcube, _dash_disabled
    close_pools()
    if pool_size is not None:
        flexcube_size = pool_size
        if dash_size != 0:
            dash_size = pool_size
    _dash_disabled = dash_size <= 0
    flex_warmup = flexcube_size if warmup is None else warmup
    if not _dash_disabled:
        dash_warmup = dash_size if warmup is None else warmup
        _pool_cofina = OracleConnectionPool(
            get_oracle_connection_cofina,
            pool_size=dash_size,
            max_overflow=max_overflow,
            name="cofina-dash",
            warmup=dash_warmup,
        )
    else:
        _pool_cofina = None
        logger.info("Pool DASH désactivé : aucune session REPORT_GROUPE")
    _pool_flexcube = OracleConnectionPool(
        get_oracle_connection_flexcube,
        pool_size=flexcube_size,
        max_overflow=max_overflow,
        name="flexcube",
        warmup=flex_warmup,
    )
    logger.info(
        "Pools Oracle statiques: flexcube=%s dash=%s overflow=%s",
        flexcube_size,
        0 if _dash_disabled else dash_size,
        max_overflow,
    )


def init_pool(pool_size: int = FLEXCUBE_POOL_SIZE, max_overflow: int = MAX_OVERFLOW):
    """Compatibilité — initialise les deux pools à la même taille."""
    init_pools(pool_size=pool_size, max_overflow=max_overflow)


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
