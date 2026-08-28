# Volumes de transferts d'argent — Flexcube CFSFCUBS145 (journaux ACVW_ALL_AC_ENTRIES).
# Debit (D) = envoi, crédit (C) = paiement, comme l'ancienne requête journal.
# On lit les GL d'attente / transit (pas les comptes banque ni les commissions).
# Dates : début inclusif, fin exclusive (YYYY-MM-DD).

# Filtres GLTM_GLMASTER : comptes d'attente / transit par opérateur.
SERVICE_VOLUME_GL_WHERE = {
    "om": """
        (UPPER(GL_DESC) LIKE '%ORANGE MONEY%' OR UPPER(GL_DESC) LIKE '%ORANGE USSD%')
        AND UPPER(GL_DESC) NOT LIKE '%BANQUE%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND (
            GL_CODE LIKE '102%'
            OR GL_CODE LIKE '372%'
            OR GL_CODE LIKE '3792%'
        )
    """,
    "wave": """
        UPPER(GL_DESC) LIKE '%WAVE%'
        AND UPPER(GL_DESC) NOT LIKE '%BANQUE%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND (
            GL_CODE LIKE '102%'
            OR GL_CODE LIKE '372%'
            OR GL_CODE LIKE '3791%'
            OR GL_CODE LIKE '3792%'
        )
    """,
    "ria": """
        UPPER(GL_DESC) LIKE '%RIA%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND GL_CODE LIKE '372%'
    """,
    "wu": """
        UPPER(GL_DESC) LIKE '%DATTENT W%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND GL_CODE LIKE '37112%'
    """,
    "moneygram": """
        UPPER(GL_DESC) LIKE '%MONEY G%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND GL_CODE LIKE '37112%'
    """,
    "wizzal": """
        (UPPER(GL_DESC) LIKE '%WIZZAL%' OR UPPER(GL_DESC) LIKE '%WIZAL%')
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND (
            GL_CODE LIKE '372%'
            OR GL_CODE LIKE '3792%'
        )
    """,
    "free_money": """
        UPPER(GL_DESC) LIKE '%FREE MONEY%'
        AND UPPER(GL_DESC) NOT LIKE '%BANQUE%'
        AND UPPER(GL_DESC) NOT LIKE '%COMMISSION%'
        AND UPPER(GL_DESC) NOT LIKE '%ARRONDI%'
        AND (
            GL_CODE LIKE '37112%'
            OR GL_CODE LIKE '372%'
        )
    """,
}

SERVICE_COMMISSION_GL_WHERE = {
    "om": """
        UPPER(GL_DESC) LIKE '%ORANGE MONEY%'
        AND GL_CODE LIKE '70292%'
    """,
    "wave": """
        UPPER(GL_DESC) LIKE '%WAVE%'
        AND GL_CODE LIKE '70292%'
    """,
    "ria": """
        UPPER(GL_DESC) LIKE '%RIA%'
        AND (GL_CODE LIKE '70292%' OR GL_CODE LIKE '729%')
    """,
    "wu": """
        UPPER(GL_DESC) LIKE '%COMMISSION WU%'
        AND (GL_CODE LIKE '70292%' OR GL_CODE LIKE '729%')
    """,
    "moneygram": """
        UPPER(GL_DESC) LIKE '%MONEYGRAM%'
        AND (GL_CODE LIKE '70292%' OR GL_CODE LIKE '729%')
    """,
    "wizzal": """
        (UPPER(GL_DESC) LIKE '%WIZZAL%' OR UPPER(GL_DESC) LIKE '%WIZAL%' OR UPPER(GL_DESC) LIKE '%COMMIS WIZZAL%')
        AND GL_CODE LIKE '70292%'
    """,
    "free_money": """
        UPPER(GL_DESC) LIKE '%FREE MONEY%'
        AND (GL_CODE LIKE '70292%' OR GL_CODE LIKE '729%')
    """,
}


def sql_transfers_flexcube_month(volume_gl_where: str, commission_gl_where: str) -> str:
    """Agrégat d'un seul mois calendaire (snapshot SQLite)."""
    return f"""
WITH VOL_GLS AS (
    SELECT GL_CODE
    FROM CFSFCUBS145.GLTM_GLMASTER
    WHERE {volume_gl_where}
),
COM_GLS AS (
    SELECT GL_CODE
    FROM CFSFCUBS145.GLTM_GLMASTER
    WHERE {commission_gl_where}
),
JRN AS (
    SELECT
        a.AC_BRANCH,
        a.DRCR_IND,
        a.LCY_AMOUNT,
        CASE WHEN v.GL_CODE IS NOT NULL THEN 1 ELSE 0 END AS IS_VOL,
        CASE WHEN c.GL_CODE IS NOT NULL THEN 1 ELSE 0 END AS IS_COM
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES a
    LEFT JOIN VOL_GLS v ON v.GL_CODE = a.AC_NO
    LEFT JOIN COM_GLS c ON c.GL_CODE = a.AC_NO
    WHERE a.TRN_DT >= TO_DATE(:date_debut, 'YYYY-MM-DD')
      AND a.TRN_DT <  TO_DATE(:date_fin_exclusive, 'YYYY-MM-DD')
      AND (v.GL_CODE IS NOT NULL OR c.GL_CODE IS NOT NULL)
)
SELECT
    J.AC_BRANCH AS CODE_AGENCE,
    NVL(B.BRANCH_NAME, J.AC_BRANCH) AS LIBELLE_AGENCE,
    SUM(CASE WHEN J.IS_VOL = 1 AND J.DRCR_IND IN ('D', 'C') THEN J.LCY_AMOUNT ELSE 0 END) AS VOLUME,
    SUM(CASE WHEN J.IS_COM = 1 AND J.DRCR_IND = 'C' THEN J.LCY_AMOUNT ELSE 0 END) AS COMMISSION
FROM JRN J
LEFT JOIN CFSFCUBS145.STTM_BRANCH B ON B.BRANCH_CODE = J.AC_BRANCH
GROUP BY J.AC_BRANCH, B.BRANCH_NAME
ORDER BY J.AC_BRANCH
"""


