"""
Répartition encours global — requête Flexcube (CHARGE + EXIGIBLE).

Jointure détail compte / prêt : sttm_cust_account × EXIGIBLE × CHARGE.
L'agrégation client est faite en Python pour éviter le double comptage
des charges (FTC, ACS…) quand plusieurs prêts partagent le même compte.
"""
from typing import Any, Dict, List

ENCOURS_REPARTITION_DETAIL = """
WITH ASC_DUE_OUV AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND COMPONENT = 'CHARGE'
      AND PRODUCT = 'ASCP'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR
),
ACS_DUE_ANNUELLE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND COMPONENT = 'CHARGE'
      AND PRODUCT = 'ASSA'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR
),
FRAIS_OUV_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND COMPONENT = 'CHARGE'
      AND PRODUCT = 'FOUV'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR
),
COFICARTE_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND COMPONENT = 'CHARGE'
      AND PRODUCT = 'COFC'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR
),
FTC_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND COMPONENT = 'CHARGE'
      AND PRODUCT = 'FTEC'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR
),
CHARGE AS (
    SELECT
        c.CUST_AC_NO AS NUMERO_COMPTE,
        c.CUST_NO AS MATRICULE_CLIENT,
        c.AC_DESC AS NOM_CLIENT,
        NVL(acs.CHARGE_DUE, 0) AS CHARGE_DUE_ACS_OUV,
        NVL(acsa.CHARGE_DUE, 0) AS CHARGE_DUE_ACS_AN,
        NVL(fro.CHARGE_DUE, 0) AS CHARGE_DUE_FR_OUV,
        NVL(crt.CHARGE_DUE, 0) AS CHARGE_DUE_CARTE,
        NVL(ftc.CHARGE_DUE, 0) AS CHARGE_DUE_FTC,
        (
            NVL(acs.CHARGE_DUE, 0) + NVL(acsa.CHARGE_DUE, 0)
            + NVL(fro.CHARGE_DUE, 0) + NVL(crt.CHARGE_DUE, 0) + NVL(ftc.CHARGE_DUE, 0)
        ) AS TOTAL_CHARGE
    FROM CFSFCUBS145.STTM_CUST_ACCOUNT c
    LEFT JOIN ASC_DUE_OUV acs ON acs.ACCOUNT_NO = c.CUST_AC_NO
    LEFT JOIN ACS_DUE_ANNUELLE acsa ON acsa.ACCOUNT_NO = c.CUST_AC_NO
    LEFT JOIN FRAIS_OUV_DUE fro ON fro.ACCOUNT_NO = c.CUST_AC_NO
    LEFT JOIN COFICARTE_DUE crt ON crt.ACCOUNT_NO = c.CUST_AC_NO
    LEFT JOIN FTC_DUE ftc ON ftc.ACCOUNT_NO = c.CUST_AC_NO
),
PENALITE_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        CONTRACT_REF_NO,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND b.COMPONENT IN ('ODIN_PNTY', 'ODIN_PNTYT', 'ODPR_PNTY', 'ODPR_PNTYT')
      AND ACCOUNT_NO LIKE '251%'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR, CONTRACT_REF_NO
),
INTERET_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        CONTRACT_REF_NO,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND b.COMPONENT = 'MAIN_INT'
      AND ACCOUNT_NO LIKE '251%'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR, CONTRACT_REF_NO
),
PRINCIPAL_DUE AS (
    SELECT
        ACCOUNT_NO,
        ACCOUNT_BR,
        CONTRACT_REF_NO,
        (SUM(AMOUNT_DUE) - SUM(AMOUNT_PAID)) AS CHARGE_DUE
    FROM CFSFCUBS145.CSTB_AUTO_SETTLE_BLOCK b
    WHERE STATUS <> 'P'
      AND b.COMPONENT = 'PRINCIPAL'
      AND ACCOUNT_NO LIKE '251%'
    GROUP BY ACCOUNT_NO, ACCOUNT_BR, CONTRACT_REF_NO
),
EXIGIBLE_1 AS (
    SELECT
        ped.ACCOUNT_NO AS NO_COMPTE,
        NVL(ped.CONTRACT_REF_NO, 0) AS NO_PRET,
        NVL(pr.CHARGE_DUE, 0) AS CHARGE_DUE_PRINC,
        NVL(ped.CHARGE_DUE, 0) AS CHARGE_DUE_PEN,
        NVL(id.CHARGE_DUE, 0) AS CHARGE_DUE_INT,
        (
            NVL(pr.CHARGE_DUE, 0) + NVL(ped.CHARGE_DUE, 0) + NVL(id.CHARGE_DUE, 0)
        ) AS EXIGIBLE
    FROM PRINCIPAL_DUE pr
    FULL OUTER JOIN PENALITE_DUE ped
        ON ped.ACCOUNT_NO = pr.ACCOUNT_NO
    FULL OUTER JOIN INTERET_DUE id
        ON id.ACCOUNT_NO = pr.ACCOUNT_NO
),
EXIGIBLE AS (
    SELECT
        c.CUST_NO AS MATRICULE_CLIENT,
        ex.NO_COMPTE,
        c.AC_DESC AS NOM_CLIENT,
        ex.NO_PRET,
        ex.CHARGE_DUE_PRINC,
        ex.CHARGE_DUE_PEN,
        ex.CHARGE_DUE_INT,
        ex.EXIGIBLE
    FROM EXIGIBLE_1 ex
    LEFT JOIN CFSFCUBS145.STTM_CUST_ACCOUNT c
        ON c.CUST_AC_NO = ex.NO_COMPTE
)
SELECT
    c.CUST_NO AS MATRICULE_CLIENT,
    c.CUST_AC_NO AS NUMERO_COMPTE,
    c.AC_DESC AS NOM_CLIENT,
    ex.NO_PRET,
    NVL(ex.CHARGE_DUE_PRINC, 0) AS CHARGE_DUE_PRINC,
    NVL(ex.CHARGE_DUE_PEN, 0) AS CHARGE_DUE_PEN,
    NVL(ex.CHARGE_DUE_INT, 0) AS CHARGE_DUE_INT,
    NVL(ex.EXIGIBLE, 0) AS EXIGIBLE,
    NVL(ch.CHARGE_DUE_ACS_OUV, 0) AS CHARGE_DUE_ACS_OUV,
    NVL(ch.CHARGE_DUE_ACS_AN, 0) AS CHARGE_DUE_ACS_AN,
    NVL(ch.CHARGE_DUE_FR_OUV, 0) AS CHARGE_DUE_FR_OUV,
    NVL(ch.CHARGE_DUE_CARTE, 0) AS CHARGE_DUE_CARTE,
    NVL(ch.CHARGE_DUE_FTC, 0) AS CHARGE_DUE_FTC,
    NVL(ch.TOTAL_CHARGE, 0) AS TOTAL_CHARGE,
    (NVL(ex.EXIGIBLE, 0) + NVL(ch.TOTAL_CHARGE, 0)) AS TOTAL_DUE_AMOUNT
FROM CFSFCUBS145.STTM_CUST_ACCOUNT c
LEFT JOIN EXIGIBLE ex
    ON ex.MATRICULE_CLIENT = c.CUST_NO
   AND ex.NO_COMPTE = c.CUST_AC_NO
LEFT JOIN CHARGE ch
    ON ch.MATRICULE_CLIENT = c.CUST_NO
   AND ch.NUMERO_COMPTE = c.CUST_AC_NO
WHERE c.CUST_NO = :customer_no
  AND (
      NVL(ex.EXIGIBLE, 0) > 0
      OR NVL(ch.TOTAL_CHARGE, 0) > 0
  )
"""


