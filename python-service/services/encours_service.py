"""
Service pour la gestion des données Encours
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import calendar
from services.utils import get_territory_from_agency, get_territory_from_branch_code, get_territory_key, get_all_territories

logger = logging.getLogger(__name__)


def _dash_float(row: dict, *names: str) -> float:
    """Lit un nombre dans une ligne Oracle (clés en majuscules variables)."""
    upper_names = {n.upper() for n in names if n}
    for k, v in row.items():
        if k is not None and str(k).upper() in upper_names:
            try:
                return float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _normalize_dash_encours_epargne_row_pep(row: dict) -> Dict[str, Any]:
    """
    Une ligne DASH → structure « epargne-pep-simple » : simple + projet + dette agrégée.
    C’est le format principal (l’UI ne requête que ce type pour remplir tous les onglets).
    """
    m_ep = _dash_float(row, "M_ENCOURS_EPARGNE_SIMPLE")
    m1_ep = _dash_float(row, "M1_ENCOURS_EPARGNE_SIMPLE")
    m_proj = _dash_float(row, "M_ENCOURS_CPT_EPARGNE_PROJET")
    m1_proj = _dash_float(row, "M1_ENCOURS_CPT_EPARGNE_PROJET")
    tot_m = _dash_float(row, "ENCOURS_TOTAL_M")
    tot_m1 = _dash_float(row, "ENCOURS_TOTAL_M_1", "ENCOURS_TOTAL_M1")

    d_simple_m = _dash_float(row, "DETES_RATT_EPARGNE_SIMPLE_M", "DETTES_RATT_EPARGNE_SIMPLE_M")
    d_proj_m = _dash_float(row, "DETES_RATT_EPARGNE_SPROJET_M", "DETTES_RATT_EPARGNE_SPROJET_M")

    code = row.get("BRANCH_CODE") or row.get("branch_code")
    name = (row.get("BRANCH_NAME") or row.get("branch_name") or "").strip()

    return {
        "BRANCH_CODE": code,
        "BRANCH_NAME": name,
        "ENCOURS_TOTAL_M": tot_m,
        "ENCOURS_TOTAL_M_1": tot_m1,
        "M_ENCOURS_COMPTE_EPARGNE": m_ep,
        "M1_ENCOURS_COMPTE_EPARGNE": m1_ep,
        "M_ENCOURS_COMPTE_EPARGNE_PROJET": m_proj,
        "M1_ENCOURS_COMPTE_EPARGNE_PROJET": m1_proj,
        "M_ENCOURS_COMPTE_COURANT": 0.0,
        "M1_ENCOURS_COMPTE_COURANT": 0.0,
        "M_ENCOURS_DAT": 0.0,
        "M1_ENCOURS_DAT": 0.0,
        "M_ENCOURS_DEPOT_GARANTIE": 0.0,
        "M1_ENCOURS_DEPOT_GARANTIE": 0.0,
        "DETTE_RATTACHEE": d_simple_m + d_proj_m,
        "detteRattachee": d_simple_m + d_proj_m,
    }


def _normalize_dash_encours_epargne_row(row: dict, encours_type: str) -> dict:
    """À partir d’une ligne DASH : vue PEP complète, ou détente simple/projet seules si demandé."""
    out = dict(_normalize_dash_encours_epargne_row_pep(row))
    d_simple_m = _dash_float(row, "DETES_RATT_EPARGNE_SIMPLE_M", "DETTES_RATT_EPARGNE_SIMPLE_M")
    d_proj_m = _dash_float(row, "DETES_RATT_EPARGNE_SPROJET_M", "DETTES_RATT_EPARGNE_SPROJET_M")

    if encours_type == "epargne-simple":
        out["DETTE_RATTACHEE"] = d_simple_m
        out["detteRattachee"] = d_simple_m
    elif encours_type == "epargne-projet":
        out["DETTE_RATTACHEE"] = d_proj_m
        out["detteRattachee"] = d_proj_m
    # epargne-pep-simple : garder dette = simple + projet (déjà dans out)

    return out


def get_encours_data(period: str = "month", zone: Optional[str] = None, 
                     month: Optional[int] = None, year: Optional[int] = None, 
                     date: Optional[str] = None, encours_type: str = "compte-courant"):
    """
    Récupère les données Encours depuis Oracle
    
    Args:
        period: Période d'analyse ("month", "year", "week")
        zone: Zone géographique (optionnel)
        month: Mois à analyser (1-12)
        year: Année à analyser
        date: Date pour la période semaine (format YYYY-MM-DD)
        encours_type: Type d'encours ("compte-courant", "epargne-simple", "epargne-pep-simple", "epargne-projet").
            Les trois types épargne lisent uniquement ``DASH_ENCOURS_EPARGNE`` (plus de requête analytique sur les journaux).
    
    Returns:
        Dictionnaire avec les données Encours organisées par zones
    """
    logger.info(f"🔍 get_encours_data appelé avec period={period}, zone={zone}, month={month}, year={year}, date={date}, type={encours_type}")
    
    # Utiliser le mois et l'année actuels si non fournis
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calculer les dates M et M-1
    if period == "month":
        # Date de fin du mois M
        m_end = datetime(year, month, calendar.monthrange(year, month)[1])
        # Date de fin du mois M-1
        if month == 1:
            m1_end = datetime(year - 1, 12, calendar.monthrange(year - 1, 12)[1])
        else:
            m1_end = datetime(year, month - 1, calendar.monthrange(year, month - 1)[1])
    elif period == "year":
        # Date de fin de l'année M
        m_end = datetime(year, 12, 31)
        # Date de fin de l'année M-1
        m1_end = datetime(year - 1, 12, 31)
    elif period == "week":
        # Pour la semaine, utiliser la date fournie ou aujourd'hui
        if date:
            try:
                reference_date = datetime.strptime(date, "%Y-%m-%d")
            except (ValueError, TypeError):
                reference_date = datetime.now()
        else:
            reference_date = datetime.now()
        
        # Trouver le dimanche de la semaine (fin de semaine)
        from datetime import timedelta
        days_since_monday = reference_date.weekday()
        sunday = reference_date + timedelta(days=(6 - days_since_monday))
        m_end = sunday
        
        # Semaine précédente
        m1_end = sunday - timedelta(days=7)
    else:
        # Par défaut, utiliser le mois actuel
        now = datetime.now()
        m_end = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
        if now.month == 1:
            m1_end = datetime(now.year - 1, 12, calendar.monthrange(now.year - 1, 12)[1])
        else:
            m1_end = datetime(now.year, now.month - 1, calendar.monthrange(now.year, now.month - 1)[1])
    
    # Calculer les dates de début du mois M et M-1 pour les dettes rattachées
    if period == "month":
        m_start = datetime(year, month, 1)
        if month == 1:
            m1_start = datetime(year - 1, 12, 1)
        else:
            m1_start = datetime(year, month - 1, 1)
    elif period == "year":
        m_start = datetime(year, 1, 1)
        m1_start = datetime(year - 1, 1, 1)
    elif period == "week":
        # Pour la semaine, utiliser la date fournie ou aujourd'hui
        if date:
            try:
                reference_date = datetime.strptime(date, "%Y-%m-%d")
            except (ValueError, TypeError):
                reference_date = datetime.now()
        else:
            reference_date = datetime.now()
        
        # Trouver le lundi de la semaine (début de semaine)
        from datetime import timedelta
        days_since_monday = reference_date.weekday()
        monday = reference_date - timedelta(days=days_since_monday)
        m_start = monday
        
        # Semaine précédente
        m1_start = monday - timedelta(days=7)
        m1_end = monday - timedelta(days=1)
    else:
        # Par défaut, utiliser le mois actuel
        now = datetime.now()
        m_start = datetime(now.year, now.month, 1)
        if now.month == 1:
            m1_start = datetime(now.year - 1, 12, 1)
        else:
            m1_start = datetime(now.year, now.month - 1, 1)
    
    # Formater les dates pour Oracle (DD/MM/YYYY)
    m_end_str = m_end.strftime("%d/%m/%Y")
    m1_end_str = m1_end.strftime("%d/%m/%Y")
    m_start_str = m_start.strftime("%d/%m/%Y")
    m1_start_str = m1_start.strftime("%d/%m/%Y")
    
    logger.info(f"📅 Dates calculées: M fin={m_end_str}, M-1 fin={m1_end_str}")
    logger.info(f"📅 Dates dettes rattachées: M début={m_start_str}, M fin={m_end_str}, M-1 début={m1_start_str}, M-1 fin={m1_end_str}")

    # Snapshot DASH_ENCOURS_EPARGNE (MM/YYYY) : mois sélectionné, décembre pour l’année, mois de m_end pour la semaine
    if period == "month":
        dash_epargne_month_year = f"{month:02d}/{year}"
    elif period == "year":
        dash_epargne_month_year = f"12/{year}"
    else:
        dash_epargne_month_year = f"{m_end.month:02d}/{m_end.year}"

    # Utiliser le pool de connexions et le cache
    from database.oracle_pool import get_pool
    from services.cache_service import get_cache, set_cache, generate_cache_key
    
    # Générer une clé de cache basée sur les paramètres
    cache_key = f"encours:{encours_type}:{generate_cache_key(period, zone, month, year, date)}"
    
    # Vérifier le cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.info("✅ Données Encours récupérées depuis le cache")
        return cached_result
    
    pool = get_pool()
    with pool.get_connection_context() as conn:
        cursor = conn.cursor()
        
        # Optimisations Oracle
        cursor.arraysize = 1000
        cursor.prefetchrows = 1000
        
        try:
            logger.info("🔍 Exécution de la requête Encours...")

            use_dash_epargne = encours_type in ("epargne-simple", "epargne-pep-simple", "epargne-projet")
            if use_dash_epargne:
                from services.encours_epargne_dash_query import ENCOURS_EPARGNE_DASH_QUERY

                logger.info(
                    "📊 Encours épargne via DASH_ENCOURS_EPARGNE uniquement, month_year=%s (period=%s)",
                    dash_epargne_month_year,
                    period,
                )
                cursor.execute(ENCOURS_EPARGNE_DASH_QUERY, {"month_year": dash_epargne_month_year})
                cols = [desc[0] for desc in cursor.description]
                raw_rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
                data = [_normalize_dash_encours_epargne_row(r, encours_type) for r in raw_rows]
            elif encours_type == "compte-courant":
                query = f"""
