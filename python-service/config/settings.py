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

# Domiciliation de flux (collecte) — tables DASH vues par ORACLE_COFINA_USERNAME.
# En cas d’ORA-00942 en production : synonymes manquants ou objets dans un autre schéma.
# Exemple : ORACLE_DASH_ETAT_CPT_TABLE=REPORT_GROUPE.DASH_ETAT_CPT
ORACLE_DASH_ETAT_CPT_TABLE = os.getenv("ORACLE_DASH_ETAT_CPT_TABLE", "DASH_ETAT_CPT").strip()
ORACLE_DASH_TOMBE_MOIS_TABLE = os.getenv("ORACLE_DASH_TOMBE_MOIS_TABLE", "DASH_TOMBE_MOIS").strip()
ORACLE_DASH_EXIGIBLE_TABLE = os.getenv("ORACLE_DASH_EXIGIBLE_TABLE", "DASH_EXIGIBLE").strip()

