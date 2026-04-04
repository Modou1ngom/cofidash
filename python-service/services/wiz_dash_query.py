# Western Union (WIZ) — tables DASH Cofina.
# La 1ʳᵉ requête porte sur les volumes paiement ; le nom de table suit le schéma DASH_PAIEMENT_* (comme OM / Ria).
# Si votre base n’a qu’une seule table, adaptez le FROM de sql_dash_paiement_wiz.

def sql_dash_paiement_wiz(inner_where: str) -> str:
    return f"""
SELECT
    CODE_AGENCE,
    LIBELLE_AGENCE,
    VOLUME_PAIEMENT_WIZ_M_1,
    VOLUME_PAIEMENT_WIZ_M,
    VARIATION_VOLUME,
    "VARIATION%",
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_PAIEMENT_WIZ
WHERE MIGRATION_DATETIME = (
    SELECT MAX(d.MIGRATION_DATETIME)
    FROM DASH_PAIEMENT_WIZ d
    WHERE {inner_where}
)
ORDER BY CODE_AGENCE, LIBELLE_AGENCE
"""


def sql_dash_envoi_wiz(inner_where: str) -> str:
    return f"""
SELECT
    CODE_AGENCE,
    LIBELLE_AGENCE,
    VOLUME_ENVOIE_WIZ_M_1,
    VOLUME_ENVOIE_WIZ_M,
    VARIATION_VOLUME,
    "VARIATION%",
    MIGRATION_DATE,
    MIGRATION_DATETIME,
    MIGRATION_DATE_MINUS1
FROM DASH_ENVOI_WIZ
WHERE MIGRATION_DATETIME = (
    SELECT MAX(d.MIGRATION_DATETIME)
    FROM DASH_ENVOI_WIZ d
    WHERE {inner_where}
)
ORDER BY CODE_AGENCE, LIBELLE_AGENCE
"""
