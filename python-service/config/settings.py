"""
Configuration du service Python pour COFIdash Dashboard
"""
import os

# Configuration de la connexion Oracle
# Chaîne de connexion: oracle://report_sn:rEport$ml221@10.44.221.104:1522/?service_name=FCPRDSNPDB
ORACLE_CONFIG = {
    'host': os.getenv('ORACLE_HOST', '10.44.221.104'),
    'port': os.getenv('ORACLE_PORT', '1522'),
    'service_name': os.getenv('ORACLE_SERVICE_NAME', 'FCPRDSNPDB'),
    'username': os.getenv('ORACLE_USERNAME', 'report_sn'),
    'password': os.getenv('ORACLE_PASSWORD', 'rEport$ml221')
}

