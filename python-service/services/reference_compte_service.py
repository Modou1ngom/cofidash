"""
Service pour la référence compte 
"""
from typing import Optional, List, Dict
from database.oracle import get_oracle_connection_cofina


def get_gl_by_code(gl_code: str) -> Optional[Dict]:
    """
    Récupère un GL par son code 
    
    Args:
        gl_code: Code GL (ex: '702930000000')
    
    Returns:
        Dict avec GL_CODE_E et GL_DESC_E, ou None si non trouvé
    """
    if not gl_code or not str(gl_code).strip():
        return None
    
    conn = get_oracle_connection_cofina()
    try:
        cursor = conn.cursor()
        query = """
            SELECT GL_CODE_E, GL_DESC_E
            FROM CFSFCUBS145.GLVW_GLMASTER_E
            WHERE GL_CODE_E = :gl_code
        """
        cursor.execute(query, {"gl_code": str(gl_code).strip()})
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            code_val = row[0]
            desc_val = row[1]
            # Conversion explicite en string (Oracle peut renvoyer CLOB, Number, etc.)
            code_str = str(code_val).strip() if code_val is not None else ""
            desc_str = str(desc_val).strip() if desc_val is not None else ""
            return {
                "GL_CODE_E": code_str,
                "GL_DESC_E": desc_str,
                "numero_gl": code_str,
                "nom_gl": desc_str
            }
        return None
    finally:
        conn.close()


def search_gl(gl_code: Optional[str] = None, gl_desc: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """
    Recherche des GL par code ou libellé (LIKE).
    
    Args:
        gl_code: Code GL (recherche exacte ou début)
        gl_desc: Description GL (recherche partielle)
        limit: Nombre max de résultats
    
    Returns:
        Liste de dicts avec GL_CODE_E et GL_DESC_E
    """
    conn = get_oracle_connection_cofina()
    results = []
    try:
        cursor = conn.cursor()
        
        if gl_code and str(gl_code).strip():
            query = """
                SELECT GL_CODE_E, GL_DESC_E
                FROM DASH_CR_PAR_AGENCE
                WHERE GL_CODE_E = :gl_code
            """
            cursor.execute(query, {"gl_code": str(gl_code).strip()})
        elif gl_desc and str(gl_desc).strip():
            query = """
                SELECT GL_CODE_E, GL_DESC_E
                FROM DASH_CR_PAR_AGENCE
                WHERE UPPER(GL_DESC_E) LIKE UPPER(:gl_desc)
                FETCH FIRST 50 ROWS ONLY
            """
            cursor.execute(query, {"gl_desc": "%" + str(gl_desc).strip() + "%"})
        else:
            return []
        
        for row in cursor.fetchall():
            code_val = row[0]
            desc_val = row[1]
            code_str = str(code_val).strip() if code_val is not None else ""
            desc_str = str(desc_val).strip() if desc_val is not None else ""
            results.append({
                "GL_CODE_E": code_str,
                "GL_DESC_E": desc_str,
                "numero_gl": code_str,
                "nom_gl": desc_str
            })
        cursor.close()
    finally:
        conn.close()
    
    return results
