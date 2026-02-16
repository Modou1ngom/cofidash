"""
Configuration du service Python pour COFIdash Dashboard
"""
import os

# Configuration de la connexion Oracle
# Toutes les valeurs sont définies via des variables d'environnement
# Variables d'environnement requises:
#   - ORACLE_HOST: Adresse IP ou hostname du serveur Oracle
#   - ORACLE_PORT: Port du serveur Oracle (par défaut: 1521)
#   - ORACLE_SERVICE_NAME: Nom du service Oracle
#   - ORACLE_USERNAME: Nom d'utilisateur Oracle
#   - ORACLE_PASSWORD: Mot de passe Oracle
ORACLE_CONFIG = {
    'host': os.getenv('ORACLE_HOST', 'localhost'),
    'port': os.getenv('ORACLE_PORT', '1521'),
    'service_name': os.getenv('ORACLE_SERVICE_NAME', 'ORCL'),
    'username': os.getenv('ORACLE_USERNAME', ''),
    'password': os.getenv('ORACLE_PASSWORD', '')
}