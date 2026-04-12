"""
Configuration du service Python pour COFIdash Dashboard
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# python-service/.env (non versionné)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')


# Oracle Cofina (REPORT_GROUPE) — mot de passe uniquement via ORACLE_COFINA_PASSWORD (fichier .env local, non versionné)
ORACLE_COFINA_CONFIG = {
    'host': os.getenv('ORACLE_COFINA_HOST', ''),
    'port': os.getenv('ORACLE_COFINA_PORT', ''),
    'service_name': os.getenv('ORACLE_COFINA_SERVICE_NAME', ''),
    'username': os.getenv('ORACLE_COFINA_USERNAME', ''),
    'password': os.getenv('ORACLE_COFINA_PASSWORD', ''),
}