def _to_float(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def aggregate_encours_repartition_rows(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Agrège les lignes détail en totaux client (charges dédupliquées par compte)."""
    if not rows:
        return {}

    capital = interest = penalty = total_exigible = 0.0
    charges_by_account: dict[str, dict] = {}

    for row in rows:
        capital += _to_float(row.get("CHARGE_DUE_PRINC"))
        penalty += _to_float(row.get("CHARGE_DUE_PEN"))
        interest += _to_float(row.get("CHARGE_DUE_INT"))
        total_exigible += _to_float(row.get("EXIGIBLE"))

        account = str(row.get("NUMERO_COMPTE") or "").strip()
        if account and account not in charges_by_account:
            charges_by_account[account] = row

    ftc = acs_ouv = acs_an = fr_ouv = carte = total_charge = 0.0
    for row in charges_by_account.values():
        acs_ouv += _to_float(row.get("CHARGE_DUE_ACS_OUV"))
        acs_an += _to_float(row.get("CHARGE_DUE_ACS_AN"))
        fr_ouv += _to_float(row.get("CHARGE_DUE_FR_OUV"))
        carte += _to_float(row.get("CHARGE_DUE_CARTE"))
        ftc += _to_float(row.get("CHARGE_DUE_FTC"))
        total_charge += _to_float(row.get("TOTAL_CHARGE"))

    return {
        "capital_due": round(capital, 2),
        "interest_due": round(interest, 2),
        "penalty_due": round(penalty, 2),
        "ftc_due": round(ftc, 2),
        "acs_due": round(acs_ouv + acs_an, 2),
        "acs_ouv_due": round(acs_ouv, 2),
        "acs_an_due": round(acs_an, 2),
        "opening_fee_due": round(fr_ouv, 2),
        "coficarte_fee_due": round(carte, 2),
        "total_exigible": round(total_exigible, 2),
        "total_charge": round(total_charge, 2),
        "total_due_amount": round(total_exigible + total_charge, 2),
    }
