"""
Service CR par Agence - données du compte de résultat par agence.
Requête DATA CR : solde (Crédit - Débit) par branche pour des parent GL donnés.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from database.oracle import get_oracle_connection

logger = logging.getLogger(__name__)


def get_cr_data_by_parent_gl(
    date_from: str,
    date_to: str,
    parent_gl_codes: List[str],
) -> List[Dict]:
    """
    Récupère les montants CR par agence pour une liste de parent GL.

    Logique alignée sur la requête de reporting financier :
    - Journal = union des écritures module DE (TRN_DT = VALUE_DT) et non-DE (TRN_DT natif)
    - Solde ouverture = cumul (C-D) jusqu'à la veille de date_from
    - Solde mois = cumul (C-D) entre date_from et date_to
    - Solde final = ouverture + mois
    Le champ `montant` retourné correspond au solde final de période par agence.

    Args:
        date_from: Date début (DD/MM/YYYY)
        date_to: Date fin (DD/MM/YYYY)
        parent_gl_codes: Liste des codes parent GL (ex: ['702120000000', '702130000000'])

    Returns:
        Liste de dicts avec AC_BRANCH, BRANCH_NAME, montant (somme par agence)
    """
    if not parent_gl_codes:
        return []

    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("ALTER SESSION SET CURRENT_SCHEMA = CFSFCUBS145")

        # Placeholders Oracle pour IN (:p0, :p1, ...)
        placeholders = ", ".join([f":p{i}" for i in range(len(parent_gl_codes))])
        params = {f"p{i}": str(c).strip() for i, c in enumerate(parent_gl_codes)}
        params["date_from"] = date_from
        params["date_to"] = date_to
        opening_date = (datetime.strptime(date_from, "%d/%m/%Y") - timedelta(days=1)).strftime("%d/%m/%Y")
        params["opening_date"] = opening_date

        query = f"""
        WITH Journal AS (
            SELECT
                a.AC_BRANCH,
                a.AC_NO,
                a.DRCR_IND,
                a.LCY_AMOUNT,
                a.VALUE_DT AS TRN_DT
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES a
            WHERE a.MODULE = 'DE'
            UNION ALL
            SELECT
                a.AC_BRANCH,
                a.AC_NO,
                a.DRCR_IND,
                a.LCY_AMOUNT,
                a.TRN_DT AS TRN_DT
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES a
            WHERE a.MODULE <> 'DE'
        ),
        base AS (
            SELECT
                j.AC_BRANCH,
                NVL(c.PARENT_GL, s.DR_GL) AS parent_gl,
                SUM(
                    DECODE(
                        j.DRCR_IND,
                        'C', CASE WHEN j.TRN_DT <= TO_DATE(:opening_date, 'DD/MM/YYYY') THEN j.LCY_AMOUNT ELSE 0 END,
                        'D', -CASE WHEN j.TRN_DT <= TO_DATE(:opening_date, 'DD/MM/YYYY') THEN j.LCY_AMOUNT ELSE 0 END,
                        0
                    )
                ) AS solde_ouverture,
                SUM(
                    DECODE(
                        j.DRCR_IND,
                        'C', CASE WHEN j.TRN_DT BETWEEN TO_DATE(:date_from, 'DD/MM/YYYY') AND TO_DATE(:date_to, 'DD/MM/YYYY') THEN j.LCY_AMOUNT ELSE 0 END,
                        'D', -CASE WHEN j.TRN_DT BETWEEN TO_DATE(:date_from, 'DD/MM/YYYY') AND TO_DATE(:date_to, 'DD/MM/YYYY') THEN j.LCY_AMOUNT ELSE 0 END,
                        0
                    )
                ) AS solde_mois
            FROM Journal j
            LEFT JOIN CFSFCUBS145.GLTM_GLMASTER c ON c.GL_CODE = j.AC_NO
            LEFT JOIN CFSFCUBS145.STTM_CUST_ACCOUNT s ON s.CUST_AC_NO = j.AC_NO
            WHERE j.TRN_DT <= TO_DATE(:date_to, 'DD/MM/YYYY')
              AND NVL(c.PARENT_GL, s.DR_GL) IN ({placeholders})
            GROUP BY j.AC_BRANCH, NVL(c.PARENT_GL, s.DR_GL)
        )
        SELECT
            base.AC_BRANCH,
            b.BRANCH_NAME,
            NVL(SUM(base.solde_ouverture), 0) AS SOLDE_OUVERTURE,
            NVL(SUM(base.solde_mois), 0) AS SOLDE_MOIS,
            NVL(SUM(base.solde_ouverture + base.solde_mois), 0) AS MONTANT
        FROM base
        JOIN CFSFCUBS145.STTM_BRANCH b ON b.BRANCH_CODE = base.AC_BRANCH
        GROUP BY base.AC_BRANCH, b.BRANCH_NAME
        """
        cursor.execute(query, params)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        cursor.close()

        return [
            dict(zip(columns, row))
            for row in rows
        ]
    except Exception as e:
        logger.exception("CR par Agence: erreur get_cr_data_by_parent_gl")
        raise
    finally:
        conn.close()
