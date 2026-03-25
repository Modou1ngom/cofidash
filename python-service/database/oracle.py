"""
Gestion de la connexion à la base de données Oracle
"""
from fastapi import HTTPException
import socket
import logging
from config.settings import ORACLE_CONFIG

logger = logging.getLogger(__name__)

try:
    import oracledb
except ImportError:
    try:
        import cx_Oracle as oracledb
    except ImportError:
        raise ImportError("Veuillez installer oracledb ou cx_Oracle: pip install oracledb")


def get_oracle_connection():
    """Établit une connexion à la base de données Oracle"""
    
    # Vérifier d'abord la connectivité réseau
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ORACLE_CONFIG['host'], int(ORACLE_CONFIG['port'])))
        sock.close()
        
        if result != 0:
            error_msg = (
                f"Impossible de se connecter au serveur Oracle.\n"
                f"Vérifiez que:\n"
                f"1. Le serveur Oracle est accessible à l'adresse {ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}\n"
                f"2. Le firewall n'bloque pas le port {ORACLE_CONFIG['port']}\n"
                f"3. Le serveur Oracle est démarré et écoute sur ce port\n"
                f"Code d'erreur: {result}"
            )
            raise HTTPException(status_code=500, detail=error_msg)
    except socket.gaierror:
        error_msg = (
            f"Impossible de résoudre l'adresse du serveur Oracle: {ORACLE_CONFIG['host']}\n"
            f"Vérifiez que l'adresse IP ou le nom d'hôte est correct."
        )
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        # Si la vérification de connectivité échoue, continuer quand même
        # car parfois le socket peut échouer mais Oracle accepter la connexion
        pass
    
    try:
        # Essayer d'abord avec la nouvelle API oracledb (version >= 2.0)
        try:
            # Nouvelle API oracledb avec connect()
            dsn = oracledb.makedsn(
                ORACLE_CONFIG['host'],
                ORACLE_CONFIG['port'],
                service_name=ORACLE_CONFIG['service_name']
            )
            # Connecter sans timeout (le timeout n'est pas supporté dans cette version d'oracledb)
            # Le timeout réseau est géré au niveau du socket, pas au niveau de la connexion Oracle
            connection = oracledb.connect(
                user=ORACLE_CONFIG['username'],
                password=ORACLE_CONFIG['password'],
                dsn=dsn
            )
            return connection
        except AttributeError:
            # Si makedsn n'existe pas, utiliser la syntaxe directe
            dsn = f"{ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}/{ORACLE_CONFIG['service_name']}"
            connection = oracledb.connect(
                user=ORACLE_CONFIG['username'],
                password=ORACLE_CONFIG['password'],
                dsn=dsn
            )
            return connection
    except Exception as e:
        # Capturer plus de détails sur l'erreur
        error_str = str(e) if str(e) else repr(e)
        error_type = type(e).__name__
        
        # Extraire le code d'erreur Oracle si présent
        error_code = None
        if hasattr(e, 'code'):
            error_code = e.code
        elif hasattr(e, 'args') and len(e.args) > 0:
            error_code = e.args[0] if isinstance(e.args[0], (int, str)) else None
        
        # Détecter l'erreur ORA-00257 spécifiquement (problème d'archivage)
        is_ora_00257 = 'ORA-00257' in error_str or error_code == '00257' or error_code == 257
        
        if is_ora_00257:
            error_msg = (
                f"❌ Erreur Oracle ORA-00257: Problème d'archivage détecté\n\n"
                f"Le serveur Oracle a un problème d'archivage qui empêche les connexions normales.\n\n"
                f"🔍 Détails techniques:\n"
                f"  Type: {error_type}\n"
                f"  Code d'erreur: ORA-00257\n"
                f"  Host: {ORACLE_CONFIG['host']}\n"
                f"  Port: {ORACLE_CONFIG['port']}\n"
                f"  Service: {ORACLE_CONFIG['service_name']}\n"
                f"  Username: {ORACLE_CONFIG['username']}\n\n"
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
        
        # Vérifier si c'est une erreur de connexion Oracle
        is_oracle_error = (
            'ORA-' in error_str or 
            'connection' in error_str.lower() or 
            'cannot connect' in error_str.lower() or
            'timeout' in error_str.lower() or
            'network' in error_str.lower() or
            error_type in ('DatabaseError', 'OperationalError', 'InterfaceError')
        )
        
        if is_oracle_error:
            error_msg = (
                f"Erreur de connexion Oracle:\n"
                f"Type: {error_type}\n"
                f"Host: {ORACLE_CONFIG['host']}\n"
                f"Port: {ORACLE_CONFIG['port']}\n"
                f"Service: {ORACLE_CONFIG['service_name']}\n"
                f"Username: {ORACLE_CONFIG['username']}\n"
            )
            if error_code:
                error_msg += f"Code d'erreur: {error_code}\n"
            if error_str:
                error_msg += f"Message: {error_str}\n"
            error_msg += (
                f"\nVérifiez que:\n"
                f"1. Le serveur Oracle est démarré et accessible\n"
                f"2. Les paramètres de connexion sont corrects\n"
                f"3. Le réseau/firewall permet la connexion au port {ORACLE_CONFIG['port']}\n"
                f"4. Le service name '{ORACLE_CONFIG['service_name']}' est correct\n"
                f"5. Les identifiants (username/password) sont valides"
            )
            logger.error(f"Erreur de connexion Oracle: {error_type} - {error_str}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
        else:
            error_msg = (
                f"Erreur de connexion Oracle (Type: {error_type}):\n"
                f"Message: {error_str}\n"
                f"Host: {ORACLE_CONFIG['host']}\n"
                f"Port: {ORACLE_CONFIG['port']}\n"
                f"Service: {ORACLE_CONFIG['service_name']}"
            )
            logger.error(f"Erreur inattendue lors de la connexion Oracle: {error_type} - {error_str}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)

