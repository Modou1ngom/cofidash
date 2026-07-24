# Liste des agences depuis DASH_RELATION — CODE_BUREAU + AGENCE.
#
# Snapshot = dernier chargement Oracle sur toute la table (MAX global de MIGRATION_DATETIME).
# Un filtre par mois calendaire (MM/YYYY) ne retient qu’un sous-ensemble de lignes et
# sous-compte les agences ; la synchro « toutes les agences » doit utiliser ce snapshot global.

from config.settings import ORACLE_DASH_RELATION_TABLE

_TBL = ORACLE_DASH_RELATION_TABLE

AGENCIES_FROM_DASH_RELATION_SQL = f"""
SELECT DISTINCT
    d.CODE_BUREAU,
    d.AGENCE
FROM {_TBL} d
WHERE d.MIGRATION_DATETIME = (
    SELECT MAX(MIGRATION_DATETIME)
    FROM {_TBL}
)
ORDER BY d.CODE_BUREAU, d.AGENCE
"""

# Variante : même périmètre que le dash clients (un mois MM/YYYY) — moins de lignes.
AGENCIES_FROM_DASH_RELATION_SQL_BY_MONTH = f"""
SELECT DISTINCT
    d.CODE_BUREAU,
    d.AGENCE
FROM {_TBL} d
WHERE d.MIGRATION_DATETIME = (
    SELECT MAX(dr.MIGRATION_DATETIME)
    FROM {_TBL} dr
    WHERE TO_CHAR(dr.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
ORDER BY d.CODE_BUREAU, d.AGENCE
"""
