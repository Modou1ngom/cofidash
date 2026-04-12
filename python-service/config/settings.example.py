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

# Collecte / domiciliation — si ORA-00942, renseigner le schéma ou les synonymes côté DBA
# ORACLE_DASH_ETAT_CPT_TABLE=DASH_ETAT_CPT
# ORACLE_DASH_TOMBE_MOIS_TABLE=DASH_TOMBE_MOIS
# ORACLE_DASH_EXIGIBLE_TABLE=DASH_EXIGIBLE
