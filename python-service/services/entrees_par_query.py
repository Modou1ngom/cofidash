from typing import Tuple

# Entrées PAR : table DASH_ENTREE_PAR (snapshot Cofina)
# Snapshot : dernier MIGRATION_DATETIME du mois calendaire (MM/YYYY), comme DASH_PAR_GLOBAL /
# DASH_DEPOT_GARANTIE — évite 0 ligne si aucune ligne n’a exactement le dernier jour du mois.

ENTREES_PAR_QUERY = """
SELECT
    NO_PRET,
    CHARGE_AFFAIRE,
    BLOC,
    STATUT AS STATUT_DECLASSEMENT,
    NOM_CLIENT,
    DATE_MISE_EN_PLACE,
    CODE_AGENCE,
    AGENCE,
    VOLUME AS PRODUCTION_EN_VOLUME,
    DATE_PREM_ECHEANCE,
    ENCOURS_TOTAL,
    ENCOURS_SAIN,
    ENCOURS_IMPAYE,
    DUREE_IMP_A_DATE AS DUREE_IMPAYE_A_DATE,
    PROVISIONS,
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENTREE_PAR
WHERE MIGRATION_DATETIME = (
    SELECT MAX(d.MIGRATION_DATETIME)
    FROM DASH_ENTREE_PAR d
    WHERE TO_CHAR(d.MIGRATION_DATE_MINUS1, 'MM/YYYY') = :month_year
)
AND (__PAR_BUCKET_WHERE__)
ORDER BY AGENCE, NO_PRET
"""

# Durée d’impayé à date (jours) : égalités strates DASH (1 → PAR0, 31 → PAR30, …, 361 → PAR360).
PAR_FILTERS = {
    0: "(NVL(DUREE_IMP_A_DATE, 0) = 1)",
    30: "(NVL(DUREE_IMP_A_DATE, 0) = 31)",
    90: "(NVL(DUREE_IMP_A_DATE, 0) = 91)",
    180: "(NVL(DUREE_IMP_A_DATE, 0) = 181)",
    360: "(NVL(DUREE_IMP_A_DATE, 0) = 361)",
}


def get_query_entrees_par(month_year: str, par_bucket: int) -> Tuple[str, dict]:
    """
    Retourne la requête Entrées PAR (DASH) et les binds Oracle.

    par_bucket: 0, 30, 90, 180 ou 360
    month_year: mois calendaire du snapshot, format MM/YYYY (ex. 04/2026)
    """
    if par_bucket not in PAR_FILTERS:
        raise ValueError("par_bucket doit être 0, 30, 90, 180 ou 360")
    where_par = PAR_FILTERS[par_bucket]
    sql = ENTREES_PAR_QUERY.replace("__PAR_BUCKET_WHERE__", where_par)
    return sql, {"month_year": month_year}