WITH JOURNAL AS (
    SELECT
        AC_ENTRY_SR_NO,
        AC_NO,
        DRCR_IND,
        LCY_AMOUNT,
        CASE 
            WHEN MODULE = 'DE' THEN VALUE_DT 
            ELSE TRN_DT 
        END AS TRN_DT
    FROM CFSFCUBS145.ACVW_ALL_AC_ENTRIES
),
 
COMPTE AS (
    SELECT 
        cpt.BRANCH_CODE,
        cpt.CUST_AC_NO,
        cpt.AC_DESC,
        cs.ACCOUNT_CLASS,
        cs.DESCRIPTION,
        cs.ACCOUNT_CODE
    FROM CFSFCUBS145.STTM_CUST_ACCOUNT cpt
    JOIN CFSFCUBS145.STTM_ACCOUNT_CLASS cs 
        ON cpt.ACCOUNT_CLASS = cs.ACCOUNT_CLASS
),
 
BRANCH AS (
    SELECT  
        BRANCH_CODE,
        BRANCH_NAME
    FROM CFSFCUBS145.STTM_BRANCH
),
 
-- Compte Courant
CPT_COURANT AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '251'
    GROUP BY y.BRANCH_CODE
),

-- Compte Épargne Projet
EPARGNE_PROJET AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '253'
      AND UPPER(y.DESCRIPTION) LIKE '%PROJET%'
    GROUP BY y.BRANCH_CODE
),

