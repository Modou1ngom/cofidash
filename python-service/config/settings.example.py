"""
Configuration du service Python pour COFIdash Dashboard
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Oracle Cofina (REPORT_GROUPE) — variables ORACLE_COFINA_* dans .env
ORACLE_COFINA_CONFIG = {
    'host': os.getenv('ORACLE_COFINA_HOST', ''),
    'port': os.getenv('ORACLE_COFINA_PORT', ''),
    'service_name': os.getenv('ORACLE_COFINA_SERVICE_NAME', ''),
    'username': os.getenv('ORACLE_COFINA_USERNAME', ''),
    'password': os.getenv('ORACLE_COFINA_PASSWORD', ''),
}

# Collecte / domiciliation
# ORACLE_DASH_SCHEMA=OWNER
# ORACLE_DOMICILIATION_ORA942_EMPTY=1
