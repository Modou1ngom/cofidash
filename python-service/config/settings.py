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
# ORACLE_DASH_SCHEMA : préfixe unique si les 3 tables sont sous le même owner (ex. DATAMART).
# Sinon surcharger chaque nom : ORACLE_DASH_ETAT_CPT_TABLE=OWNER.DASH_ETAT_CPT
def _dash_domiciliation_table(env_explicit: str, short_name: str) -> str:
    explicit = os.getenv(env_explicit, "").strip()
    if explicit:
        return explicit
    schema = os.getenv("ORACLE_DASH_SCHEMA", "").strip().rstrip(".")
    if schema:
        return f"{schema}.{short_name}"
    return short_name


ORACLE_DASH_ETAT_CPT_TABLE = _dash_domiciliation_table("ORACLE_DASH_ETAT_CPT_TABLE", "DASH_ETAT_CPT")
ORACLE_DASH_TOMBE_MOIS_TABLE = _dash_domiciliation_table("ORACLE_DASH_TOMBE_MOIS_TABLE", "DASH_TOMBE_MOIS")
ORACLE_DASH_EXIGIBLE_TABLE = _dash_domiciliation_table("ORACLE_DASH_EXIGIBLE_TABLE", "DASH_EXIGIBLE")

# Si 1 : en ORA-00942 (table absente), retourner 200 + data vide au lieu de 500 (dashboard utilisable).
ORACLE_DOMICILIATION_ORA942_EMPTY = os.getenv(
    "ORACLE_DOMICILIATION_ORA942_EMPTY", "1"
).strip().lower() in ("1", "true", "yes", "on")

