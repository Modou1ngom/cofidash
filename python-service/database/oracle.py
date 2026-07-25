"""
Gestion de la connexion à la base de données Oracle
"""
from fastapi import HTTPException
import socket
import logging
from config.settings import ORACLE_COFINA_CONFIG, ORACLE_FLEXCUBE_CONFIG, ORACLE_CONNECT_TIMEOUT

logger = logging.getLogger(__name__)

try:
    import oracledb
except ImportError:
    try:
        import cx_Oracle as oracledb
    except ImportError:
        raise ImportError("Veuillez installer oracledb ou cx_Oracle: pip install oracledb")


def _oracle_connect(config: dict):
    """Établit une connexion Oracle à partir d'un dictionnaire host/port/service_name/username/password."""
    host = config['host']
    port = str(config['port'])
    service_name = config['service_name']
    username = config['username']
    password = config.get('password') or ''

    try:
        connect_kwargs = {"tcp_connect_timeout": ORACLE_CONNECT_TIMEOUT}
        try:
            dsn = oracledb.makedsn(host, port, service_name=service_name)
            return oracledb.connect(
                user=username, password=password, dsn=dsn, **connect_kwargs
            )
        except AttributeError:
            dsn = f"{host}:{port}/{service_name}"
            return oracledb.connect(
                user=username, password=password, dsn=dsn, **connect_kwargs
            )
    except Exception as e:
        error_str = str(e) if str(e) else repr(e)
        error_type = type(e).__name__
        error_code = None
        if hasattr(e, 'code'):
            error_code = e.code
        elif hasattr(e, 'args') and len(e.args) > 0:
            error_code = e.args[0] if isinstance(e.args[0], (int, str)) else None

        is_ora_00257 = 'ORA-00257' in error_str or error_code == '00257' or error_code == 257
        if is_ora_00257:
            logger.error(
                "ORA-00257 archivage Oracle host=%s port=%s service=%s: %s",
                host, port, service_name, error_str,
                exc_info=True,
            )
            raise HTTPException(
                status_code=503,
                detail="Service de données temporairement indisponible.",
            )

        is_oracle_error = (
            'ORA-' in error_str
            or 'connection' in error_str.lower()
            or 'cannot connect' in error_str.lower()
            or 'timeout' in error_str.lower()
            or 'network' in error_str.lower()
            or error_type in ('DatabaseError', 'OperationalError', 'InterfaceError')
        )
        logger.error(
            "Erreur connexion Oracle type=%s host=%s port=%s service=%s user=%s code=%s: %s",
            error_type, host, port, service_name, username, error_code, error_str,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Service de données temporairement indisponible.",
        )


def _require_password(cfg: dict, env_var: str, label: str):
    if not (cfg.get('password') or '').strip():
        logger.error("Mot de passe Oracle manquant pour %s (variable %s)", label, env_var)
        raise HTTPException(
            status_code=500,
            detail="Service de données temporairement indisponible.",
        )


def _check_host_reachable(cfg: dict, label: str):
    host = cfg['host']
    port = int(cfg['port'])
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(ORACLE_CONNECT_TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            logger.error(
                "Serveur Oracle %s inaccessible: %s:%s (code %s)",
                label, host, port, result,
            )
            raise HTTPException(
                status_code=500,
                detail="Service de données temporairement indisponible.",
            )
    except socket.gaierror:
        logger.error("Impossible de résoudre l'hôte Oracle %s: %s", label, host)
        raise HTTPException(
            status_code=500,
            detail="Service de données temporairement indisponible.",
        )
    except HTTPException:
        raise
    except Exception:
        pass


def get_oracle_connection():
    """Connexion Oracle Flexcube (CFSFCUBS145)."""
    return get_oracle_connection_flexcube()


def get_oracle_connection_cofina():
    """
    Connexion Oracle Cofina (REPORT_GROUPE / tables DASH).
    Définir ORACLE_COFINA_PASSWORD dans l'environnement (ou .env chargé au démarrage).
    """
    cfg = ORACLE_COFINA_CONFIG
    _require_password(cfg, "ORACLE_COFINA_PASSWORD", "Cofina (DASH)")
    _check_host_reachable(cfg, "Cofina (DASH)")
    return _oracle_connect(cfg)


def get_oracle_connection_flexcube():
    """
    Connexion Oracle Flexcube (CFSFCUBS145).
    Définir ORACLE_FLEXCUBE_PASSWORD ou ORACLE_PASSWORD dans .env.
    """
    cfg = ORACLE_FLEXCUBE_CONFIG
    if not (cfg.get('host') or '').strip():
        logger.error("Oracle Flexcube non configuré (hôte manquant)")
        raise HTTPException(
            status_code=500,
            detail="Service de données temporairement indisponible.",
        )
    _require_password(cfg, "ORACLE_FLEXCUBE_PASSWORD ou ORACLE_PASSWORD", "Flexcube")
    _check_host_reachable(cfg, "Flexcube")
    return _oracle_connect(cfg)