-- Compte Épargne (autres)
CPT_EPARGNE AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '253'
      AND UPPER(y.DESCRIPTION) NOT LIKE '%PROJET%'
    GROUP BY y.BRANCH_CODE
),

-- DAT
DAT AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '252'
    GROUP BY y.BRANCH_CODE
),

-- Dépôt de Garantie
DEPOT_GARANTIE AS (
    SELECT 
        y.BRANCH_CODE,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M,
        SUM(CASE WHEN a.DRCR_IND = 'C' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END)
      - SUM(CASE WHEN a.DRCR_IND = 'D' AND a.TRN_DT <= TO_DATE('{m1_end_str}','DD/MM/YYYY') THEN NVL(a.LCY_AMOUNT,0) ELSE 0 END) AS M_1
    FROM JOURNAL a
    JOIN COMPTE y ON a.AC_NO = y.CUST_AC_NO
    WHERE y.ACCOUNT_CODE = '254'
    GROUP BY y.BRANCH_CODE
),

-- Somme des encours par agence (sans ORDER BY dans le CTE)
depot AS (
    SELECT
        A.BRANCH_CODE,
        A.BRANCH_NAME,
        NVL(c.M, 0) AS M_ENCOURS_COMPTE_COURANT,
        NVL(e.M, 0) AS M_ENCOURS_COMPTE_EPARGNE,
        NVL(p.M, 0) AS M_ENCOURS_COMPTE_EPARGNE_PROJET,
        NVL(d.M, 0) AS M_ENCOURS_DAT,
        NVL(g.M, 0) AS M_ENCOURS_DEPOT_GARANTIE,
        NVL(c.M_1, 0) AS M1_ENCOURS_COMPTE_COURANT,
        NVL(e.M_1, 0) AS M1_ENCOURS_COMPTE_EPARGNE,
        NVL(p.M_1, 0) AS M1_ENCOURS_COMPTE_EPARGNE_PROJET,
        NVL(d.M_1, 0) AS M1_ENCOURS_DAT,
        NVL(g.M_1, 0) AS M1_ENCOURS_DEPOT_GARANTIE
    FROM BRANCH A
    LEFT JOIN CPT_COURANT c ON A.BRANCH_CODE = c.BRANCH_CODE
    LEFT JOIN CPT_EPARGNE e ON A.BRANCH_CODE = e.BRANCH_CODE
    LEFT JOIN EPARGNE_PROJET p ON A.BRANCH_CODE = p.BRANCH_CODE
    LEFT JOIN DAT d ON A.BRANCH_CODE = d.BRANCH_CODE
    LEFT JOIN DEPOT_GARANTIE g ON A.BRANCH_CODE = g.BRANCH_CODE
),

