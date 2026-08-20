"""
Service pour la référence compte
"""
from typing import Optional, List, Dict
from database.oracle_pool import get_pool


def get_gl_by_code(gl_code: str) -> Optional[Dict]:
    """
    Vérifie qu'un PARENT_GL existe dans le dernier snapshot DASH_CR_PAR_AGENCE (Oracle Cofina).

    Aucun libellé n'est renvoyé : la table ne comporte pas de colonne exploitable (ex. GL_DESC_E).
    """
    if not gl_code or not str(gl_code).strip():
        return None

    code = str(gl_code).strip()
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            query = """
            SELECT PARENT_GL
            FROM DASH_CR_PAR_AGENCE
            WHERE TRIM(TO_CHAR(PARENT_GL)) = TRIM(TO_CHAR(:gl_code))
              AND MIGRATION_DATETIME = (SELECT MAX(MIGRATION_DATETIME) FROM DASH_CR_PAR_AGENCE)
            FETCH FIRST 1 ROW ONLY
        """
            cursor.execute(query, {"gl_code": code})
            row = cursor.fetchone()
            if row:
                code_val = row[0]
                code_str = str(code_val).strip() if code_val is not None else ""
                return {
                    "GL_CODE_E": code_str,
                    "GL_DESC_E": "",
                    "numero_gl": code_str,
                    "nom_gl": "",
                }
            return None
        finally:
            cursor.close()


def search_gl(gl_code: Optional[str] = None, gl_desc: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """
    Recherche par numéro PARENT_GL uniquement (dernier snapshot).
    La recherche par libellé n'est pas supportée (pas de colonne libellé dans DASH_CR_PAR_AGENCE).
    """
    pool = get_pool()
    results: List[Dict] = []
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        try:
            if gl_desc and str(gl_desc).strip():
                return []

            if gl_code and str(gl_code).strip():
                query = """
                SELECT PARENT_GL
                FROM DASH_CR_PAR_AGENCE
                WHERE TRIM(TO_CHAR(PARENT_GL)) = TRIM(TO_CHAR(:gl_code))
                  AND MIGRATION_DATETIME = (SELECT MAX(MIGRATION_DATETIME) FROM DASH_CR_PAR_AGENCE)
                FETCH FIRST 1 ROW ONLY
            """
                cursor.execute(query, {"gl_code": str(gl_code).strip()})
            else:
                return []

            for row in cursor.fetchall():
                code_val = row[0]
                code_str = str(code_val).strip() if code_val is not None else ""
                results.append({
                    "GL_CODE_E": code_str,
                    "GL_DESC_E": "",
                    "numero_gl": code_str,
                    "nom_gl": "",
                })
        finally:
            cursor.close()

    return results
