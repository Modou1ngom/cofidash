"""
Service CR par Agence - données du compte de résultat par agence.
Requête DATA CR : solde (Crédit - Débit) par branche pour des parent GL donnés.
"""
import logging
from typing import List, Dict, Optional
from database.oracle import get_oracle_connection

logger = logging.getLogger(__name__)


def get_cr_data_by_parent_gl(
    date_from: str,
    date_to: str,
    parent_gl_codes: List[str],
) -> List[Dict]:
    """
    Récupère les montants CR par agence pour une liste de codes GL (sous-rubrique).

    Logique : solde (Crédits - Débits) sur la période VALUE_DT, pour les comptes qui :
    - ont leur parent_gl (dans GLTM_GLMASTER) dans la liste, OU
    - ont leur gl_code (AC_NO) directement dans la liste (ex. Charges d'encadrement 702100000000).
    Résultat groupé par AC_BRANCH.

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

        # Placeholders pour la liste IN (Oracle)
        placeholders = ", ".join([f":p{i}" for i in range(len(parent_gl_codes))])
        params = {f"p{i}": str(c).strip() for i, c in enumerate(parent_gl_codes)}
        params["date_from"] = date_from
        params["date_to"] = date_to

        # Inclure les comptes dont parent_gl est dans la liste OU dont gl_code (AC_NO) est dans la liste
        query = f"""
        WITH period_balance AS (
            SELECT
                b.AC_NO,
                b.AC_BRANCH,
                SUM(DECODE(b.DRCR_IND, 'C', b.LCY_AMOUNT, 0)) - SUM(DECODE(b.DRCR_IND, 'D', b.LCY_AMOUNT, 0)) AS balance
            FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES b
            WHERE b.VALUE_DT BETWEEN TO_DATE(:date_from, 'DD/MM/YYYY') AND TO_DATE(:date_to, 'DD/MM/YYYY')
            GROUP BY b.AC_NO, b.AC_BRANCH
        )
        SELECT
            p.AC_BRANCH,
            b.BRANCH_NAME,
            NVL(SUM(p.balance), 0) AS montant
        FROM period_balance p
        LEFT JOIN CFSFCUBS145.GLTM_GLMASTER c ON c.gl_code = p.AC_NO
        JOIN CFSFCUBS145.STTM_BRANCH b ON b.BRANCH_CODE = p.AC_BRANCH
        WHERE (
            (c.gl_code IS NOT NULL AND (c.parent_gl IN ({placeholders}) OR c.gl_code IN ({placeholders})))
            OR (c.gl_code IS NULL AND p.AC_NO IN ({placeholders}))
        )
        GROUP BY p.AC_BRANCH, b.BRANCH_NAME
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
