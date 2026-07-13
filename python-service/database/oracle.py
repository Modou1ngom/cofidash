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
            error_msg = (
                f"❌ Erreur Oracle ORA-00257: Problème d'archivage détecté\n\n"
                f"Le serveur Oracle a un problème d'archivage qui empêche les connexions normales.\n\n"
                f"🔍 Détails techniques:\n"
                f"  Type: {error_type}\n"
                f"  Code d'erreur: ORA-00257\n"
                f"  Host: {host}\n"
                f"  Port: {port}\n"
                f"  Service: {service_name}\n"
                f"  Username: {username}\n\n"
                f"⚠️  Solution:\n"
                f"  Cette erreur indique que:\n"
                f"  1. L'espace disque pour les archives est plein, OU\n"
                f"  2. La configuration d'archivage est incorrecte\n\n"
                f"  Action requise:\n"
                f"  - Contactez l'administrateur Oracle pour résoudre le problème\n"
                f"  - L'administrateur doit se connecter en mode SYSDBA et:\n"
                f"    • Libérer de l'espace disque pour les archives, OU\n"
                f"    • Désactiver temporairement l'archivage si nécessaire\n"
                f"    • Vérifier la configuration d'archivage\n\n"
                f"  Une fois le problème résolu, les connexions normales pourront reprendre.\n\n"
                f"  Message Oracle complet: {error_str}"
            )
            logger.error(f"Erreur ORA-00257 détectée: {error_str}", exc_info=True)
            raise HTTPException(status_code=503, detail=error_msg)

        is_oracle_error = (
            'ORA-' in error_str
            or 'connection' in error_str.lower()
            or 'cannot connect' in error_str.lower()
            or 'timeout' in error_str.lower()
            or 'network' in error_str.lower()
            or error_type in ('DatabaseError', 'OperationalError', 'InterfaceError')
        )
        if is_oracle_error:
            error_msg = (
                f"Erreur de connexion Oracle:\n"
                f"Type: {error_type}\n"
                f"Host: {host}\n"
                f"Port: {port}\n"
                f"Service: {service_name}\n"
                f"Username: {username}\n"
            )
            if error_code:
                error_msg += f"Code d'erreur: {error_code}\n"
            if error_str:
                error_msg += f"Message: {error_str}\n"
            error_msg += (
                f"\nVérifiez que:\n"
                f"1. Le serveur Oracle est démarré et accessible\n"
                f"2. Les paramètres de connexion sont corrects\n"
                f"3. Le réseau/firewall permet la connexion au port {port}\n"
                f"4. Le service name '{service_name}' est correct\n"
                f"5. Les identifiants (username/password) sont valides"
            )
            logger.error(f"Erreur de connexion Oracle: {error_type} - {error_str}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
        error_msg = (
            f"Erreur de connexion Oracle (Type: {error_type}):\n"
            f"Message: {error_str}\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"Service: {service_name}"
        )
        logger.error(f"Erreur inattendue lors de la connexion Oracle: {error_type} - {error_str}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


def _require_password(cfg: dict, env_var: str, label: str):
    if not (cfg.get('password') or '').strip():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Mot de passe Oracle {label} manquant. Définissez {env_var} "
                "(fichier .env du service Python)."
            ),
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
            raise HTTPException(
                status_code=500,
                detail=f"Serveur Oracle {label} inaccessible: {host}:{port} (code {result})",
            )
    except socket.gaierror:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de résoudre l'hôte Oracle {label}: {host}",
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
        raise HTTPException(
            status_code=500,
            detail=(
                "Oracle Flexcube non configuré. Définissez ORACLE_FLEXCUBE_HOST "
                "ou ORACLE_HOST dans python-service/.env"
            ),
        )
    _require_password(cfg, "ORACLE_FLEXCUBE_PASSWORD ou ORACLE_PASSWORD", "Flexcube")
    _check_host_reachable(cfg, "Flexcube")
    return _oracle_connect(cfg)