DEBLOCAGE AS (
    -- On convertit SCHEDULE_LINKAGE en date si c'est stocké sous forme texte 'DD/MM/YYYY'
    SELECT
        ACCOUNT_NUMBER,
        COALESCE(DTYPE, 'VIDE') AS DTYPE,
        MAX(SCHEDULE_LINKAGE) AS SCHEDULE_LINKAGE
    FROM CFSFCUBS145.CLTB_DISBR_SCHEDULES
    WHERE (DTYPE <> 'X' OR DTYPE IS NULL)
    GROUP BY ACCOUNT_NUMBER, COALESCE(DTYPE, 'VIDE')
),

ENCOURS_M AS (
    SELECT 
        c.ACCOUNT_NUMBER AS NO_PRET,
        c.BRANCH_CODE,
        SUM(NVL(z.AMOUNT_DUE,0)) AS MT_CAPITAL_TA,
        SUM(NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) AS ENCOURS_TOTAL_M,
        SUM(CASE WHEN c.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                 THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_SAIN,
        SUM(CASE WHEN c.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                 THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_IMPAYE
    FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
    LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
           ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
    LEFT JOIN DEBLOCAGE d 
           ON d.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
    WHERE 
        c.ACCOUNT_STATUS NOT IN ('L', 'V')
        AND z.COMPONENT_NAME = 'PRINCIPAL'
        AND (d.SCHEDULE_LINKAGE IS NULL OR d.SCHEDULE_LINKAGE <= TO_DATE('{m_end_str}','DD/MM/YYYY'))
    GROUP BY c.ACCOUNT_NUMBER, c.BRANCH_CODE
),

ENCOURS_M_1 AS (
    SELECT 
        c.ACCOUNT_NUMBER AS NO_PRET,
        c.BRANCH_CODE,
        SUM(NVL(z.AMOUNT_DUE,0)) AS MT_CAPITAL_TA,
        SUM(NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) AS ENCOURS_TOTAL_M_1,
        SUM(CASE WHEN c.USER_DEFINED_STATUS IN ('NORM', 'IMPA') 
                 THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_SAIN,
        SUM(CASE WHEN c.USER_DEFINED_STATUS NOT IN ('NORM', 'IMPA') 
                 THEN (NVL(z.AMOUNT_DUE,0) - NVL(z.AMOUNT_SETTLED,0)) ELSE 0 END) AS ENCOURS_IMPAYE
    FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
    LEFT JOIN CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES z 
           ON z.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
    LEFT JOIN DEBLOCAGE d 
           ON d.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
    WHERE 
        c.ACCOUNT_STATUS NOT IN ('L', 'V')
        AND z.COMPONENT_NAME = 'PRINCIPAL'
        AND (d.SCHEDULE_LINKAGE IS NULL OR d.SCHEDULE_LINKAGE <= TO_DATE('{m1_end_str}','DD/MM/YYYY'))
    GROUP BY c.ACCOUNT_NUMBER, c.BRANCH_CODE
),

encours_credit AS (
    SELECT
      COALESCE(e1.BRANCH_CODE, e.BRANCH_CODE) AS BRANCH_CODE,
      br.BRANCH_NAME,
      SUM(NVL(e.ENCOURS_TOTAL_M,0)) AS ENCOURS_TOTAL_M,
      SUM(NVL(e1.ENCOURS_TOTAL_M_1,0)) AS ENCOURS_TOTAL_M_1,
      SUM(NVL(e.ENCOURS_TOTAL_M,0)) - SUM(NVL(e1.ENCOURS_TOTAL_M_1,0)) AS VARIATION_ENCOURS_CREDIT,
      SUM(NVL(e.ENCOURS_SAIN,0)) AS ENCOURS_SAIN_M,
      SUM(NVL(e.ENCOURS_IMPAYE,0)) AS ENCOURS_IMPAYE_M
    FROM  ENCOURS_M e
    LEFT JOIN ENCOURS_M_1 e1 ON e1.NO_PRET = e.NO_PRET
    LEFT JOIN BRANCH br ON br.BRANCH_CODE = COALESCE(e1.BRANCH_CODE, e.BRANCH_CODE)
    GROUP BY COALESCE(e1.BRANCH_CODE, e.BRANCH_CODE), br.BRANCH_NAME
)

SELECT 
    o.BRANCH_CODE,
    o.BRANCH_NAME,
    NVL(v.ENCOURS_TOTAL_M,0)         AS ENCOURS_TOTAL_M,
    NVL(v.ENCOURS_TOTAL_M_1,0)       AS ENCOURS_TOTAL_M_1,
    o.M1_ENCOURS_COMPTE_COURANT,
    o.M_ENCOURS_COMPTE_COURANT
FROM depot o
LEFT JOIN encours_credit v ON o.BRANCH_CODE = v.BRANCH_CODE
ORDER BY o.BRANCH_CODE, o.BRANCH_NAME
"""
            else:
                # Pour les autres types, retourner une structure vide pour l'instant
                query = "SELECT NULL AS BRANCH_CODE, NULL AS BRANCH_NAME, 0 AS M1_ENCOURS_COMPTE_COURANT, 0 AS M_ENCOURS_COMPTE_COURANT FROM DUAL WHERE 1=0"

            if not use_dash_epargne:
                logger.info(f"⏱️  Exécution de la requête Encours (timeout: 5 minutes)")
                cursor.execute(query)

                # Récupérer les résultats
                columns = [desc[0] for desc in cursor.description]
                data = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    data.append(row_dict)
            
            logger.info(f"📊 {len(data)} lignes récupérées depuis Oracle")
            if data and encours_type in ["epargne-pep-simple", "epargne-simple", "epargne-projet"]:
                logger.info(f"🔍 Colonnes disponibles: {list(data[0].keys())}")
                if 'DETTE_RATTACHEE' in data[0]:
                    logger.info(f"🔍 Première ligne - DETTE_RATTACHEE: {data[0].get('DETTE_RATTACHEE')}")
                # Log quelques exemples de dettes rattachées
                dettes_samples = [row.get('DETTE_RATTACHEE', 0) for row in data[:5] if row.get('DETTE_RATTACHEE', 0) != 0]
                if dettes_samples:
                    logger.info(f"🔍 Exemples de dettes rattachées trouvées: {dettes_samples}")
                else:
                    logger.warning(f"⚠️ Aucune dette rattachée non-nulle trouvée dans les {min(5, len(data))} premières lignes")
            
            if len(data) == 0:
                logger.warning("⚠️ Aucune donnée Encours trouvée")
                return {
                    "hierarchicalData": {
                        "TERRITOIRE": {},
                        "POINT SERVICES": {}
                    }
                }
            
            # Organiser les données par territoire et point de service
            agencies_by_territory = {
                'territoire_dakar_ville': [],
                'territoire_dakar_banlieue': [],
                'territoire_province_centre_sud': [],
                'territoire_province_nord': []
            }
            
            grand_compte = None
            
            for row in data:
                branch_code = row.get('BRANCH_CODE') or row.get('branch_code')
                agency_name = row.get('BRANCH_NAME') or row.get('branch_name') or ''
                
                # Créer l'objet agence selon le type d'encours
                if encours_type == "epargne-simple":
                    agency = {
                        'BRANCH_CODE': branch_code,
                        'BRANCH_NAME': agency_name,
                        'name': agency_name,
                        'M1_ENCOURS_COMPTE_EPARGNE': float(row.get('M1_ENCOURS_COMPTE_EPARGNE') or 0),
                        'M_ENCOURS_COMPTE_EPARGNE': float(row.get('M_ENCOURS_COMPTE_EPARGNE') or 0),
                        'ENCOURS_TOTAL_M': float(row.get('ENCOURS_TOTAL_M') or 0),
                        'ENCOURS_TOTAL_M_1': float(row.get('ENCOURS_TOTAL_M_1') or 0),
                        'DETTE_RATTACHEE': float(row.get('DETTE_RATTACHEE') or 0),
                        'detteRattachee': float(row.get('DETTE_RATTACHEE') or 0)
                    }
                elif encours_type == "epargne-pep-simple":
                    agency = {
                        'BRANCH_CODE': branch_code,
                        'BRANCH_NAME': agency_name,
                        'name': agency_name,
                        'M_ENCOURS_COMPTE_COURANT': float(row.get('M_ENCOURS_COMPTE_COURANT') or 0),
                        'M_ENCOURS_COMPTE_EPARGNE': float(row.get('M_ENCOURS_COMPTE_EPARGNE') or 0),
                        'M_ENCOURS_COMPTE_EPARGNE_PROJET': float(row.get('M_ENCOURS_COMPTE_EPARGNE_PROJET') or 0),
                        'M_ENCOURS_DAT': float(row.get('M_ENCOURS_DAT') or 0),
                        'M_ENCOURS_DEPOT_GARANTIE': float(row.get('M_ENCOURS_DEPOT_GARANTIE') or 0),
                        'M1_ENCOURS_COMPTE_COURANT': float(row.get('M1_ENCOURS_COMPTE_COURANT') or 0),
                        'M1_ENCOURS_COMPTE_EPARGNE': float(row.get('M1_ENCOURS_COMPTE_EPARGNE') or 0),
                        'M1_ENCOURS_COMPTE_EPARGNE_PROJET': float(row.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET') or 0),
                        'M1_ENCOURS_DAT': float(row.get('M1_ENCOURS_DAT') or 0),
                        'M1_ENCOURS_DEPOT_GARANTIE': float(row.get('M1_ENCOURS_DEPOT_GARANTIE') or 0),
                        'ENCOURS_TOTAL_M': float(row.get('ENCOURS_TOTAL_M') or 0),
                        'ENCOURS_TOTAL_M_1': float(row.get('ENCOURS_TOTAL_M_1') or 0),
                        'DETTE_RATTACHEE': float(row.get('DETTE_RATTACHEE') or 0),
                        'detteRattachee': float(row.get('DETTE_RATTACHEE') or 0)
                    }
                elif encours_type == "epargne-projet":
                    agency = {
                        'BRANCH_CODE': branch_code,
                        'BRANCH_NAME': agency_name,
                        'name': agency_name,
                        'M_ENCOURS_COMPTE_EPARGNE_PROJET': float(row.get('M_ENCOURS_COMPTE_EPARGNE_PROJET') or 0),
                        'M1_ENCOURS_COMPTE_EPARGNE_PROJET': float(row.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET') or 0),
                        'ENCOURS_TOTAL_M': float(row.get('ENCOURS_TOTAL_M') or 0),
                        'ENCOURS_TOTAL_M_1': float(row.get('ENCOURS_TOTAL_M_1') or 0),
                        'DETTE_RATTACHEE': float(row.get('DETTE_RATTACHEE') or 0),
                        'detteRattachee': float(row.get('DETTE_RATTACHEE') or 0)
                    }
                else:
                    # Compte courant par défaut
                    agency = {
                        'BRANCH_CODE': branch_code,
                        'BRANCH_NAME': agency_name,
                        'name': agency_name,
                        'M1_ENCOURS_COMPTE_COURANT': float(row.get('M1_ENCOURS_COMPTE_COURANT') or 0),
                        'M_ENCOURS_COMPTE_COURANT': float(row.get('M_ENCOURS_COMPTE_COURANT') or 0),
                        'ENCOURS_TOTAL_M': float(row.get('ENCOURS_TOTAL_M') or 0),
                        'ENCOURS_TOTAL_M_1': float(row.get('ENCOURS_TOTAL_M_1') or 0)
                    }
                
                # Territoire : code agence (mapping Oracle), puis nom d'agence — nécessaire pour DASH
                # (BRANCH_CODE parfois absent ou non présent dans le cache ; BRANCH_NAME toujours exploitable).
                territory = get_territory_from_branch_code(branch_code)
                if territory is None:
                    territory = get_territory_from_agency(agency_name)

                # Vérifier si c'est le grand compte
                if agency_name and 'GRAND COMPTE' in agency_name.upper():
                    grand_compte = agency
                    continue
                
                if territory is None or territory == 'POINT SERVICES':
                    territory_key = 'territoire_dakar_ville'
                else:
                    territory_key = get_territory_key(territory)
                if territory_key in agencies_by_territory:
                    agencies_by_territory[territory_key].append(agency)
            
            # Calculer les totaux pour chaque territoire
            def calculate_territory_totals(agencies_list):
                """Calcule les totaux pour un territoire"""
                totals = {
                    'm1Enours': 0,
                    'mEnours': 0,
                    'encoursTotalM': 0,
                    'encoursTotalM1': 0
                }
                for agency in agencies_list:
                    if encours_type == "epargne-simple":
                        totals['m1Enours'] += float(agency.get('M1_ENCOURS_COMPTE_EPARGNE', 0) or 0)
                        totals['mEnours'] += float(agency.get('M_ENCOURS_COMPTE_EPARGNE', 0) or 0)
                    elif encours_type == "epargne-pep-simple":
                        # Pour PEP et SIMPLE, on additionne M1 EPARGNE + M1 EPARGNE PROJET
                        totals['m1Enours'] += float(agency.get('M1_ENCOURS_COMPTE_EPARGNE', 0) or 0) + float(agency.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET', 0) or 0)
                        # Pour PEP et SIMPLE, on additionne M EPARGNE + M EPARGNE PROJET
                        totals['mEnours'] += float(agency.get('M_ENCOURS_COMPTE_EPARGNE', 0) or 0) + float(agency.get('M_ENCOURS_COMPTE_EPARGNE_PROJET', 0) or 0)
                    elif encours_type == "epargne-projet":
                        # Pour EPARGNE PROJET, on utilise seulement les valeurs PROJET
                        totals['m1Enours'] += float(agency.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET', 0) or 0)
                        totals['mEnours'] += float(agency.get('M_ENCOURS_COMPTE_EPARGNE_PROJET', 0) or 0)
                    else:
                        totals['m1Enours'] += float(agency.get('M1_ENCOURS_COMPTE_COURANT', 0) or 0)
                        totals['mEnours'] += float(agency.get('M_ENCOURS_COMPTE_COURANT', 0) or 0)
                    totals['encoursTotalM'] += float(agency.get('ENCOURS_TOTAL_M', 0) or 0)
                    totals['encoursTotalM1'] += float(agency.get('ENCOURS_TOTAL_M_1', 0) or 0)
                return totals
            
            # Construire la structure hiérarchique
            response_data = {
                "hierarchicalData": {
                    "TERRITOIRE": {},
                    "POINT SERVICES": {}
                }
            }
            
            # Ajouter les territoires
            if any(agencies_by_territory.values()):
                response_data["hierarchicalData"]["TERRITOIRE"] = {
                    "territoire_dakar_ville": {
                        "name": "DAKAR CENTRE VILLE",
                        "agencies": agencies_by_territory['territoire_dakar_ville'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_dakar_ville'])
                    },
                    "territoire_dakar_banlieue": {
                        "name": "DAKAR BANLIEUE",
                        "agencies": agencies_by_territory['territoire_dakar_banlieue'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_dakar_banlieue'])
                    },
                    "province_centre_sud": {
                        "name": "PROVINCE CENTRE SUD",
                        "agencies": agencies_by_territory['territoire_province_centre_sud'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_province_centre_sud'])
                    },
                    "province_nord": {
                        "name": "PROVINCE NORD",
                        "agencies": agencies_by_territory['territoire_province_nord'],
                        "totals": calculate_territory_totals(agencies_by_territory['territoire_province_nord'])
                    }
                }
                
                # Ajouter le grand compte dans TERRITOIRE si présent
                if grand_compte:
                    if encours_type == "epargne-simple":
                        grand_compte_totals = {
                            'm1Enours': grand_compte.get('M1_ENCOURS_COMPTE_EPARGNE', 0),
                            'mEnours': grand_compte.get('M_ENCOURS_COMPTE_EPARGNE', 0),
                            'encoursTotalM': grand_compte.get('ENCOURS_TOTAL_M', 0)
                        }
                    elif encours_type == "epargne-pep-simple":
                        grand_compte_totals = {
                            'm1Enours': grand_compte.get('M1_ENCOURS_COMPTE_EPARGNE', 0) + grand_compte.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET', 0),
                            'mEnours': grand_compte.get('M_ENCOURS_COMPTE_EPARGNE', 0) + grand_compte.get('M_ENCOURS_COMPTE_EPARGNE_PROJET', 0),
                            'encoursTotalM': grand_compte.get('ENCOURS_TOTAL_M', 0)
                        }
                    elif encours_type == "epargne-projet":
                        grand_compte_totals = {
                            'm1Enours': grand_compte.get('M1_ENCOURS_COMPTE_EPARGNE_PROJET', 0),
                            'mEnours': grand_compte.get('M_ENCOURS_COMPTE_EPARGNE_PROJET', 0),
                            'encoursTotalM': grand_compte.get('ENCOURS_TOTAL_M', 0)
                        }
                    else:
                        grand_compte_totals = {
                            'm1Enours': grand_compte.get('M1_ENCOURS_COMPTE_COURANT', 0),
                            'mEnours': grand_compte.get('M_ENCOURS_COMPTE_COURANT', 0),
                            'encoursTotalM': grand_compte.get('ENCOURS_TOTAL_M', 0)
                        }
                    response_data["hierarchicalData"]["TERRITOIRE"]["grand_compte"] = {
                        "name": "GRAND COMPTE",
                        "agencies": [grand_compte],
                        "totals": grand_compte_totals
                    }
            
            # Mettre en cache le résultat (TTL de 5 minutes)
            set_cache(cache_key, response_data, ttl=300)
            
            logger.info(f"✅ Données Encours récupérées: {len(data)} agences")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données Encours: {str(e)}", exc_info=True)
            raise
