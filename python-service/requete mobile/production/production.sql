WITH DEBLOCAGE AS (
  SELECT
    account_number,
    COALESCE(DTYPE, 'VIDE') AS DTYPE,
    MAX(SCHEDULE_LINKAGE)   AS SCHEDULE_LINKAGE
  FROM cfsfcubs145.CLTB_DISBR_SCHEDULES
  WHERE (DTYPE <> 'X') OR DTYPE IS NULL
  GROUP BY account_number, COALESCE(DTYPE, 'VIDE')
),
ECRITURE_DEBLOCAGE as (

SELECT 
                            e.RELATED_ACCOUNT,
 
                                e.AC_NO,
 
                                e.AMOUNT_TAG,
 
                                e.EVENT,
 
                                e.TRN_CODE,
                                e.TRN_DT
 
        FROM CFSFCUBS145.acvw_all_ac_entries e  
 
        WHERE
 
            e.TRN_CODE = '040'  
 
         
 
            and e.MODULE = 'CL'  
            and e.EVENT='DSBR'
 
            AND e.ac_no LIKE '251%'
 
          
)

,ENCOURS_COFINA AS (
       SELECT
    ACCOUNT_NUMBER,
    SUM(AMOUNT_DUE) AS MONTANT_DU,
    SUM(AMOUNT_DUE - AMOUNT_SETTLED) AS ENCOURS_TOTAL,
    SUM(
        CASE
            WHEN SCHEDULE_DUE_DATE >= TRUNC(SYSDATE)
            THEN AMOUNT_DUE
            ELSE 0
        END
    ) AS ENCOURS_SAIN,
    SUM(
        CASE
            WHEN SCHEDULE_DUE_DATE < TRUNC(SYSDATE)
            THEN AMOUNT_DUE - AMOUNT_SETTLED
            ELSE 0
        END
    ) AS ENCOURS_IMPAYE,
    ROUND(
        CASE
            WHEN SUM(AMOUNT_DUE) = 0 THEN 0
            ELSE (SUM(AMOUNT_SETTLED) / SUM(AMOUNT_DUE)) * 100
        END,
        2
    ) AS POURCENTAGE_REMBOURSEMENT
FROM CFSFCUBS145.CLTB_ACCOUNT_SCHEDULES
WHERE COMPONENT_NAME = 'PRINCIPAL'
GROUP BY ACCOUNT_NUMBER
        
  
)
    