def sql_transfers_flexcube(volume_gl_where: str, commission_gl_where: str) -> str:
    return f"""
WITH VOL_GLS AS (
    SELECT GL_CODE
    FROM CFSFCUBS145.GLTM_GLMASTER
    WHERE {volume_gl_where}
),
COM_GLS AS (
    SELECT GL_CODE
    FROM CFSFCUBS145.GLTM_GLMASTER
    WHERE {commission_gl_where}
),
JRN AS (
    SELECT
        a.AC_BRANCH,
        a.DRCR_IND,
        a.LCY_AMOUNT,
        a.TRN_DT,
        CASE WHEN v.GL_CODE IS NOT NULL THEN 1 ELSE 0 END AS IS_VOL,
        CASE WHEN c.GL_CODE IS NOT NULL THEN 1 ELSE 0 END AS IS_COM
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES a
    LEFT JOIN VOL_GLS v ON v.GL_CODE = a.AC_NO
    LEFT JOIN COM_GLS c ON c.GL_CODE = a.AC_NO
    WHERE a.TRN_DT >= TO_DATE(:date_m1_debut, 'YYYY-MM-DD')
      AND a.TRN_DT <  TO_DATE(:date_m_fin_exclusive, 'YYYY-MM-DD')
      AND (v.GL_CODE IS NOT NULL OR c.GL_CODE IS NOT NULL)
),
PER_M AS (
    SELECT
        AC_BRANCH,
        SUM(CASE WHEN IS_VOL = 1 AND DRCR_IND = 'D' THEN LCY_AMOUNT ELSE 0 END) AS ENVOI_M,
        SUM(CASE WHEN IS_VOL = 1 AND DRCR_IND = 'C' THEN LCY_AMOUNT ELSE 0 END) AS PAIEMENT_M,
        SUM(CASE WHEN IS_COM = 1 AND DRCR_IND = 'C' THEN LCY_AMOUNT ELSE 0 END) AS COMM_M
    FROM JRN
    WHERE TRN_DT >= TO_DATE(:date_m_debut, 'YYYY-MM-DD')
      AND TRN_DT <  TO_DATE(:date_m_fin_exclusive, 'YYYY-MM-DD')
    GROUP BY AC_BRANCH
),
PER_M1 AS (
    SELECT
        AC_BRANCH,
        SUM(CASE WHEN IS_VOL = 1 AND DRCR_IND = 'D' THEN LCY_AMOUNT ELSE 0 END) AS ENVOI_M1,
        SUM(CASE WHEN IS_VOL = 1 AND DRCR_IND = 'C' THEN LCY_AMOUNT ELSE 0 END) AS PAIEMENT_M1
    FROM JRN
    WHERE TRN_DT >= TO_DATE(:date_m1_debut, 'YYYY-MM-DD')
      AND TRN_DT <  TO_DATE(:date_m_debut, 'YYYY-MM-DD')
    GROUP BY AC_BRANCH
),
ALL_AGENCIES AS (
    SELECT AC_BRANCH FROM PER_M
    UNION
    SELECT AC_BRANCH FROM PER_M1
)
SELECT
    AA.AC_BRANCH AS CODE_AGENCE,
    NVL(B.BRANCH_NAME, AA.AC_BRANCH) AS LIBELLE_AGENCE,
    NVL(M.ENVOI_M, 0) + NVL(M.PAIEMENT_M, 0) AS VOLUME_M,
    NVL(M1.ENVOI_M1, 0) + NVL(M1.PAIEMENT_M1, 0) AS VOLUME_M_1,
    (NVL(M.ENVOI_M, 0) + NVL(M.PAIEMENT_M, 0))
      - (NVL(M1.ENVOI_M1, 0) + NVL(M1.PAIEMENT_M1, 0)) AS VARIATION_VOLUME,
    ROUND(
        (
            (
                (NVL(M.ENVOI_M, 0) + NVL(M.PAIEMENT_M, 0))
                - (NVL(M1.ENVOI_M1, 0) + NVL(M1.PAIEMENT_M1, 0))
            )
            / NULLIF(NVL(M1.ENVOI_M1, 0) + NVL(M1.PAIEMENT_M1, 0), 0)
        ) * 100,
        2
    ) AS VARIATION_PCT,
    NVL(M.COMM_M, 0) AS COMMISSION
FROM ALL_AGENCIES AA
LEFT JOIN PER_M M ON M.AC_BRANCH = AA.AC_BRANCH
LEFT JOIN PER_M1 M1 ON M1.AC_BRANCH = AA.AC_BRANCH
LEFT JOIN CFSFCUBS145.STTM_BRANCH B ON B.BRANCH_CODE = AA.AC_BRANCH
ORDER BY AA.AC_BRANCH
"""