SELECT
  c.BRANCH_CODE                                  AS "CODE AGENCE",
  b.branch_name                                  AS "NOM AGENCE",
  c.ACCOUNT_NUMBER                               AS "NO PRET",
  c.CUSTOMER_ID                                  AS "MATRICULE CLIENT",
  c.PRIMARY_APPLICANT_NAME                       AS "NOM CLIENT",
   c.DR_PROD_AC  AS "COMPTE",
    -----kyc.ADRESSE_ACTIVITE                         AS "ADDRESSE D'ACTIVITE",

  

  (SELECT g.GL_DESC_E
     FROM CFSFCUBS145.cltm_product_rth pr
     JOIN CFSFCUBS145.GLVW_GLMASTER_E g
       ON pr.ACCOUNT_HEAD = g.GL_CODE_E
    WHERE pr.PRODUCT_CODE = c.PRODUCT_CODE
      AND pr.ACCOUNTING_ROLE = 'LOAN_ACCOUNT'
      AND ROWNUM = 1)                             AS "TYPE PRET",
  c.BOOK_DATE                                    AS "DATE MISE EN PLACE",
  d.SCHEDULE_LINKAGE                              AS "DATE_VAL_MISE_EN_PLACE",
  ec.TRN_DT                                        AS "DATE_DEBLOCAGE",
  
  c.MATURITY_DATE                                AS DATE_MATURITE,
  
  
  
  (SELECT MIN(sc.schedule_due_date)
     FROM cfsfcubs145.CLTB_ACCOUNT_SCHEDULES sc
    WHERE sc.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
      AND sc.COMPONENT_NAME = 'MAIN_INT')         AS "DATE_PREMIERE_ECHEANCE",
  (SELECT MAX(sc.schedule_due_date)
     FROM cfsfcubs145.CLTB_ACCOUNT_SCHEDULES sc
    WHERE sc.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
      AND sc.COMPONENT_NAME = 'MAIN_INT')         AS "DATE_DERNIERE_ECHEANCE",
  
  c.amount_financed                              AS "MONTANT CAPITAL ACCORDE",
  DECODE(c.ACCOUNT_STATUS,
         'A', 'FINANCER',
         'L', 'SOLDER',
         'V', 'Annuler',
         'Y', 'Futur Deblocage',
         'H', 'EN ATTENTE',
         c.ACCOUNT_STATUS)                        AS "STATUT PRET",
  (SELECT DECODE(MAX(sch.unit),
                 'M', 'Mensuel',
                 'B', 'infin?',
                 'H', 'semi annuel',
                 'Y', 'Annuel',
                 'Q', 'Trimestrielle',
                 'D', 'Journalier',
                 MAX(sch.unit))
     FROM cfsfcubs145.cltbs_account_comp_sch sch
    WHERE sch.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER)  AS "PERIODICITE",
   
    C.FIELD_NUMBER_2  "CPT_DEPOT_GARANTIE" ,
    
    (SELECT NVL(SUM(DECODE(t.drcr_ind, 'C', t.lcy_amount, 0)), 0)
     FROM cfsfcubs145.ACVW_ALL_AC_ENTRIES t
    WHERE t.RELATED_ACCOUNT = c.ACCOUNT_NUMBER
      AND t.AMOUNT_TAG IN ('GUAR_DEPO_LIQD'))        AS "MONTANT_DEPOT_GARANTIE_INITIAL",
      
         ( 
        select 
        sum(decode (g.drcr_ind, 'C', g.lcy_amount, 0)) - sum(decode (g.drcr_ind, 'D', g.lcy_amount, 0))
        from CFSFCUBS145.acvw_all_ac_entries g
        where  g.AC_NO like '254%' and  g.ac_no =  C.FIELD_NUMBER_2
        
        group by g.ac_no 
        ) AS "SOLDE_DEPOT_GARANTIE",
    
    
    
     (SELECT NVL(SUM(DECODE(t.drcr_ind, 'C', t.lcy_amount, 0)), 0)
     FROM cfsfcubs145.ACVW_ALL_AC_ENTRIES t
    WHERE t.RELATED_ACCOUNT = c.ACCOUNT_NUMBER
      AND t.AMOUNT_TAG IN ('PROC_FEES_LIQD'))        AS "FRAIS_DOSSIER",
  
  (SELECT NVL(SUM(DECODE(t.drcr_ind, 'C', t.lcy_amount, 0)), 0)
     FROM cfsfcubs145.ACVW_ALL_AC_ENTRIES t
    WHERE t.RELATED_ACCOUNT = c.ACCOUNT_NUMBER
      AND t.AMOUNT_TAG IN ('INSUR_LIQD'))        AS "FRAIS_ASSURANCE",
  (SELECT MAX(v.ude_value)
     FROM cfsfcubs145.cltbs_account_ude_values v
    WHERE v.ACCOUNT_NUMBER = c.ACCOUNT_NUMBER
      AND v.ude_id = 'INTEREST_RATE'
      AND v.ude_value IS NOT NULL)                AS "TAUX DE CREDIT",
  c.FIELD_CHAR_5                                  AS "TYPE_PRET",
 
  
  

  c.FIELD_CHAR_2                                  AS "CODE_GESTION_PRET",
  (SELECT MAX(u.LOV_DESC)
     FROM cfsfcubs145.UDTM_LOV u
    WHERE u.FIELD_NAME = 'GESTION_PRET'
      AND u.LOV = c.FIELD_CHAR_2)                 AS "CHARGE_D'AFFAIRE"
 
 ,ES.ENCOURS_TOTAL
 ,ES.ENCOURS_SAIN
 ,ES.ENCOURS_IMPAYE
 ,ES.POURCENTAGE_REMBOURSEMENT
 
 ----- c.FIELD_NUMBER_3                                AS "MONTANT_DEPOT_GARANTIE_INITIAL"

  
FROM CFSFCUBS145.CLTB_ACCOUNT_MASTER c
LEFT JOIN CFSFCUBS145.STTM_BRANCH b
  ON b.branch_code = c.branch_code
left join ECRITURE_DEBLOCAGE ec
    on ec.RELATED_ACCOUNT= c.ACCOUNT_NUMBER
LEFT JOIN DEBLOCAGE d
  ON d.account_number = c.ACCOUNT_NUMBER
  
Left join ENCOURS_COFINA ES 
  on ES.ACCOUNT_NUMBER=c.ACCOUNT_NUMBER
  

  
---------------------------------------------------------------------------------------------------------------------
   where  

  ec.TRN_DT between TO_DATE(:m_start, 'YYYY-MM-DD') and TO_DATE(:m_end, 'YYYY-MM-DD')
